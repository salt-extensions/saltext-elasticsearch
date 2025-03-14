"""
:codeauthor: Cesar Sanchez <cesan3@gmail.com>
"""

from elasticsearch import NotFoundError
from elasticsearch import TransportError


class ApiResult:
    def __init__(self, meta, body):
        self.meta = meta
        self.body = body


class MockElasticIndices:
    """
    Mock of Elasticsearch IndicesClient
    """

    def __init__(self, found=True, failure=False, ack=True, shards=True, ack_shards=True):
        self.found = found
        self.failure = failure
        self.ack = ack
        self.shards = shards
        self.ack_shards = ack_shards

    def put_alias(self, *args, **kwargs):
        """
        Mock of put_alias method
        """
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"acknowledged": self.ack}

    def delete_alias(self, *args, **kwargs):
        """
        Mock of delete_alias method
        """
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"acknowledged": self.ack}

    def exists_alias(self, *args, **kwargs):
        """
        Mock of exists_alias method
        """
        if not self.found:
            raise NotFoundError("not found error", {}, {})
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"acknowledged": self.ack}

    def get_alias(self, *args, **kwargs):
        """
        Mock of get_alias method
        """
        if not self.found:
            raise NotFoundError("not found error", {}, {})
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"test": "key"}

    def create(self, *args, **kwargs):
        """
        Mock of index method
        """
        if self.failure:
            raise TransportError("customer error", (123, 0))
        if self.shards:
            return {"acknowledged": self.ack, "shards_acknowledged": self.ack_shards}
        else:
            return {"acknowledged": self.ack}

    def delete(self, *args, **kwargs):
        """
        Mock of delete method
        """
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"acknowledged": self.ack}

    def exists(self, *args, **kwargs):
        """
        Mock of exists method
        """
        if not self.found:
            raise NotFoundError("not found error", {}, {})
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return True

    def get(self, *args, **kwargs):
        """
        Mock of get method
        """
        if not self.found:
            raise NotFoundError("not found error", {}, {})
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"test": "key"}

    def open(self, *args, **kwargs):
        """
        Mock of open method
        """
        if not self.found:
            raise NotFoundError("not found error", {}, {})
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"acknowledged": self.ack}

    def close(self, *args, **kwargs):
        """
        Mock of close method
        """
        if not self.found:
            raise NotFoundError("not found error", {}, {})
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"acknowledged": self.ack}

    def put_mapping(self, *args, **kwargs):
        """
        Mock of put_mapping method
        """
        if not self.found:
            raise NotFoundError("not found error", {}, {})
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"acknowledged": self.ack}

    def get_mapping(self, *args, **kwargs):
        """
        Mock of get_mapping method
        """
        if not self.found:
            raise NotFoundError("not found error", {}, {})
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"test": "key"}

    def put_template(self, *args, **kwargs):
        """
        Mock of put_template method
        """
        if not self.found:
            raise NotFoundError("not found error", {}, {})
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"acknowledged": self.ack}

    def delete_template(self, *args, **kwargs):
        """
        Mock of delete_template method
        """
        if not self.found:
            raise NotFoundError("not found error", {}, {})
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"acknowledged": self.ack}

    def exists_index_template(self, *args, **kwargs):
        """
        Mock of exists_template method
        """
        if not self.found:
            return False
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return True

    def exists_template(self, *args, **kwargs):
        """
        Mock of exists_template method
        """
        if not self.found:
            return False
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return True

    def get_template(self, *args, **kwargs):
        """
        Mock of get_template method
        """
        if not self.found:
            raise NotFoundError("not found error", {}, {})
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"test": "key"}

    def get_settings(self, *args, **kwargs):
        """
        Mock of get_settings method
        """
        if not self.found:
            raise NotFoundError("not found error", {}, {})
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"foo": "key"}

    def put_settings(self, **kwargs):
        """
        Mock of get_settings method
        """
        if not self.found:
            raise NotFoundError("not found error", {}, {})
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"acknowledged": True}

    def flush(self, hosts=None, profile=None, **kwargs):
        """
        Mock of flush method
        """
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"_shards": {"failed": 0, "successful": 0, "total": 0}}

    def flush_synced(self, hosts=None, profile=None, **kwargs):
        """
        Mock of flush_synced method
        """
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"_shards": {"failed": 0, "successful": 0, "total": 0}}


