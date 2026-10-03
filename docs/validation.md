# MVP validation

Validation date: 2026-10-04 Asia/Shanghai. Local runtime: Linux / Python 3.12.14. Direct runtime dependencies pinned to locally tested versions; transitive dependencies are not fully locked. Existing upstream uv.lock is a legacy upstream artifact and is not used by the documented pip/Docker workflow.

- Original upstream snapshot, offline baseline: **115 passed, 2 failed, 3 live tests deselected**. Failures were an obsolete dockerignore-path assertion and a raw-result test expecting no newly introduced visibility metadata.
- Current MVP: **189 passed, 3 live tests deselected**. This includes 72 Radar cases: all required price types, body/listed mismatch, negation, context money parsing, specifications, model candidates, interest scoring, independent SQLite persistence, concurrent deduplication, changed/reverted inputs, historical price eligibility, CLI/backfill, and integration proving no AI/image/seller requests in Radar mode.
- Frontend: `npm ci` and `npm run build` passed, including Vue TypeScript checking and Vite production build.
- CLI fixture import and backfill passed against a temporary SQLite database.
- Python source compilation and Git whitespace check passed.
- Pre-publication tracked-file scan: no common GitHub/OpenAI/private-key token patterns and no runtime Cookie/state/database/.env files (synthetic state.sample.json fixture contains only dummy data).
- Docker build/run **not executed**: Docker is not installed in this execution environment. Dockerfile paths and Compose were reviewed; local backend, static output and module integration tested independently.
- Live Goofish crawl **not executed**: no user login state supplied. Upstream parser/dispatcher regression tests pass, but platform selectors and actual account access require a manual first run. Captchas and expired login must be handled on official pages.
- GitHub CI / Windows execution **pending remote publication**. The workflow is committed; local success is not a claim of remote green CI.

Known limits:

1. Rules are heuristics, not calibrated probabilities. Obfuscated wording, text-only prices without recognized context, multiple configurations, negation outside covered phrases and image-only prices may require manual review.
2. Model strings are candidates; no manufacturer/model catalog, OCR or image identification yet.
3. The existing crawler skips processed links, so old-item price revisions need new imported observations until low-frequency re-observation is implemented.
4. History records credible asking prices, not confirmed sale prices. Condition is not yet extracted; no market median/ratio statistics yet.
5. Notifications have no durable outbox/retry. An evaluation is persisted before upstream save/notify; a crash or delivery failure can leave an unsent candidate. Changed descriptions may generate a new notice. Worth-opening depends on interest, not price, so suspicious but interesting items can also be sent with warnings.
6. Upstream Web API is suitable only for a trusted local environment; login UI alone does not enforce server-side authorization. Default Docker port is loopback-only. Use an authenticated reverse proxy including WebSocket before any remote exposure.
7. Radar-specific ranking/filter controls are not implemented in the Vue frontend. Reasons appear via the existing result fields; complete structured data is available in SQLite and JSON.
8. Scheduler rate is configurable; conservative examples and one-page cap are provided, but no global request-budget governor yet. Keep a small number of staggered tasks.
