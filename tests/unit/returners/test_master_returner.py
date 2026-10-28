"""
Test the elasticsearch master returner functions (master job cache).

These cover ``save_load``, ``get_load``, ``get_jid``, ``get_jids``,
``get_fun``, ``get_minions``, ``_make_cache_doc`` and ``_add_minion_to_doc``
parametrized across all three returner modules.
"""

from contextlib import ExitStack
from unittest.mock import patch

import pytest
import salt.utils.json
from salt.exceptions import CommandExecutionError

import saltext.elasticsearch.returners.elasticsearch6_mod as es6_return
import saltext.elasticsearch.returners.elasticsearch8_mod as es8_return
import saltext.elasticsearch.returners.elasticsearch9_mod as es9_return

RETURNER_MODULES = [
    pytest.param(es6_return, id="es6"),
    pytest.param(es8_return, id="es8"),
    pytest.param(es9_return, id="es9"),
]


def _patched(mod, mock_salt, options):
    """Patch __salt__/__opts__ and get_returner_options on a returner module."""
    stack = ExitStack()
    stack.enter_context(patch.dict(mod.__salt__, mock_salt))
    stack.enter_context(patch.object(mod, "__opts__", {}))
    stack.enter_context(patch("salt.returners.get_returner_options", return_value=options))
    return stack


# ---------------------------------------------------------------------------
# _make_cache_doc()
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("returner_mod", RETURNER_MODULES)
def test__make_cache_doc_full(returner_mod, load):
    """
    The cache doc carries the function, user, target, jid, JSON-encoded
    arguments and both timestamps.
    """
    doc = returner_mod._make_cache_doc(load, load["jid"])
    assert doc["Function"] == "test.ping"
    assert doc["User"] == "norbert"
    assert doc["Schedule"] is None
    assert doc["Target-type"] == "glob"
    assert doc["Target"] == "*"
    assert doc["jid"] == "20260924120000000000"
    assert salt.utils.json.loads(doc["Arguments"]) == ["timeout=5"]
    assert doc["StartTime"] == "2026-09-24T12:00:00Z"
    assert doc["@timestamp"] == "2026-09-24T12:00:00Z"


@pytest.mark.parametrize("returner_mod", RETURNER_MODULES)
def test__make_cache_doc_minimal(returner_mod):
    """
    Loads without user/schedule/tgt_type fall back to the documented defaults.
    """
    load = {"fun": "test.ping", "tgt": "minion1", "_stamp": "2026-09-24T12:00:00Z"}
    doc = returner_mod._make_cache_doc(load, "20260924120000000001")
    assert doc["User"] == "salt"
    assert doc["Schedule"] is None
    assert doc["Target-type"] is None
    assert doc["Target"] == "minion1"


@pytest.mark.parametrize("returner_mod", RETURNER_MODULES)
def test__make_cache_doc_prefers_fun_args(returner_mod):
    """
    fun_args wins over arg when both are present in the load.
    """
    load = {
        "fun": "test.ping",
        "tgt": "*",
        "arg": ["a"],
        "fun_args": ["b"],
        "_stamp": "2026-09-24T12:00:00Z",
    }
    doc = returner_mod._make_cache_doc(load, "20260924120000000002")
    assert salt.utils.json.loads(doc["Arguments"]) == ["b"]


@pytest.mark.parametrize("returner_mod", RETURNER_MODULES)
def test__make_cache_doc_fun_args_beats_fun_arg(returner_mod):
    """
    fun_args wins over the singular fun_arg when both are present.
    """
    load = {
        "fun": "test.ping",
        "tgt": "*",
        "fun_args": ["b"],
        "fun_arg": ["c"],
        "_stamp": "2026-09-24T12:00:00Z",
    }
    doc = returner_mod._make_cache_doc(load, "20260924120000000003")
    assert salt.utils.json.loads(doc["Arguments"]) == ["b"]


@pytest.mark.parametrize("returner_mod", RETURNER_MODULES)
def test__make_cache_doc_fun_arg_fallback(returner_mod):
    """
    fun_arg is used when neither arg nor fun_args are present.
    """
    load = {
        "fun": "test.ping",
        "tgt": "*",
        "fun_arg": ["c"],
        "_stamp": "2026-09-24T12:00:00Z",
    }
    doc = returner_mod._make_cache_doc(load, "20260924120000000004")
    assert salt.utils.json.loads(doc["Arguments"]) == ["c"]


