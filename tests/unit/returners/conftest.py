"""Shared fixtures for the elasticsearch returner tests."""

from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_salt():
    """Dict of mocked __salt__ functions used by the returner tests."""
    return {
        "elasticsearch.index_exists": MagicMock(return_value=True),
        "elasticsearch.index_create": MagicMock(return_value=True),
        "elasticsearch.alias_create": MagicMock(return_value=True),
        "elasticsearch.alias_exists": MagicMock(return_value=False),
        "elasticsearch.alias_delete": MagicMock(return_value=True),
        "elasticsearch.document_create": MagicMock(return_value=True),
        "elasticsearch.document_exists": MagicMock(return_value=False),
        "elasticsearch.document_get": MagicMock(return_value=None),
        "elasticsearch.document_get_all": MagicMock(return_value={"hits": []}),
        "elasticsearch.document_update": MagicMock(return_value=True),
        "elasticsearch.search": MagicMock(return_value={"hits": {"hits": []}}),
        "config.option": MagicMock(return_value={}),
    }


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
        "failover": False,
        "dev": False,
        "retry_on_conflicts": 5,
    }


@pytest.fixture
def load():
    """A typical publish load as sent by the master."""
    return {
        "cmd": "publish",
        "fun": "test.ping",
        "jid": "20260924120000000000",
        "id": "minion1",
        "user": "norbert",
        "tgt": "*",
        "tgt_type": "glob",
        "arg": ["timeout=5"],
        "_stamp": "2026-09-24T12:00:00Z",
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
