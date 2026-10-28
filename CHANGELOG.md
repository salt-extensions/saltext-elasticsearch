The changelog format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

This project uses [Semantic Versioning](https://semver.org/) - MAJOR.MINOR.PATCH

# Changelog

## 1.2.4 (2026-10-28)


### Changed

- Sync custom returner fixes from the Rentec salt-ext-elasticsearch fork.

  Elasticsearch returners (v1/v2 alias rotation,
  `fun_args` in the payload, master job-cache and event-cache functions, SSH
  client fallback via `document_get`/`document_update`, and `states_*` options).
  This change brings those fixes into the extension:
  - Update schema for elastic search to avoid indexing issues. Blobs avoid the
    inherent issue with strong typing in elasticsearch and weak typing in python
  - ``returner``: keys containing dots are converted with the original key
    preserved, ``fun_args`` is indexed, and a load carrying ``data`` (but no
    ``return``) is normalized so the payload is not null.
  - ``states_order_output``: iterate over a copy of the return dict to avoid a
    ``RuntimeError`` on modern Pythons.
  - ``event_return``: index every event instead of only the last one.
  - Master job-cache functions (``save_load``, ``get_load``, ``get_jid``,
    ``get_jids``, ``get_fun``, ``get_minions``) return the Salt
    job-cache-compatible payloads.
  - Client import fallback: prefer ``elasticsearch8`` and fall back to
    ``elasticsearch`` when it is not installed (the ``elasticsearch8`` module
    pair only; the ES6/ES9 returner and execution modules use the versionless
    client).
  - Restore accidentally removed version-specific ``__virtual__`` gates so exactly one returner
    loads per environment: ES6 rejects an 8+ client, ES8 rejects 9+ clients,
    and ES9 rejects clients older than 9. Each returner now pulls its matching
    execution module when self-loading over SSH.
  - Tests run locally and passed [#27](https://github.com/salt-extensions/saltext-elasticsearch/issues/27)


### Fixed

- Fix docutils errors (``Unknown target name: "id"``) in the ``elasticsearch`` execution
  module docs. The ES8-style ``id_`` parameter name in the ``elasticsearch6_mod`` docstrings
  was parsed as an implicit hyperlink reference, failing the docs build under ``-W``.

  Address PR review findings for the master job cache returner:
  - ``get_minions`` now aggregates on ``Minions.keyword`` (the field the cache docs
    actually populate) instead of the legacy ``load.id.keyword``, which returned no
    buckets on the new ``-v2`` indexes.
  - ``_add_minion_to_doc`` uses ``Minions`` as the upsert key so the upsert path
    creates the same field the script appends to.
  - ``get_load`` no longer crashes on jobs cached without arguments, and
    ``_make_cache_doc`` gives ``fun_args`` precedence over the singular ``fun_arg``.
  - The ES6 execution module ``search`` function now passes ``source_excludes`` as
    the ``_source.excludes`` body form instead of the invalid ``_source_exclude`` key,
    which broke ``get_jid`` on the ES6/SSH path.
  - Restored the non-dict guard for ``states_count`` state counting in all returners
    (regression vs ``main``).
  - ``_ensure_index`` only tolerates already-exists races; real index/alias failures
    now propagate, and the race handling is consistent across ``returner``,
    ``save_load`` and ``event_return``.
  - The ES8 execution module ``document_create`` no longer swallows
    ``BadRequestError``, which silently dropped returner documents.
  - The ES6 execution module ``document_update`` accepts ``retry_on_conflict``
    again, matching what all returners pass.
  - ``document_get_all`` no longer hard-sorts by ``@timestamp``; the sort is an
    optional parameter.
  - Ported the ``failover`` host-probing connection setup to the ES6 and ES9
    execution modules (previously only available in the ES8 module).
  - ``retry_on_conflicts`` is now a proper returner option (default 5) and is
    documented, along with the ``dev`` and ``failover`` options and the ``-v1`` to
    ``-v2`` alias-rotation behavior of the master job cache.
  - Master job cache returner tests are now parametrized across all three returner
    modules; the global ``elasticsearch`` test stub was removed so
    ``pytest.importorskip`` skips honestly when the client is not installed.
  - Fixed copy-paste typos and docstring version claims across the modules and
    returners (``librarielastic``, ``elasticserach``, ``elasicsearch``, ``8.x``
    headers) and out-of-scope ``{id}`` f-strings in ES8/ES9 module error messages.
  - Replaced the string-spliced JID query and the ``eval`` based SSH module loading
    with ``json.dumps`` and ``getattr``. [#27](https://github.com/salt-extensions/saltext-elasticsearch/issues/27)

## 1.2.3 (2026-02-08)


### Fixed

- Fixed a crash in the elasticsearch9 returner when `states_order_output` is enabled (dict modified during iteration). Fixed `event_return()` to index each event individually instead of only the last one. Fixed `search()` in both elasticsearch8 and elasticsearch9 modules to parse JSON string `body` arguments before calling `.get()`. [#22](https://github.com/salt-extensions/saltext-elasticsearch/issues/22)

## 1.2.1 (2024-01-17)


### Added

- Fixed towncrier config and changelog to release [#6](https://github.com/salt-extensions/saltext-elasticsearch/pull/6)

## [1.1.1](https://github.com/cesan3/salt-ext-elasticsearch/compare/1.1.0...1.1.1) - 2023-11-17
- fix: pass correct id attribute name by @cesan3 in https://github.com/cesan3/salt-ext-elasticsearch/pull/20

## [1.1.0](https://github.com/cesan3/salt-ext-elasticsearch/compare/1.0.0...1.1.0) - 2023-11-17
- Fix returner for ES8 by @cesan3 in https://github.com/cesan3/salt-ext-elasticsearch/pull/18

## [1.0.0](https://github.com/cesan3/salt-ext-elasticsearch/compare/0.0.8...1.0.0) - 2023-11-08
- Merge upstream by @cesan3 in https://github.com/cesan3/salt-ext-elasticsearch/pull/16

## [0.0.8](https://github.com/cesan3/salt-ext-elasticsearch/compare/0.0.7...0.0.8) - 2023-11-06
- fix: add elasticsearch returner by @cesan3 in https://github.com/cesan3/salt-ext-elasticsearch/pull/14

## [0.0.7](https://github.com/cesan3/salt-ext-elasticsearch/compare/0.0.6...0.0.7) - 2023-11-06
- Revert "fix: obsoletes saltext.elasticsearch8" by @cesan3 in https://github.com/cesan3/salt-ext-elasticsearch/pull/12

## [0.0.6](https://github.com/cesan3/salt-ext-elasticsearch/compare/0.0.5...0.0.6) - 2023-11-06
- fix: obsoletes saltext.elasticsearch8 by @cesan3 in https://github.com/cesan3/salt-ext-elasticsearch/pull/10

## [0.0.5](https://github.com/cesan3/salt-ext-elasticsearch/compare/0.0.4...0.0.5) - 2023-11-06
- fix: add flush_synced method to ES6 module by @cesan3 in https://github.com/cesan3/salt-ext-elasticsearch/pull/8

## [0.0.4](https://github.com/cesan3/salt-ext-elasticsearch/compare/0.0.3...0.0.4) - 2023-11-06
- fix: update test workflow by @cesan3 in https://github.com/cesan3/salt-ext-elasticsearch/pull/6

## [0.0.3](https://github.com/cesan3/salt-ext-elasticsearch/compare/0.0.2...0.0.3) - 2023-11-06
- Update release.yml by @cesan3 in https://github.com/cesan3/salt-ext-elasticsearch/pull/4

## [0.0.2](https://github.com/cesan3/salt-ext-elasticsearch/compare/0.0.1...0.0.2) - 2023-11-06
- feat: Adding elasticsearch extension module by @cesan3 in https://github.com/cesan3/salt-ext-elasticsearch/pull/1
- fix: update README by @cesan3 in https://github.com/cesan3/salt-ext-elasticsearch/pull/2

## [0.0.1](https://github.com/cesan3/salt-ext-elasticsearch/commits/0.0.1) - 2023-11-04
