import logging
import os
import sys
import types

import pytest

try:
    from saltfactories.utils import random_string
except ImportError:
    # saltfactories is only needed for the integration test fixtures below;
    # unit tests do not require it.
    def random_string(prefix):
        import uuid
        return prefix + "-" + str(uuid.uuid4())[:8]

try:
    from saltext.elasticsearch import PACKAGE_ROOT
except ImportError:
    PACKAGE_ROOT = None

# Provide a minimal elasticsearch stub when the real client is not installed,
# so that the unit tests (which use importorskip) can actually run.
try:
    import elasticsearch
except ImportError:
    _es_stub = types.ModuleType("elasticsearch")
    _es_stub.__version__ = (8, 14, 0)

    class TransportError(Exception):
        errors = {}
        message = ""
        status_code = 400
        error = ""

    class NotFoundError(TransportError):
        pass

    class ApiError(TransportError):
        pass

    class BadRequestError(TransportError):
        pass

    _es_stub.TransportError = TransportError
    _es_stub.NotFoundError = NotFoundError
    _es_stub.ApiError = ApiError
    _es_stub.BadRequestError = BadRequestError
    _es_stub.Elasticsearch = None
    _es_stub.exceptions = types.SimpleNamespace(
        TransportError=TransportError,
        NotFoundError=NotFoundError,
        ApiError=ApiError,
        BadRequestError=BadRequestError,
    )
    sys.modules["elasticsearch"] = _es_stub

    _et = types.ModuleType("elastic_transport")
    _et.RequestsHttpNode = object
    sys.modules["elastic_transport"] = _et

# Reset the root logger to its default level(because salt changed it)
logging.root.setLevel(logging.WARNING)


# This swallows all logging to stdout.
# To show select logs, set --log-cli-level=<level>
for handler in logging.root.handlers[:]:  # pragma: no cover
    logging.root.removeHandler(handler)
    handler.close()


@pytest.fixture(scope="session")
def salt_factories_config():  # pragma: no cover
    """
    Return a dictionary with the keyword arguments for FactoriesManager
    """
    return {
        "code_dir": str(PACKAGE_ROOT),
        "inject_sitecustomize": "COVERAGE_PROCESS_START" in os.environ,
        "start_timeout": 120 if os.environ.get("CI") else 60,
    }


@pytest.fixture(scope="package")
def master_config():  # pragma: no cover
    """
    Salt master configuration overrides for integration tests.
    """
    return {}


@pytest.fixture(scope="package")
def master(salt_factories, master_config):  # pragma: no cover
    return salt_factories.salt_master_daemon(random_string("master-"), overrides=master_config)


@pytest.fixture(scope="package")
def minion_config():  # pragma: no cover
    """
    Salt minion configuration overrides for integration tests.
    """
    return {}


@pytest.fixture(scope="package")
def minion(master, minion_config):  # pragma: no cover
    return master.salt_minion_daemon(random_string("minion-"), overrides=minion_config)
