# Toolsmith's Journal

This journal records critical learnings discovered while building tools for the Pipecat bot.

## 2025-05-15 - Journal Initialized
**Learning:** Initialized Toolsmith's journal to track critical learnings.
**Action:** Always check this file before starting a new tool implementation.

## 2025-05-15 - Existing tool bug discovery
**Learning:** Found an `IndexError` in `get_current_weather` when the location had no commas (e.g., "London"). This caused existing tests to fail even though they were previously present.
**Action:** Fixed `get_current_weather` to check if at least one comma exists before attempting to split and access the state part. Always verify existing tests when adding new ones to catch regressions or pre-existing issues.
