# Local Codex model catalog

`codex_models.json` is an explicit compatibility descriptor for the configured local provider, not an OpenAI product-default model catalog. On 2026-10-27, the 4141 `/v1/models` endpoint advertised `gpt-6.1-sol`, low/medium/high/xhigh/max reasoning efforts, and a 1,050,000-token maximum context. These values populate the descriptor.

Unadvertised harness fields retain Codex 0.157.1 generic defaults; the instruction template is the exact generic prompt from Codex 0.157.1 (`codex-rs/models-manager/prompt.md`), also used by its unknown-model fallback. It is included under the accompanying Apache-2.0 CODEX_LICENSE, not copied from another model's specialized catalog. The Codex-native catalog schema and fallback behavior were checked against the official `rust-v0.157.1` source in `codex-rs/protocol/src/openai_models.rs` and `codex-rs/models-manager/src/model_info.rs`. `model_catalog_json` is the documented configuration interface.

Each ASP session receives this catalog. A missing selected slug is an explicit preparation error. Its hash is part of the settings fingerprint and the actual descriptor is saved with each run. Switching to another model requires an explicit matching descriptor; do not silently relabel a different model's catalog. The older v0.6 debug group used fallback metadata with a 272,000-token maximum and is recorded as such.

Generic prompt SHA256: `ac8ae107a0d72fe3476b430afb161ea4e67da2e446d778aefc44828160559807`.