# ---------------------------------------------------------------------------
# _add_minion_to_doc()
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("returner_mod", RETURNER_MODULES)
def test__add_minion_to_doc(returner_mod):
    """
    The upsert doc appends the minion id via a painless script.
    """
    doc = returner_mod._add_minion_to_doc("minion1")
    assert doc["script"]["lang"] == "painless"
    assert doc["script"]["params"]["minion"] == "minion1"
    assert doc["upsert"] == {"Minions": ["minion1"]}
    assert "ctx._source.Minions" in doc["script"]["source"]


# ---------------------------------------------------------------------------
# _ensure_index()
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("returner_mod", RETURNER_MODULES)
def test__ensure_index_already_exists(returner_mod, mock_salt):
    """
    When the -v2 index exists, no create/alias calls should be made.
    """
    mock_salt["elasticsearch.index_exists"].return_value = True
    with patch.dict(returner_mod.__salt__, mock_salt):
        returner_mod._ensure_index("salt-test_ping")
        mock_salt["elasticsearch.index_exists"].assert_called_once_with(index="salt-test_ping-v2")
        mock_salt["elasticsearch.index_create"].assert_not_called()
        mock_salt["elasticsearch.alias_create"].assert_not_called()


@pytest.mark.parametrize("returner_mod", RETURNER_MODULES)
def test__ensure_index_creates_new(returner_mod, mock_salt):
    """
    When the -v2 index is missing, index_create is called with -v2 and the alias
    is created pointing at it.
    """
    mock_salt["elasticsearch.index_exists"].return_value = False
    with patch.dict(returner_mod.__salt__, mock_salt):
        returner_mod._ensure_index("salt-test_ping")
        mock_salt["elasticsearch.index_create"].assert_called_once()
        create_kwargs = mock_salt["elasticsearch.index_create"].call_args[1]
        assert create_kwargs["index"] == "salt-test_ping-v2"
        assert "number_of_shards" in create_kwargs["settings"]
        assert "properties" in create_kwargs["mappings"]
        mock_salt["elasticsearch.alias_create"].assert_called_once_with(
            indices="salt-test_ping-v2", alias="salt-test_ping"
        )


@pytest.mark.parametrize("returner_mod", RETURNER_MODULES)
def test__ensure_index_replaces_stale_alias(returner_mod, mock_salt):
    """
    When the -v1 alias still points at the old index, it is deleted before
    creating the -v2 alias.
    """
    mock_salt["elasticsearch.index_exists"].return_value = False
    mock_salt["elasticsearch.alias_exists"].return_value = True
    with patch.dict(returner_mod.__salt__, mock_salt):
        returner_mod._ensure_index("salt-test_ping")
        mock_salt["elasticsearch.alias_delete"].assert_called_once_with(
            indices="salt-test_ping-v1", aliases="salt-test_ping"
        )


@pytest.mark.parametrize("returner_mod", RETURNER_MODULES)
def test__ensure_index_races_tolerated(returner_mod, mock_salt):
    """
    Already-exists races during index/alias creation are tolerated.
    """
    mock_salt["elasticsearch.index_exists"].return_value = False
    mock_salt["elasticsearch.index_create"].side_effect = CommandExecutionError(
        "resource_already_exists_exception while creating"
    )
    with patch.dict(returner_mod.__salt__, mock_salt):
        returner_mod._ensure_index("salt-test_ping")


@pytest.mark.parametrize("returner_mod", RETURNER_MODULES)
def test__ensure_index_other_errors_propagate(returner_mod, mock_salt):
    """
    Failures other than already-exists races are not swallowed.
    """
    mock_salt["elasticsearch.index_exists"].return_value = False
    mock_salt["elasticsearch.index_create"].side_effect = CommandExecutionError("boom")
    with patch.dict(returner_mod.__salt__, mock_salt):
        with pytest.raises(CommandExecutionError):
            returner_mod._ensure_index("salt-test_ping")


