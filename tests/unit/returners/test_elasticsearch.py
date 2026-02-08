"""
Test the elasticsearch returner
"""

import datetime
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import salt.utils.jid
import salt.utils.json

elastic = pytest.importorskip("elasticsearch")

ES_MAJOR_VERSION = elastic.__version__[0]
if ES_MAJOR_VERSION >= 9:
    import saltext.elasticsearch.returners.elasticsearch9_mod as elasticsearch_return
elif ES_MAJOR_VERSION >= 8:
    import saltext.elasticsearch.returners.elasticsearch8_mod as elasticsearch_return
else:
    import saltext.elasticsearch.returners.elasticsearch6_mod as elasticsearch_return


@pytest.fixture
def configure_loader_modules():
    return {elasticsearch_return: {}}


@pytest.fixture
def default_options():
    """Default options returned by _get_options()."""
    return {
        "debug_returner_payload": False,
        "doc_type": "default",
        "functions_blacklist": [],
        "index_date": False,
        "master_event_index": "salt-master-event-cache",
        "master_event_doc_type": "default",
        "master_job_cache_index": "salt-master-job-cache",
        "master_job_cache_doc_type": "default",
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "states_order_output": False,
        "states_count": False,
        "states_single_index": False,
    }


@pytest.fixture
def mock_salt():
    """Dict of mocked __salt__ functions."""
    return {
        "elasticsearch.index_exists": MagicMock(return_value=True),
        "elasticsearch.index_create": MagicMock(return_value=True),
        "elasticsearch.alias_create": MagicMock(return_value=True),
        "elasticsearch.document_create": MagicMock(return_value=True),
        "elasticsearch.document_get": MagicMock(return_value=None),
    }


@pytest.fixture
def sample_ret():
    """Basic successful return payload."""
    return {
        "fun": "test.ping",
        "jid": "20230101120000000000",
        "id": "minion1",
        "retcode": 0,
        "return": True,
    }


# ---------------------------------------------------------------------------
# __virtual__()
# ---------------------------------------------------------------------------


def test__virtual_with_elasticsearch():
    """
    Test __virtual__ function when elasticsearch is available and version >= 9.
    """
    with patch.dict(elasticsearch_return.__salt__, {"elasticsearch.index_exists": MagicMock()}):
        result = elasticsearch_return.__virtual__()
        expected = "elasticsearch"
        assert expected == result


def test__virtual_without_elasticsearch():
    """
    Test __virtual__ returns False when HAS_ELASTICSEARCH is False.
    """
    with patch.object(elasticsearch_return, "HAS_ELASTICSEARCH", False):
        result = elasticsearch_return.__virtual__()
        assert result[0] is False
        assert "elasticsearch" in result[1].lower()


@pytest.mark.skipif(ES_MAJOR_VERSION < 9, reason="ES9-specific __virtual__ behavior")
def test__virtual_with_old_version():
    """
    Test __virtual__ returns False when ES_MAJOR_VERSION < 9.
    """
    with (
        patch.object(elasticsearch_return, "HAS_ELASTICSEARCH", True),
        patch.object(elasticsearch_return, "ES_MAJOR_VERSION", 8),
    ):
        result = elasticsearch_return.__virtual__()
        assert result[0] is False
        assert "9" in result[1]


# ---------------------------------------------------------------------------
# _get_options()
# ---------------------------------------------------------------------------


def test__get_options_defaults(mock_salt, default_options):
    """
    Verify _get_options() calls get_returner_options with correct defaults/attrs.
    """
    with (
        patch.dict(elasticsearch_return.__salt__, mock_salt),
        patch.dict(elasticsearch_return.__opts__, {}),
        patch("salt.returners.get_returner_options", return_value=default_options) as mock_gro,
    ):
        result = elasticsearch_return._get_options()
        mock_gro.assert_called_once()
        args, kwargs = mock_gro.call_args
        assert args[0] == "elasticsearch"
        assert kwargs["defaults"] == default_options
        assert result == default_options


# ---------------------------------------------------------------------------
# _ensure_index()
# ---------------------------------------------------------------------------


def test__ensure_index_already_exists(mock_salt, default_options):
    """
    When index_exists returns True, no create/alias calls should be made.
    """
    mock_salt["elasticsearch.index_exists"].return_value = True
    with patch.dict(elasticsearch_return.__salt__, mock_salt):
        elasticsearch_return._ensure_index("salt-test_ping")
        mock_salt["elasticsearch.index_exists"].assert_called_once_with("salt-test_ping")
        mock_salt["elasticsearch.index_create"].assert_not_called()
        mock_salt["elasticsearch.alias_create"].assert_not_called()


