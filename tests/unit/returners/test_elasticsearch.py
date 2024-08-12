"""
Test the elasticsearch returner
"""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

elastic = pytest.importorskip("elasticsearch")

ES_MAJOR_VERSION = elastic.__version__[0]
if ES_MAJOR_VERSION >= 8:
    import saltext.elasticsearch.returners.elasticsearch8_mod as elasticsearch_return
else:
    import saltext.elasticsearch.returners.elasticsearch6_mod as elasticsearch_return


@pytest.fixture
def configure_loader_modules():
    return {elasticsearch_return: {}}


def test__virtual_with_elasticsearch():
    """
    Test __virtual__ function when elasticsearch
    and the elasticsearch module is not available
    """
    with patch.dict(elasticsearch_return.__salt__, {"elasticsearch.index_exists": MagicMock()}):
        result = elasticsearch_return.__virtual__()
        expected = "elasticsearch"
        assert expected == result
