# Manual Test Plan: LiteLLM Gateway Routing — Day 07

## Prerequisites

1. **LiteLLM proxy installed**: `pip install litellm[proxy]`
2. **`.env` configured** with `OPENROUTER_API_KEY` and optionally
   `LITELLM_PROXY_API_KEY`.
3. **Proxy started**:
   ```bash
   litellm --config src/gateway/litellm_config.yaml --port 4000
   ```
4. **eComBot `.env` updated**:
   ```env
   LITELLM_PROXY_ENABLED=true
   LITELLM_PROXY_URL=http://localhost:4000
   LITELLM_PROXY_API_KEY=<your-master-key>
   ```

---

## Test 1 — Simple Query Routes to `fast-faq`

| Step | Action | Expected |
|------|--------|----------|
| 1 | Start the proxy, then run `python src/agents/support_agent.py`. | Chat loop starts. |
| 2 | Type: `Where is my order ORD-001?` | Console log shows `Route → fast-faq`. Agent replies with order status. |
| 3 | Check proxy logs (stdout or `litellm.log`). | Request went to model group `fast-faq` (gemini-2.0-flash). |

**Pass**: [ ]

---

## Test 2 — Complex Query Routes to `deep-support`

| Step | Action | Expected |
|------|--------|----------|
| 1 | Type: `I received a damaged item and the wrong product was in the box. I want to escalate this complaint and get a full refund plus compensation.` | Console log shows `Route → deep-support`. |
| 2 | Check proxy logs. | Request went to model group `deep-support` (gemini-2.5-flash). |
| 3 | Verify agent response is coherent and addresses the multi-step concern. | Agent acknowledges damage, offers refund steps. |

**Pass**: [ ]

---

## Test 3 — Fallback Behaviour

| Step | Action | Expected |
|------|--------|----------|
| 1 | In `litellm_config.yaml`, temporarily change `fast-faq`'s model to an invalid string, e.g. `openrouter/INVALID_MODEL_XYZ`. | |
| 2 | Restart the proxy. | |
| 3 | Type a simple query: `What is the return policy?` | Router picks `fast-faq`, proxy fails, then retries with `deep-support`. Agent still answers correctly. |
| 4 | Check proxy logs. | Should see a failed attempt on `fast-faq` followed by a successful call to `deep-support`. |
| 5 | Revert the config change. | |

**Pass**: [ ]

---

## Test 4 — Proxy Disabled (Backward Compatibility)

| Step | Action | Expected |
|------|--------|----------|
| 1 | Set `LITELLM_PROXY_ENABLED=false` in `.env`. | |
| 2 | Stop the proxy (or leave it running — shouldn't matter). | |
| 3 | Run `python src/agents/support_agent.py`. | Agent starts normally. |
| 4 | Type: `What payment methods do you accept?` | Agent replies using the direct OpenRouter endpoint, no proxy involved. |
| 5 | Verify no "Route →" log lines appear in console. | Direct LiteLLM mode used. |

**Pass**: [ ]

---

## Test 5 — Route Log Observability

| Step | Action | Expected |
|------|--------|----------|
| 1 | Enable proxy, set logging to DEBUG (`LOGLEVEL=DEBUG` or code). | |
| 2 | Send 3–4 varied queries. | |
| 3 | Check console output. | Each query has a `Route →` log with model group, confidence, and reasoning. |
| 4 | Verify `GatewayClient` log entries contain all fields. | `model`, `confidence`, `reasoning`, `fallback` present. |

**Pass**: [ ]

---

## Test 6 — Unit Tests Pass

| Step | Action | Expected |
|------|--------|----------|
| 1 | Run: `pytest tests/test_litellm_routing.py -v` | All tests green. |
| 2 | No warnings about import errors. | `src/` path setup works. |

**Pass**: [ ]

---

## Test 7 — Config Override via Environment

| Step | Action | Expected |
|------|--------|----------|
| 1 | Export `LITELLM_FAST_MODEL=my-custom-fast` and `LITELLM_DEEP_MODEL=my-custom-deep`. | |
| 2 | Run the unit tests or agent. | Router uses `my-custom-fast` / `my-custom-deep` as route hints. |
| 3 | Reset the env vars. | |

**Pass**: [ ]

---

## Summary

| Test | Description | Result |
|------|-------------|--------|
| 1 | Simple → fast-faq | [ ] |
| 2 | Complex → deep-support | [ ] |
| 3 | Fallback on failure | [ ] |
| 4 | Proxy disabled compat | [ ] |
| 5 | Observability logs | [ ] |
| 6 | Unit tests pass | [ ] |
| 7 | Config overrides | [ ] |