# ---------------------------------------------------------------------------
# save_load()
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("returner_mod", RETURNER_MODULES)
def test_save_load_publish_creates_cache_doc(returner_mod, mock_salt, default_options, load):
    """
    A publish load is written to the master job cache index with id_=jid.
    """
    with _patched(returner_mod, mock_salt, default_options):
        returner_mod.save_load(load["jid"], load)
        mock_salt["elasticsearch.document_create"].assert_called_once()
        kwargs = mock_salt["elasticsearch.document_create"].call_args[1]
        assert kwargs["index"] == "salt-master-job-cache"
        assert kwargs["id_"] == "20260924120000000000"
        doc = salt.utils.json.loads(kwargs["document"])
        assert doc["Function"] == "test.ping"
        assert doc["Target"] == "*"


@pytest.mark.parametrize("returner_mod", RETURNER_MODULES)
def test_save_load_return_updates_minions(returner_mod, mock_salt, default_options, load):
    """
    A _return load for an existing cache doc updates it with the minion id.
    """
    ret_load = dict(load)
    ret_load["cmd"] = "_return"
    mock_salt["elasticsearch.document_exists"].return_value = True

    with _patched(returner_mod, mock_salt, default_options):
        returner_mod.save_load(ret_load["jid"], ret_load)
        mock_salt["elasticsearch.document_update"].assert_called_once()
        kwargs = mock_salt["elasticsearch.document_update"].call_args[1]
        assert kwargs["index"] == "salt-master-job-cache"
        assert kwargs["id_"] == "20260924120000000000"
        assert kwargs["body"]["script"]["params"]["minion"] == "minion1"
        assert kwargs["retry_on_conflict"] == 5
        mock_salt["elasticsearch.document_create"].assert_not_called()


@pytest.mark.parametrize("returner_mod", RETURNER_MODULES)
def test_save_load_return_missing_creates_cache_doc(returner_mod, mock_salt, default_options, load):
    """
    A _return load for a missing cache doc falls back to creating it.
    """
    ret_load = dict(load)
    ret_load["cmd"] = "_return"
    mock_salt["elasticsearch.document_exists"].return_value = False

    with _patched(returner_mod, mock_salt, default_options):
        returner_mod.save_load(ret_load["jid"], ret_load)
        mock_salt["elasticsearch.document_create"].assert_called_once()
        mock_salt["elasticsearch.document_update"].assert_not_called()


@pytest.mark.parametrize("returner_mod", RETURNER_MODULES)
def test_save_load_other_cmd_is_noop(returner_mod, mock_salt, default_options, load):
    """
    Loads with an unknown cmd are logged and skipped without ES calls.
    """
    other = dict(load)
    other["cmd"] = "sync"
    with _patched(returner_mod, mock_salt, default_options):
        returner_mod.save_load(other["jid"], other)
        mock_salt["elasticsearch.document_create"].assert_not_called()
        mock_salt["elasticsearch.document_update"].assert_not_called()


@pytest.mark.parametrize("returner_mod", RETURNER_MODULES)
def test_save_load_no_cmd_new_jid(returner_mod, mock_salt, default_options, load):
    """
    Loads without cmd and a fresh jid are added to the cache.
    """
    plain = {
        "fun": "test.ping",
        "jid": load["jid"],
        "tgt": "*",
        "tgt_type": "glob",
        "_stamp": "2026-09-24T12:00:00Z",
    }
    with _patched(returner_mod, mock_salt, default_options):
        returner_mod.save_load(plain["jid"], plain)
        mock_salt["elasticsearch.document_create"].assert_called_once()


@pytest.mark.parametrize("returner_mod", RETURNER_MODULES)
def test_save_load_no_cmd_existing_jid(returner_mod, mock_salt, default_options, load):
    """
    Loads without cmd whose jid is already cached are skipped.
    """
    plain = {
        "fun": "test.ping",
        "jid": load["jid"],
        "tgt": "*",
        "tgt_type": "glob",
        "_stamp": "2026-09-24T12:00:00Z",
    }
    mock_salt["elasticsearch.document_exists"].return_value = True
    with _patched(returner_mod, mock_salt, default_options):
        returner_mod.save_load(plain["jid"], plain)
        mock_salt["elasticsearch.document_create"].assert_not_called()


@pytest.mark.parametrize("returner_mod", RETURNER_MODULES)
def test_save_load_no_jid_noop(returner_mod, mock_salt, default_options):
    """
    Loads without cmd and without a jid are skipped entirely.
    """
    with _patched(returner_mod, mock_salt, default_options):
        returner_mod.save_load(None, {"fun": "test.ping", "_stamp": "x"})
        mock_salt["elasticsearch.document_create"].assert_not_called()


