from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import salt.modules.cp as cp

import saltext.elasticsearch.states.elasticsearch_mod as elasticsearch_state
from tests.support.unit import TestCase

elastic = pytest.importorskip("elasticsearch")


def get_es_config(key):
    config_es = {"elasticsearch": {"host": "http://localhost:9200"}}
    return config_es.get(key)


@pytest.fixture
def configure_loader_modules():
    index_get_result = {"test1": {"abcd"}}
    module_globals = {
        "__salt__": {
            "config.option": get_es_config,
            "cp.get_file_str": cp.get_file_str,
            "elasticsearch.index_get": MagicMock(return_value=index_get_result),
        },
        "__opts__": {},
    }
    return {
        elasticsearch_state: module_globals,
    }


class ElasticsearchTestCase(TestCase):
    """
    Elasticsearch TestCase
    """

    def setUp(self):
        self.__opts__ = {"test": True}

    def tearDown(self):
        del self.__opts__

    def test_index_absent_test(self, hosts=None, profile=None):  # pylint: disable=unused-argument
        """
        Test of the index_absent method
        """
        result = {
            "name": "test1",
            "changes": {"old": {"abcd"}},
            "result": None,
            "comment": "Index test1 will be removed",
        }
        with patch.object(elasticsearch_state, "__opts__", MagicMock(return_value=self.__opts__)):
            assert elasticsearch_state.index_absent("test1") == result