def test__ensure_index_creates_new(mock_salt, default_options):
    """
    When index_exists returns False, calls index_create with {index}-v1 and alias_create.
    """
    mock_salt["elasticsearch.index_exists"].return_value = False
    with (
        patch.dict(elasticsearch_return.__salt__, mock_salt),
        patch.dict(elasticsearch_return.__opts__, {}),
        patch("salt.returners.get_returner_options", return_value=default_options),
    ):
        elasticsearch_return._ensure_index("salt-test_ping")
        mock_salt["elasticsearch.index_create"].assert_called_once()
        create_args = mock_salt["elasticsearch.index_create"].call_args
        assert create_args[0][0] == "salt-test_ping-v1"
        mock_salt["elasticsearch.alias_create"].assert_called_once_with(
            "salt-test_ping-v1", "salt-test_ping"
        )


# ---------------------------------------------------------------------------
# _convert_keys()
# ---------------------------------------------------------------------------


def test__convert_keys_scalar():
    """Scalar values pass through unchanged."""
    assert elasticsearch_return._convert_keys(42) == 42
    assert elasticsearch_return._convert_keys("hello") == "hello"
    assert elasticsearch_return._convert_keys(None) is None
    assert elasticsearch_return._convert_keys(True) is True


def test__convert_keys_dict_no_dots():
    """Dict keys without dots are unchanged."""
    data = {"foo": "bar", "baz": 1}
    result = elasticsearch_return._convert_keys(data)
    assert result == {"foo": "bar", "baz": 1}


def test__convert_keys_dict_with_dots():
    """Dotted keys get _orig_key stored and dots replaced with underscores."""
    data = {"some.dotted.key": "value"}
    result = elasticsearch_return._convert_keys(data)
    assert "some_dotted_key" in result
    assert result["some_dotted_key"] == "value"
    assert result["_orig_key"] == "some.dotted.key"


def test__convert_keys_nested():
    """Recursive conversion of nested dicts and lists."""
    data = {
        "top": {
            "nested.key": "val",
        },
        "items": [{"list.key": "lval"}, "plain"],
    }
    result = elasticsearch_return._convert_keys(data)
    assert result["top"]["nested_key"] == "val"
    assert result["top"]["_orig_key"] == "nested.key"
    assert result["items"][0]["list_key"] == "lval"
    assert result["items"][1] == "plain"


# ---------------------------------------------------------------------------
# returner()
# ---------------------------------------------------------------------------


def test_returner_basic(mock_salt, default_options, sample_ret):
    """
    Basic successful return (test.ping), verifies document_create called with correct index.
    """
    with (
        patch.dict(elasticsearch_return.__salt__, mock_salt),
        patch.dict(elasticsearch_return.__opts__, {}),
        patch("salt.returners.get_returner_options", return_value=default_options),
    ):
        elasticsearch_return.returner(sample_ret)
        mock_salt["elasticsearch.document_create"].assert_called_once()
        kwargs = mock_salt["elasticsearch.document_create"].call_args[1]
        assert kwargs["index"] == "salt-test_ping"
        doc = salt.utils.json.loads(kwargs["document"])
        assert doc["fun"] == "test.ping"
        assert doc["jid"] == "20230101120000000000"
        assert doc["minion"] == "minion1"
        assert doc["success"] is True
        assert doc["retcode"] == 0


def test_returner_blacklisted_function(mock_salt, default_options, sample_ret):
    """
    Function in blacklist returns early, no ES calls.
    """
    opts = {**default_options, "functions_blacklist": ["test.ping"]}
    with (
        patch.dict(elasticsearch_return.__salt__, mock_salt),
        patch.dict(elasticsearch_return.__opts__, {}),
        patch("salt.returners.get_returner_options", return_value=opts),
    ):
        elasticsearch_return.returner(sample_ret)
        mock_salt["elasticsearch.document_create"].assert_not_called()


def test_returner_no_data_no_return(mock_salt, default_options):
    """
    Both data and return are None, returns early.
    """
    ret = {
        "fun": "test.ping",
        "jid": "20230101120000000000",
        "id": "minion1",
        "retcode": 0,
        "return": None,
    }
    with (
        patch.dict(elasticsearch_return.__salt__, mock_salt),
        patch.dict(elasticsearch_return.__opts__, {}),
        patch("salt.returners.get_returner_options", return_value=default_options),
    ):
        elasticsearch_return.returner(ret)
        mock_salt["elasticsearch.document_create"].assert_not_called()


