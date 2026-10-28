"""
Tests for the elasticsearch state module
"""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

import saltext.elasticsearch.states.elasticsearch_mod as elasticsearch_state

elastic = pytest.importorskip("elasticsearch")


@pytest.fixture
def configure_loader_modules():
    return {elasticsearch_state: {}}


class TestIndexAbsent:
    """
    Tests for index_absent
    """

    def test_index_absent_test(self):
        """
        Test mode: index exists, nothing removed, result is None.
        """
        mock_salt = {
            "elasticsearch.index_get": MagicMock(return_value={"test1": {"abcd"}}),
        }
        result = {
            "name": "test1",
            "changes": {"old": {"abcd"}},
            "result": None,
            "comment": "Index test1 will be removed",
        }
        with (
            patch.dict(elasticsearch_state.__salt__, mock_salt),
            patch.object(elasticsearch_state, "__opts__", {"test": True}),
        ):
            assert elasticsearch_state.index_absent("test1") == result

    def test_index_absent_run(self):
        """
        Non-test mode: index exists, removed successfully.
        """
        mock_salt = {
            "elasticsearch.index_get": MagicMock(return_value={"test1": {"abcd"}}),
            "elasticsearch.index_delete": MagicMock(return_value=True),
        }
        result = {
            "name": "test1",
            "changes": {"old": {"abcd"}},
            "result": True,
            "comment": "Successfully removed index test1",
        }
        with (
            patch.dict(elasticsearch_state.__salt__, mock_salt),
            patch.object(elasticsearch_state, "__opts__", {}),
        ):
            assert elasticsearch_state.index_absent("test1") == result

    def test_index_absent_already_gone(self):
        """
        Index not found: no-op success.
        """
        mock_salt = {
            "elasticsearch.index_get": MagicMock(return_value=None),
        }
        result = {
            "name": "test1",
            "changes": {},
            "result": True,
            "comment": "Index test1 is already absent",
        }
        with (
            patch.dict(elasticsearch_state.__salt__, mock_salt),
            patch.object(elasticsearch_state, "__opts__", {}),
        ):
            assert elasticsearch_state.index_absent("test1") == result

    def test_index_absent_failure(self):
        """
        index_get raising is captured as result=False with the error in comment.
        """
        mock_salt = {
            "elasticsearch.index_get": MagicMock(side_effect=Exception("connection refused")),
        }
        with (
            patch.dict(elasticsearch_state.__salt__, mock_salt),
            patch.object(elasticsearch_state, "__opts__", {}),
        ):
            ret = elasticsearch_state.index_absent("test1")
            assert ret["result"] is False
            assert ret["comment"] == "connection refused"


class TestIndexPresent:
    """
    Tests for index_present
    """

    def test_index_present_new_index(self):
        """
        Index missing: created with provided settings, result True.
        """
        mock_salt = {
            "elasticsearch.index_exists": MagicMock(return_value=False),
            "elasticsearch.index_create": MagicMock(return_value=True),
            "elasticsearch.index_get": MagicMock(return_value={"test1": {"abcd"}}),
        }
        with (
            patch.dict(elasticsearch_state.__salt__, mock_salt),
            patch.object(elasticsearch_state, "__opts__", {"test": False}),
        ):
            ret = elasticsearch_state.index_present(
                "test1", shards=3, replicas=1, refresh_interval="30s"
            )
            assert ret["result"] is True
            assert ret["comment"] == "Successfully created index test1"
            mock_salt["elasticsearch.index_create"].assert_called_once()
            kwargs = mock_salt["elasticsearch.index_create"].call_args[1]
            assert kwargs["index"] == "test1"
            assert kwargs["shards"] == 3
            assert kwargs["replicas"] == 1
            assert kwargs["refresh_interval"] == "30s"

    def test_index_present_already_there(self):
        """
        Index already exists: no create call.
        """
        mock_salt = {
            "elasticsearch.index_exists": MagicMock(return_value=True),
            "elasticsearch.index_create": MagicMock(return_value=True),
        }
        with (
            patch.dict(elasticsearch_state.__salt__, mock_salt),
            patch.object(elasticsearch_state, "__opts__", {}),
        ):
            ret = elasticsearch_state.index_present("test1")
            assert ret["result"] is True
            assert ret["comment"] == "Index test1 is already present"
            mock_salt["elasticsearch.index_create"].assert_not_called()

    def test_index_present_create_fails(self):
        """
        index_create returning False yields result False.
        """
        mock_salt = {
            "elasticsearch.index_exists": MagicMock(return_value=False),
            "elasticsearch.index_create": MagicMock(return_value=False),
        }
        with (
            patch.dict(elasticsearch_state.__salt__, mock_salt),
            patch.object(elasticsearch_state, "__opts__", {"test": False}),
        ):
            ret = elasticsearch_state.index_present("test1")
            assert ret["result"] is False
            assert "Cannot create index test1" in ret["comment"]