# ---------------------------------------------------------------------------
# get_load()
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("returner_mod", RETURNER_MODULES)
def test_get_load_string_response(returner_mod, mock_salt, default_options, load):
    """
    A string response from document_get is parsed as JSON. The string path
    returns the cache doc as-is (no field-name mapping).
    """
    cache_doc = returner_mod._make_cache_doc(load, load["jid"])
    mock_salt["elasticsearch.document_get"].return_value = salt.utils.json.dumps(cache_doc)

    with _patched(returner_mod, mock_salt, default_options):
        ret = returner_mod.get_load(load["jid"])
        assert ret["Function"] == "test.ping"
        assert ret["jid"] == "20260924120000000000"


@pytest.mark.parametrize("returner_mod", RETURNER_MODULES)
def test_get_load_dict_response(returner_mod, mock_salt, default_options, load):
    """
    A dict response from document_get is unmapped from the cache field names.
    """
    cache_doc = returner_mod._make_cache_doc(load, load["jid"])
    mock_salt["elasticsearch.document_get"].return_value = {"_source": dict(cache_doc)}

    with _patched(returner_mod, mock_salt, default_options):
        ret = returner_mod.get_load(load["jid"])
        assert ret["fun"] == "test.ping"
        assert ret["tgt"] == "*"
        assert ret["tgt_type"] == "glob"
        assert ret["user"] == "norbert"
        assert ret["arg"] == ["timeout=5"]


@pytest.mark.parametrize("returner_mod", RETURNER_MODULES)
def test_get_load_no_arguments(returner_mod, mock_salt, default_options, load):
    """
    A cache doc without arguments does not crash get_load and yields an empty
    arg list.
    """
    cache_doc = returner_mod._make_cache_doc(load, load["jid"])
    del cache_doc["Arguments"]
    mock_salt["elasticsearch.document_get"].return_value = {"_source": dict(cache_doc)}

    with _patched(returner_mod, mock_salt, default_options):
        ret = returner_mod.get_load(load["jid"])
        assert ret["arg"] == []


@pytest.mark.parametrize("returner_mod", RETURNER_MODULES)
def test_get_load_missing(returner_mod, mock_salt, default_options, load):
    """
    A missing document returns an empty dict.
    """
    mock_salt["elasticsearch.document_get"].return_value = None
    with _patched(returner_mod, mock_salt, default_options):
        assert returner_mod.get_load("missing-jid") == {}


# ---------------------------------------------------------------------------
# get_jid()
# ---------------------------------------------------------------------------


def _cache_doc_stub(mod, load):
    return {
        "_source": mod._make_cache_doc(load, load["jid"]),
    }


@pytest.mark.parametrize("returner_mod", RETURNER_MODULES)
def test_get_jid_returns_minion_returns(returner_mod, mock_salt, default_options, load):
    """
    get_jid reads the cache doc for the function, searches the job index and
    returns {minion: return}, deserializing the data field.
    """
    mock_salt["elasticsearch.document_get"].return_value = _cache_doc_stub(returner_mod, load)
    mock_salt["elasticsearch.search"].return_value = {
        "hits": {
            "hits": [
                {"_source": {"minion": "minion1", "data": salt.utils.json.dumps({"return": True})}},
                {
                    "_source": {
                        "minion": "minion2",
                        "data": salt.utils.json.dumps({"return": "ret"}),
                    }
                },
            ]
        }
    }

    with _patched(returner_mod, mock_salt, default_options):
        ret = returner_mod.get_jid(load["jid"])
        assert ret == {"minion1": {"return": True}, "minion2": {"return": "ret"}}
        # the job index derives from the cached function name
        search_kwargs = mock_salt["elasticsearch.search"].call_args[1]
        assert search_kwargs["index"] == "salt-test_ping"
        # the jid is JSON-quoted in the query body
        assert '"20260924120000000000"' in search_kwargs["body"]


@pytest.mark.parametrize("returner_mod", RETURNER_MODULES)
def test_get_jid_missing_raises(returner_mod, mock_salt, default_options, load):
    """
    A jid missing from the master cache raises CommandExecutionError.
    """
    mock_salt["elasticsearch.document_get"].return_value = None
    with _patched(returner_mod, mock_salt, default_options):
        with pytest.raises(CommandExecutionError):
            returner_mod.get_jid("missing-jid")