def test_returner_with_data_field(mock_salt, default_options):
    """
    data is not None, should proceed even if return is None, and data should
    be normalized into ret['return'] so the payload contains it.
    """
    ret = {
        "fun": "test.ping",
        "jid": "20230101120000000000",
        "id": "minion1",
        "retcode": 0,
        "return": None,
        "data": {"some": "data"},
    }
    with (
        patch.dict(elasticsearch_return.__salt__, mock_salt),
        patch.dict(elasticsearch_return.__opts__, {}),
        patch("salt.returners.get_returner_options", return_value=default_options),
    ):
        elasticsearch_return.returner(ret)
        mock_salt["elasticsearch.document_create"].assert_called_once()
        kwargs = mock_salt["elasticsearch.document_create"].call_args[1]
        doc = salt.utils.json.loads(kwargs["document"])
        assert doc["data"] == {"some": "data"}


def test_returner_index_date(mock_salt, default_options, sample_ret):
    """
    index_date=True, index name includes date suffix.
    """
    opts = {**default_options, "index_date": True}
    today = datetime.date.today().strftime("%Y.%m.%d")
    with (
        patch.dict(elasticsearch_return.__salt__, mock_salt),
        patch.dict(elasticsearch_return.__opts__, {}),
        patch("salt.returners.get_returner_options", return_value=opts),
    ):
        elasticsearch_return.returner(sample_ret)
        kwargs = mock_salt["elasticsearch.document_create"].call_args[1]
        assert kwargs["index"] == f"salt-test_ping-{today}"


def test_returner_state_apply(mock_salt, default_options):
    """
    fun=state.apply, index is salt-state_apply.
    """
    ret = {
        "fun": "state.apply",
        "jid": "20230101120000000000",
        "id": "minion1",
        "retcode": 0,
        "return": {
            "file_|-managed_|-/tmp/test_|-managed": {
                "result": True,
                "__run_num__": 0,
                "changes": {},
                "comment": "File is in the correct state",
            }
        },
    }
    with (
        patch.dict(elasticsearch_return.__salt__, mock_salt),
        patch.dict(elasticsearch_return.__opts__, {}),
        patch("salt.returners.get_returner_options", return_value=default_options),
    ):
        elasticsearch_return.returner(ret)
        kwargs = mock_salt["elasticsearch.document_create"].call_args[1]
        assert kwargs["index"] == "salt-state_apply"


def test_returner_states_single_index(mock_salt, default_options):
    """
    states_single_index=True with state.sls uses salt-state_apply index.
    """
    opts = {**default_options, "states_single_index": True}
    ret = {
        "fun": "state.sls",
        "jid": "20230101120000000000",
        "id": "minion1",
        "retcode": 0,
        "return": {
            "file_|-managed_|-/tmp/test_|-managed": {
                "result": True,
                "__run_num__": 0,
                "changes": {},
                "comment": "",
            }
        },
    }
    with (
        patch.dict(elasticsearch_return.__salt__, mock_salt),
        patch.dict(elasticsearch_return.__opts__, {}),
        patch("salt.returners.get_returner_options", return_value=opts),
    ):
        elasticsearch_return.returner(ret)
        kwargs = mock_salt["elasticsearch.document_create"].call_args[1]
        assert kwargs["index"] == "salt-state_apply"


def test_returner_states_count(mock_salt, default_options):
    """
    states_count=True, verify counts dict in payload.
    """
    opts = {**default_options, "states_count": True}
    ret = {
        "fun": "state.apply",
        "jid": "20230101120000000000",
        "id": "minion1",
        "retcode": 0,
        "return": {
            "file_|-managed_|-/tmp/ok_|-managed": {
                "result": True,
                "__run_num__": 0,
                "changes": {},
                "comment": "",
            },
            "pkg_|-installed_|-vim_|-installed": {
                "result": False,
                "__run_num__": 1,
                "changes": {},
                "comment": "Failed",
            },
            "service_|-running_|-nginx_|-running": {
                "result": None,
                "__run_num__": 2,
                "changes": {},
                "comment": "Would start",
            },
        },
    }
    with (
        patch.dict(elasticsearch_return.__salt__, mock_salt),
        patch.dict(elasticsearch_return.__opts__, {}),
        patch("salt.returners.get_returner_options", return_value=opts),
    ):
        elasticsearch_return.returner(ret)
        kwargs = mock_salt["elasticsearch.document_create"].call_args[1]
        doc = salt.utils.json.loads(kwargs["document"])
        assert doc["counts"]["succeeded"] == 2
        assert doc["counts"]["failed"] == 1


