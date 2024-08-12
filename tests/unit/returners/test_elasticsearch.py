"""
Test the elasticsearch returner
"""

import pytest

from tests.support.mock import MagicMock
from tests.support.mock import patch
from tests.support.unit import TestCase

HAS_ELASTIC = True
try:
    import elasticsearch as elastic
except Exception:  # pylint: disable=broad-except
    HAS_ELASTIC = False

if HAS_ELASTIC:
    ES_MAJOR_VERSION = elastic.__version__[0]
    if ES_MAJOR_VERSION >= 8:
        import saltext.elasticsearch.returners.elasticsearch8_mod as elasticsearch_return
        from tests.support.esmockutils.elasticsearch_mock8 import MockElastic
    else:
        import saltext.elasticsearch.returners.elasticsearch6_mod as elasticsearch_return
        from tests.support.esmockutils.elasticsearch_mock import MockElastic


@pytest.fixture
def configure_loader_modules():
    return {elasticsearch_return: {}}


@pytest.mark.skipif(
    not HAS_ELASTIC,
    reason="Install elasticsearch-py before running Elasticsearch unit tests.",
)
class ElasticSearchReturnerTestCase(TestCase):
    def test__virtual_with_elasticsearch(self):
        """
        Test __virtual__ function when elasticsearch
        and the elasticsearch module is not available
        """
        with patch.dict(elasticsearch_return.__salt__, {"elasticsearch.index_exists": MagicMock()}):
            result = elasticsearch_return.__virtual__()
            expected = "elasticsearch"
            assert expected == result
