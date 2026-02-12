# Toolsmith's Journal

This journal records critical learnings discovered while building tools for the Pipecat bot.

## 2025-01-31 - Journal Initialized
**Learning:** Initialized Toolsmith's journal to track critical learnings.
**Action:** Always check this file before starting a new tool implementation.

## 2025-02-01 - Existing tool bug discovery
**Learning:** Found an `IndexError` in `get_current_weather` when the location had no commas (e.g., "London"). This caused existing tests to fail even though they were previously present.
**Action:** Fixed `get_current_weather` to check if at least one comma exists before attempting to split and access the state part. Always verify existing tests when adding new ones to catch regressions or pre-existing issues.

## 2026-02-02 - User preferences
**Learning:** The user requested that I not create tools that replicate basic LLM abilities like dictionary word lookups and trivia.
**Action:** Always design tools that are legitimately useful and don't copy existing functionality.

## 2026-02-03 - Blocking I/O in Async Tools
**Learning:** Using blocking libraries like `requests` in Pipecat direct functions (which are async) can freeze the event loop, causing audio stuttering or latency in the bot.
**Action:** Always use an asynchronous HTTP client like `httpx` for making API calls in tools.

## 2026-02-04 - Mocking Async Clients in Tests
**Learning:** When mocking `httpx.AsyncClient`, standard `MagicMock` may appear to work in some environments but can fail with `TypeError: object Mock can't be used in 'await' expression` in others. Properly mocking the async context manager and the `get` method with `AsyncMock` is essential for test stability.
**Action:** Always use `AsyncMock` for async methods and correctly set up the `__aenter__` return value for async context managers in unit tests.

## 2026-02-05 - Free News API
**Learning:** The `ok.surf` news API (`https://ok.surf/api/v1/cors/news-feed`) is a reliable free resource for news headlines that does not require an API key.
**Action:** Use this API for news-related functionality when no API keys are available.

## 2026-02-05 - Currency API update
**Learning:** The `api.exchangerate.host` API now requires an access key. An alternative free API is `open.er-api.com`.
**Action:** Prefer `open.er-api.com` for currency conversion tools if no key is provided.

## 2026-02-07 - Time Lookup tool rejected
**Learning:** My local time lookup tool was rejected because its functionality could easily be handled by a Wolfram Alpha query ("time in tokyo")
**Action:** When designing a tool, make sure that it isn't a simple fact or data lookup tool.

## 2026-02-09 - Hacker News tool rejected
**Learning:** My Hacker News search tool was rejected for not providing enough benefit.
**Action:** Avoid designing tools whose functionality is centered around keyword seraches.

## 2026-02-12 - crypto_price tool rejected
**Learning:** My crypto_price tool was rejected because the user is uninterested in crypto.
**Action:** Avoid designing crypto-related tools.