def test_returner_states_order_output(mock_salt, default_options):
    """
    states_order_output=True, verify key prefixing, _func field, and -ordered index.
    """
    opts = {**default_options, "states_order_output": True}
    ret = {
        "fun": "state.apply",
        "jid": "20230101120000000000",
        "id": "minion1",
        "retcode": 0,
        "return": {
            "file_|-managed_|-/tmp/test_|-managed": {
                "result": True,
                "__run_num__": 0,
                "changes": {},
                "comment": "",
            },
            "pkg_|-installed_|-vim_|-installed": {
                "result": True,
                "__run_num__": 1,
                "changes": {},
                "comment": "",
            },
        },
    }
    with (
        patch.dict(elasticsearch_return.__salt__, mock_salt),
        patch.dict(elasticsearch_return.__opts__, {}),
        patch("salt.returners.get_returner_options", return_value=opts),
    ):
        elasticsearch_return.returner(ret)
        kwargs = mock_salt["elasticsearch.document_create"].call_args[1]
        assert kwargs["index"] == "salt-state_apply-ordered"
        doc = salt.utils.json.loads(kwargs["document"])
        # Keys should be prefixed with zero-padded run numbers
        data_keys = list(doc["data"].keys())
        assert any(k.startswith("0_|-") for k in data_keys)
        assert any(k.startswith("1_|-") for k in data_keys)
        # _func field should be set
        for v in doc["data"].values():
            assert "_func" in v


def test_returner_state_non_dict_return(mock_salt, default_options):
    """
    State function with non-dict return wraps in {"return": ...}.
    """
    ret = {
        "fun": "state.apply",
        "jid": "20230101120000000000",
        "id": "minion1",
        "retcode": 1,
        "return": "Error: something went wrong",
    }
    with (
        patch.dict(elasticsearch_return.__salt__, mock_salt),
        patch.dict(elasticsearch_return.__opts__, {}),
        patch("salt.returners.get_returner_options", return_value=default_options),
    ):
        elasticsearch_return.returner(ret)
        kwargs = mock_salt["elasticsearch.document_create"].call_args[1]
        doc = salt.utils.json.loads(kwargs["document"])
        assert doc["data"] == {"return": "Error: something went wrong"}


def test_returner_debug_payload(mock_salt, default_options, sample_ret):
    """
    debug_returner_payload=True, verify log.debug called.
    """
    opts = {**default_options, "debug_returner_payload": True}
    with (
        patch.dict(elasticsearch_return.__salt__, mock_salt),
        patch.dict(elasticsearch_return.__opts__, {}),
        patch("salt.returners.get_returner_options", return_value=opts),
        patch.object(elasticsearch_return.log, "debug") as mock_debug,
    ):
        elasticsearch_return.returner(sample_ret)
        mock_debug.assert_called_once()
        assert "payload" in mock_debug.call_args[0][0].lower()


def test_returner_payload_structure(mock_salt, default_options, sample_ret):
    """
    Verify full payload has @timestamp, success, retcode, minion, fun, jid, counts, data.
    """
    with (
        patch.dict(elasticsearch_return.__salt__, mock_salt),
        patch.dict(elasticsearch_return.__opts__, {}),
        patch("salt.returners.get_returner_options", return_value=default_options),
    ):
        elasticsearch_return.returner(sample_ret)
        kwargs = mock_salt["elasticsearch.document_create"].call_args[1]
        doc = salt.utils.json.loads(kwargs["document"])
        expected_keys = {
            "@timestamp",
            "success",
            "retcode",
            "minion",
            "fun",
            "jid",
            "counts",
            "data",
        }
        assert expected_keys == set(doc.keys())


# ---------------------------------------------------------------------------
# event_return()
# ---------------------------------------------------------------------------


def test_event_return(mock_salt, default_options):
    """
    Basic event return, verifies document_create called with event index.
    """
    events = [
        {"tag": "salt/job/123/ret/minion1", "data": {"return": True}},
    ]
    with (
        patch.dict(elasticsearch_return.__salt__, mock_salt),
        patch.dict(elasticsearch_return.__opts__, {}),
        patch("salt.returners.get_returner_options", return_value=default_options),
    ):
        elasticsearch_return.event_return(events)
        mock_salt["elasticsearch.document_create"].assert_called_once()
        kwargs = mock_salt["elasticsearch.document_create"].call_args[1]
        assert kwargs["index"] == "salt-master-event-cache"