class MockElasticCluster:
    """
    Mock of Elasticsearch ClusterClient
    """

    def __init__(self, failure=False):
        self.failure = failure

    def health(self, *args, **kwargs):
        """
        Mock of health method
        """
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return [{"test": "key"}]

    def stats(self, *args, **kwargs):
        """
        Mock of health method
        """
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return [{"test": "key"}]

    def get_settings(self, *args, **kwargs):
        """
        Mock of get_settings method
        """
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"transient": {}, "persistent": {}}

    def put_settings(self, *args, **kwargs):
        """
        Mock of put_settings method
        """
        result = {
            "acknowledged": True,
            "transient": {},
            "persistent": {"indices": {"recovery": {"max_bytes_per_sec": "50mb"}}},
        }
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return result

    def allocation_explain(self, *args, **kwargs):
        """
        Mock of allocation_explain method
        """
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"allocate_explanation": "foo", "can_allocate": "no"}

    def pending_tasks(self, *args, **kwargs):
        """
        Mock of pending tasks method
        """
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {}


class MockElasticNodes:
    """
    Mock of Elasticsearch NodesClient
    """

    def __init__(self, failure=False):
        self.failure = failure

    def info(self, *args, **kwargs):
        """
        Mock of info method
        """
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return [{"test": "key"}]


class MockElasticIndicesPass:
    pass


class MockElasticIngestPass:
    pass


class MockElasticIngest:
    """
    Mock of Elastic Ingest
    """

    def __init__(self, found=True, failure=False, ack=True):
        self.found = found
        self.failure = failure
        self.ack = ack

    def processor_grok(self, *args, **kwargs):
        """
        Mock of processor_grok method
        """
        expected = {"patterns": {}}
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return expected

    def geo_ip_stats(self, *args, **kwargs):
        """
        Mock of geo_ip_stats method
        """
        expected = {
            "stats": {
                "successful_downloads": 0,
                "failed_downloads": 0,
                "total_download_time": 0,
                "databases_count": 0,
                "skipped_updates": 0,
                "expired_databases": 0,
            },
            "nodes": {},
        }
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return expected

    def get_pipeline(self, *args, **kwargs):
        """
        Mock of get_pipeline method
        """
        if not self.found:
            raise NotFoundError("not found error", {}, {})
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"test": "key"}

    def delete_pipeline(self, *args, **kwargs):
        """
        Mock of delete_pipeline method
        """
        if not self.found:
            raise NotFoundError("not found error", {}, {})
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"acknowledged": self.ack}

    def put_pipeline(self, *args, **kwargs):
        """
        Mock of delete_pipeline method
        """
        if not self.found:
            raise NotFoundError("not found error", {}, {})
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"acknowledged": self.ack}

    def simulate(self, *args, **kwargs):
        """
        Mock of simulate method
        """
        if not self.found:
            raise NotFoundError("not found error", {}, {})
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"test": "key"}


