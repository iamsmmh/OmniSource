# OmniSource plugins

Plugins extend the core without editing the pipeline. Supported capabilities:

- source format detection and normalization;
- feed validators;
- metadata enrichment providers;
- feed generators for future client formats.

Implement the protocols in [`src/omnisource/plugins.py`](../src/omnisource/plugins.py),
package the plugin with a pinned dependency, and enable it only through the
reviewed allow-list in `config/plugins.json`. Discovery results can never
select or import a plugin. The default runtime registers only the built-in
AltStore-family JSON normalizer and metadata validator.

A plugin must be deterministic, network-timeout aware, and covered by tests.
It must not receive credentials unless its provider explicitly requires a
host-scoped API token.