def test_event_return_multiple_events(mock_salt, default_options):
    """
    Multiple events should each produce a document_create call.
    """
    events = [
        {"tag": "salt/job/1/ret/minion1", "data": {"return": True}},
        {"tag": "salt/job/2/ret/minion2", "data": {"return": False}},
        {"tag": "salt/job/3/ret/minion3", "data": {"return": "ok"}},
    ]
    with (
        patch.dict(elasticsearch_return.__salt__, mock_salt),
        patch.dict(elasticsearch_return.__opts__, {}),
        patch("salt.returners.get_returner_options", return_value=default_options),
    ):
        elasticsearch_return.event_return(events)
        assert mock_salt["elasticsearch.document_create"].call_count == 3


def test_event_return_empty(mock_salt, default_options):
    """
    Empty events list should not call document_create and should not crash.
    """
    with (
        patch.dict(elasticsearch_return.__salt__, mock_salt),
        patch.dict(elasticsearch_return.__opts__, {}),
        patch("salt.returners.get_returner_options", return_value=default_options),
    ):
        elasticsearch_return.event_return([])
        mock_salt["elasticsearch.document_create"].assert_not_called()


def test_event_return_with_index_date(mock_salt, default_options):
    """
    index_date=True appends date to event index.
    """
    opts = {**default_options, "index_date": True}
    events = [
        {"tag": "salt/job/123/ret/minion1", "data": {"return": True}},
    ]
    today = datetime.date.today().strftime("%Y.%m.%d")
    with (
        patch.dict(elasticsearch_return.__salt__, mock_salt),
        patch.dict(elasticsearch_return.__opts__, {}),
        patch("salt.returners.get_returner_options", return_value=opts),
    ):
        elasticsearch_return.event_return(events)
        kwargs = mock_salt["elasticsearch.document_create"].call_args[1]
        assert kwargs["index"] == f"salt-master-event-cache-{today}"


# ---------------------------------------------------------------------------
# prep_jid()
# ---------------------------------------------------------------------------


def test_prep_jid_with_passed_jid():
    """
    Returns the passed JID when one is provided.
    """
    with patch.dict(elasticsearch_return.__opts__, {}):
        result = elasticsearch_return.prep_jid(passed_jid="20230101120000000000")
        assert result == "20230101120000000000"


def test_prep_jid_generates_new():
    """
    When passed_jid=None, generates a new JID.
    """
    with (
        patch.dict(elasticsearch_return.__opts__, {}),
        patch("salt.utils.jid.gen_jid", return_value="20230101120000000001") as mock_gen,
    ):
        result = elasticsearch_return.prep_jid()
        mock_gen.assert_called_once()
        assert result == "20230101120000000001"


# ---------------------------------------------------------------------------
# save_load()
# ---------------------------------------------------------------------------


def test_save_load(mock_salt, default_options):
    """
    Verifies document_create called with correct index, id, and data.
    """
    jid = "20230101120000000000"
    load = {"fun": "test.ping", "arg": []}
    with (
        patch.dict(elasticsearch_return.__salt__, mock_salt),
        patch.dict(elasticsearch_return.__opts__, {}),
        patch("salt.returners.get_returner_options", return_value=default_options),
    ):
        elasticsearch_return.save_load(jid, load)
        mock_salt["elasticsearch.document_create"].assert_called_once()
        kwargs = mock_salt["elasticsearch.document_create"].call_args[1]
        assert kwargs["index"] == "salt-master-job-cache"
        assert kwargs["id_"] == jid
        doc = salt.utils.json.loads(kwargs["document"])
        assert doc["jid"] == jid
        assert doc["load"] == load


# ---------------------------------------------------------------------------
# get_load()
# ---------------------------------------------------------------------------


def test_get_load_with_data(mock_salt, default_options):
    """
    document_get returns data, verify JSON parsed correctly.
    """
    expected_data = {"jid": "20230101120000000000", "load": {"fun": "test.ping"}}
    mock_salt["elasticsearch.document_get"].return_value = salt.utils.json.dumps(expected_data)
    with (
        patch.dict(elasticsearch_return.__salt__, mock_salt),
        patch.dict(elasticsearch_return.__opts__, {}),
        patch("salt.returners.get_returner_options", return_value=default_options),
    ):
        result = elasticsearch_return.get_load("20230101120000000000")
        mock_salt["elasticsearch.document_get"].assert_called_once_with(
            index="salt-master-job-cache", id="20230101120000000000"
        )
        assert result == expected_data


def test_get_load_no_data(mock_salt, default_options):
    """
    document_get returns None, returns empty dict.
    """
    mock_salt["elasticsearch.document_get"].return_value = None
    with (
        patch.dict(elasticsearch_return.__salt__, mock_salt),
        patch.dict(elasticsearch_return.__opts__, {}),
        patch("salt.returners.get_returner_options", return_value=default_options),
    ):
        result = elasticsearch_return.get_load("20230101120000000000")
        assert result == {}