@pytest.mark.parametrize("returner_mod", RETURNER_MODULES)
def test_get_jid_search_failure_returns_empty(returner_mod, mock_salt, default_options, load):
    """
    A search failure is tolerated and yields an empty dict.
    """
    mock_salt["elasticsearch.document_get"].return_value = _cache_doc_stub(returner_mod, load)
    mock_salt["elasticsearch.search"].side_effect = Exception("es down")
    with _patched(returner_mod, mock_salt, default_options):
        assert returner_mod.get_jid(load["jid"]) == {}


# ---------------------------------------------------------------------------
# get_jids()
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("returner_mod", RETURNER_MODULES)
def test_get_jids_lists_cached_jobs(returner_mod, mock_salt, default_options, load):
    """
    get_jids returns {jid: source} with Minions stripped and Arguments decoded.
    """
    cache_doc = returner_mod._make_cache_doc(load, load["jid"])
    cache_doc["Minions"] = ["minion1"]
    mock_salt["elasticsearch.document_get_all"].return_value = {"hits": [{"_source": cache_doc}]}

    with _patched(returner_mod, mock_salt, default_options):
        jobs = returner_mod.get_jids()
        assert list(jobs) == ["20260924120000000000"]
        assert jobs["20260924120000000000"]["Function"] == "test.ping"
        assert "Minions" not in jobs["20260924120000000000"]
        assert jobs["20260924120000000000"]["Arguments"] == ["timeout=5"]


@pytest.mark.parametrize("returner_mod", RETURNER_MODULES)
def test_get_jids_empty(returner_mod, mock_salt, default_options):
    """
    An empty cache index yields no jobs.
    """
    with _patched(returner_mod, mock_salt, default_options):
        assert not returner_mod.get_jids()


# ---------------------------------------------------------------------------
# get_fun() / get_minions()
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("returner_mod", RETURNER_MODULES)
def test_get_fun_returns_hits(returner_mod, mock_salt, default_options):
    """
    get_fun searches the salt-<fun> index and returns the raw hits.
    """
    hits = [{"_id": "a", "_source": {}}, {"_id": "b", "_source": {}}]
    mock_salt["elasticsearch.search"].return_value = {"hits": {"hits": hits}}

    with _patched(returner_mod, mock_salt, default_options):
        ret = returner_mod.get_fun("test.ping")
        assert ret == hits
        kwargs = mock_salt["elasticsearch.search"].call_args[1]
        assert kwargs["index"] == "salt-test_ping"


@pytest.mark.parametrize("returner_mod", RETURNER_MODULES)
def test_get_minions_returns_keys(returner_mod, mock_salt, default_options):
    """
    get_minions extracts the aggregation bucket keys.
    """
    mock_salt["elasticsearch.search"].return_value = {
        "aggregations": {
            "unique_field_values": {
                "buckets": [
                    {"key": "minion1", "doc_count": 3},
                    {"key": "minion2", "doc_count": 1},
                ]
            }
        }
    }

    with _patched(returner_mod, mock_salt, default_options):
        ret = returner_mod.get_minions()
        assert ret == ["minion1", "minion2"]
        kwargs = mock_salt["elasticsearch.search"].call_args[1]
        assert kwargs["index"] == "salt-master-job-cache"
        # the aggregation must run against the field the cache docs actually
        # populate (Minions), not the legacy load.id field
        assert "Minions.keyword" in kwargs["body"]


# ---------------------------------------------------------------------------
# returner() states_count guard
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("returner_mod", RETURNER_MODULES)
def test_returner_states_count_non_dict_states(returner_mod, mock_salt, default_options):
    """
    Non-dict state entries do not crash states_count counting.
    """
    ret = {
        "fun": "state.apply",
        "jid": "20260924120000000000",
        "id": "minion1",
        "retcode": 0,
        "return": {"m1": {"result": True}, "m2": "not-a-dict"},
    }
    options = {**default_options, "states_count": True}
    with _patched(returner_mod, mock_salt, options):
        returner_mod.returner(ret)
        mock_salt["elasticsearch.document_create"].assert_called_once()
        doc = salt.utils.json.loads(
            mock_salt["elasticsearch.document_create"].call_args[1]["document"]
        )
        assert doc["counts"] == {"succeeded": 1, "failed": 0}
