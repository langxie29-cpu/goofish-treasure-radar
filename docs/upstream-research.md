# Upstream source review

Checked 2026-10-04 Asia/Shanghai using freshly cloned default-branch HEADs, not README-only. “Last commit” is the retrieved commit timestamp, not a claim that the maintainer remains active. No authenticated Goofish requests were made.

| Repository | HEAD / last commit | License | Findings / reuse |
| --- | --- | --- | --- |
| Usagi-org/ai-goofish-monitor | f85d140b6b45029d9a0925feb96dad733b41396d / 2026-05-18 | MIT, copyright 2025 dingyufei615 | Selected. Layered Python backend, Vue, SQLite migrations, scheduler and notifications; easiest small integration hook. |
| superboyyy/xianyu_spider | eb52bd4d1901eee9ba8035e860583cddf50ead4c / 2026-09-12 | No LICENSE found in retrieved tree | Newer maintenance evidence. Latest core search is HTTP mtop rather than a Playwright crawl; browser handles official login. Do not copy source without permission/license clarification. |
| just-ads/ai-goofish | 259c931442137d4cb105e6f1ed97072c2e0a9655 / 2026-03-02 | MIT, copyright 2025 just-ads | Playwright + Vue, multi-step AI but JSONL results. Architectural reference only; source not imported. |

## Files inspected

Usagi:

- `src/scraper.py`: Chromium browsing, search response interception, detail API, new listings sort, login/challenge detection, pacing, link dedup. Detail `itemDO` was fetched but description not saved. Added `商品描述`; removed webdriver masking/security overrides to honor project requirements. Radar caps pages and forbids rotation/retry after challenges.
- `src/parsers.py`: Chinese item fields (`商品ID`, `商品标题`, `当前售价`, link/images/publication metadata).
- `src/services/item_analysis_dispatcher.py`: bounded asynchronous seller/image/AI/save/notify stage. Single Radar early branch reuses saver and notifier; no AI or extra seller/image requests in this branch.
- `src/infrastructure/persistence/sqlite_connection.py`, `sqlite_bootstrap.py`, `src/services/result_storage_service.py`: SQLite WAL, additive legacy import, tasks/result_items/price_snapshots and raw JSON. Radar uses separate namespaced tables in the same file without altering these.
- `src/services/scheduler_service.py`, `src/core/cron_utils.py`, `src/services/process_service.py`: APScheduler cron launches task subprocesses. Conservative example, disabled until user enables.
- `src/api/routes/accounts.py`, `login_state.py`, `src/infrastructure/config/settings.py`, `chrome-extension/`: account state management and configuration. State files remain local; enhanced browser snapshots are an upstream compatibility feature, not new bypass code.
- `src/services/notification_service.py`, `src/infrastructure/external/notification_clients/{bark_client,webhook_client,factory}.py`: configurable channels, async fan-out, exception capture. No durable outbox yet.
- `src/infrastructure/external/ai_client.py`, `src/services/ai_request_compat.py`: existing AI compatibility code retained but not used by Radar MVP.
- `src/app.py`, API dependencies, front-end authentication helpers: login UI does not enforce complete backend API authentication. Loopback-only Docker binding retained; remote deployment requires an authenticated proxy.
- `Dockerfile`, Compose, runtime requirements, `tests/`: multi-stage Vue/Python/Chromium build. Fixed missing tracked prompts directory COPY and obsolete dockerignore entry. Upstream offline baseline: 115 passed / 2 failed / 3 deselected; failures documented in validation.

superboyyy:

- `xianyu/search.py`, `mtop.py`, `search_query.py`: HTTP search with bounded concurrent pages, normalized query and platform request protocol.
- `xianyu/session.py`, `qr_browser.py`: local session persistence and official login browser.
- `xianyu/models.py`, `config.py`, `app.py`: Tortoise ORM product schema (title/price/area/seller/link_hash/image/publish time), database settings and FastAPI routes. Not the same SQLite domain layer as Usagi.
- `xianyu/im_service.py`, `routers/im.py`: messaging features unrelated to this MVP; explicitly not reused.
- `requirements.txt`, `tests/test_{search_query,qr_login,app,im_protocol}.py`, tree: meaningful auth/search/protocol coverage; no comparable built-in cron+recommendation+notification pipeline found. No Dockerfile/Compose in the retrieved tracked tree. No AI evaluator or LICENSE found. Its tests were inspected, not executed.

just-ads:

- `src/spider/spider.py`, `parsers.py`, `src/utils/browser.py`: browser crawl, response parsing, challenge checks and record construction.
- `src/account/login.py`: interactive password/SMS login sessions with expiration cleanup and login checks.
- `src/types/product.py`: Chinese TypedDict item/seller fields, including description.
- `src/task/result.py`: results appended to JSONL, sorted and aggregated on read, not SQLite result storage.
- `src/server/scheduler.py`: APScheduler with task subprocess lifecycle.
- `src/agent/product_evaluator.py`, `src/ai/client.py`: title/product/seller/image/combine AI stages. Useful future design but too much mandatory AI for this MVP.
- `src/notify/{notify_manager,webhook,base}.py`, `docker-compose.yml`, Dockerfile: modular notifications and buildable Compose with root bind mount.
- `tests/notify/test.py`: limited checked-in notification test coverage compared with Usagi; not executed.

## Import and sync

Original MIT LICENSE remains unchanged. The imported snapshot excludes upstream workflow publishing, environment files and runtime state/data. `tests/fixtures/state.sample.json` contains only `{"session":"dummy"}`; it is a synthetic fixture, not a login state. API credentials detected in reviewed source: no matches to common GitHub/OpenAI/private-key token patterns; this check is not proof against every possible secret format.

```bash
git remote add upstream https://github.com/Usagi-org/ai-goofish-monitor.git
# If upstream is already configured, skip the line above.
git fetch upstream master
git switch -c work/upstream-review
# Inspect changes against the recorded commit before applying selective patches:
git diff f85d140b6b45029d9a0925feb96dad733b41396d upstream/master -- src web-ui
```

This is a source import, not a GitHub fork, and original history is not the base ancestry. Fetch makes the pinned upstream commit available for comparison; selectively port reviewed fixes rather than blindly merging unrelated histories. Never overwrite local changes/state. Radar modules are isolated to simplify synchronization.