class MockElasticSnapshot:
    """
    Mock of elastic snapshot
    """

    def __init__(self, found=True, failure=False, ack=True, accepted=True):
        self.found = found
        self.failure = failure
        self.ack = ack
        self.accepted = accepted

    def get_repository(self, **kwargs):
        """
        Mock of get_repository method
        """
        if not self.found:
            raise NotFoundError("not found error", {}, {})
        if self.failure:
            raise TransportError("customer error", (123, 0))
        result = {
            "foo": {
                "type": "hdfs",
                "settings": {
                    "path": "elastic_snapshots",
                    "max_restore_bytes_per_sec": "1024mb",
                    "uri": "hdfs://foo.host:9000",
                    "max_snapshot_bytes_per_sec": "1024mb",
                },
            }
        }
        return result

    def create_repository(self, **kwargs):
        """
        Mock of create repository method
        """
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"acknowledged": self.ack}

    def delete_repository(self, **kwargs):
        """
        Mock of delete repository method
        """
        if not self.found:
            raise NotFoundError("not found error", {}, {})
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"acknowledged": self.ack}

    def cleanup_repository(self, **kwargs):
        """
        Mock of cleanup repository method
        """
        if not self.found:
            raise NotFoundError("not found error", {}, {})
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"results": {"deleted_bytes": 0, "deleted_blobs": 0}}

    def verify_repository(self, **kwargs):
        """
        Mock of verify repository method
        """
        if not self.found:
            raise NotFoundError("not found error", {}, {})
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"nodes": {"foo": {"name": "node1"}, "bar": {"name": "node2"}}}

    def status(self, **kargs):
        """
        Mock of snapshot status method
        """
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"snapshots": []}

    def get(self, **kargs):
        """
        Mock of snapshot get method
        """
        if not self.found:
            # raise NotFoundError("not found error", {}, {})
            raise TransportError("customer error", (123, 0))
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"snapshots": [{"snapshot": "foo", "uuid": "foo", "repository": "foo"}]}

    def create(self, **kwargs):
        """
        Mock of snapshot create method
        """
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"accepted": self.accepted}

    def clone(self, **kwargs):
        """
        Mock of snapshot create method
        """
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"acknowledged": self.ack}

    def restore(self, **kwargs):
        """
        Mock of snapshot restore method
        """
        from collections import namedtuple  # pylint: disable=import-outside-toplevel

        _api_meta = namedtuple("api_error", "status")
        _meta = _api_meta(0)
        if self.failure:
            # pylint: disable=too-many-function-args
            raise TransportError("error restoring snapshot", _meta, "")
        return {"accepted": self.accepted}

    def delete(self, **kwargs):
        """
        Mock of snapshot delete method
        """
        if not self.found:
            raise NotFoundError("not found error", {}, {})
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"acknowledged": self.ack}


class MockElastic:
    """
    Mock of Elasticsearch client
    """

    def __init__(
        self,
        found=True,
        failure=False,
        accepted=True,
        ack=True,
        shards=True,
        ack_shards=True,
        no_indices=False,
        no_ingest=False,
    ):
        self.failure = failure
        self.found = found
        self.ack = ack
        self.nodes = MockElasticNodes(failure=failure)
        self.cluster = MockElasticCluster(failure=failure)
        self.snapshot = MockElasticSnapshot(
            found=found, failure=failure, ack=ack, accepted=accepted
        )
        if no_indices:
            self.indices = MockElasticIndicesPass()
        else:
            self.indices = MockElasticIndices(
                found=found,
                failure=failure,
                ack=ack,
                shards=shards,
                ack_shards=ack_shards,
            )
        if no_ingest:
            self.ingest = MockElasticIngestPass()
        else:
            self.ingest = MockElasticIngest(found=found, failure=failure, ack=ack)

    def ping(self, *args, **kwargs):
        """
        Mock of ping method
        """
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return True

    def info(self, *args, **kwargs):
        """
        Mock of info method
        """
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return [{"test": "key"}]

    def index(self, *args, **kwargs):
        """
        Mock of index method
        """
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"test": "key"}

    def delete(self, *args, **kwargs):
        """
        Mock of delete method
        """
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"test": "key"}

    def exists(self, *args, **kwargs):
        """
        Mock of exists method
        """
        if not self.found:
            return False
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return True

    def get(self, *args, **kwargs):
        """
        Mock of index method
        """
        if not self.found:
            raise NotFoundError("not found error", {}, {})
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"test": "key"}

    def get_script(self, *args, **kwargs):
        """
        Mock of get_script method
        """
        if not self.found:
            raise NotFoundError("not found error", {}, {})
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"test": "key"}

    def put_script(self, *args, **kwargs):
        """
        Mock of put_script method
        """
        if not self.found:
            raise NotFoundError("not found error", {}, {})
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"acknowledged": self.ack}

    def delete_script(self, *args, **kwargs):
        """
        Mock of delete_template method
        """
        if not self.found:
            raise NotFoundError("not found error", {}, {})
        if self.failure:
            raise TransportError("customer error", (123, 0))
        return {"acknowledged": self.ack}
