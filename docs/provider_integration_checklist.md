# Provider Integration Checklist

Use this checklist when adding a new remote inference provider to OGX.

## 1. Provider spec

- [ ] Create `src/ogx/providers/registry/<provider>.py` with the `RemoteProviderSpec`.
- [ ] Set `provider_type` to `remote::<provider_name>`.
- [ ] Set `module` to the dotted path of the provider class.
- [ ] Set `config_class` to the dotted path of the Pydantic config.
- [ ] Add `api_dependencies` for each API the provider satisfies.

## 2. Config class

- [ ] Inherit from the appropriate base config.
- [ ] All fields have `Field(description=...)` — this auto-generates provider docs.
- [ ] Required credentials default to reading from environment variables.
- [ ] Add a `test_connection()` method returning `bool`.

## 3. Provider implementation

- [ ] Implement the relevant protocol (`Inference`, `Embeddings`, etc.).
- [ ] Map provider-specific HTTP errors to OGX error types.
- [ ] Streaming responses yield `AsyncIterator` of chunks.
- [ ] Structured logging uses `logger.info("...", key=value)` — no f-strings.
- [ ] All error messages begin with `"Failed to ..."` per coding guidelines.

## 4. Tests

- [ ] Unit test: mock the provider HTTP client and verify request construction.
- [ ] Integration test recording: run with `--inference-mode record-if-missing`.
- [ ] Verify the recording file is committed under `tests/integration/*/recordings/`.

## 5. Documentation

- [ ] Add provider to `README.md` architecture diagram.
- [ ] Run `uv run ./scripts/provider_codegen.py` to regenerate provider docs.
- [ ] Update `ARCHITECTURE.md` if a new storage or transport pattern is introduced.

## 6. Distribution config

- [ ] Add provider to at least one distribution YAML in `src/ogx/distributions/`.
- [ ] Run `uv run ./scripts/distro_codegen.py` to regenerate distribution code.

---

## Error message conventions

All errors raised by provider code must use the prefix `"Failed to ..."` to
align with the OGX error message standard:

```python
# Good
raise ProviderError("Failed to authenticate with ExampleProvider: invalid API key")

# Bad
raise ProviderError("Authentication failed")
```
