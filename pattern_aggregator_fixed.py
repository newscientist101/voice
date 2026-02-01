#
# Copyright (c) 2024-2026, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

import re
from typing import List, Optional, Tuple
from loguru import logger
from pipecat.utils.text.pattern_pair_aggregator import PatternPairAggregator, PatternMatch, MatchAction

class FixedPatternPairAggregator(PatternPairAggregator):
    """Local fix for PatternPairAggregator bugs in version 0.0.102.dev8.

    Fixes:
    1. Symmetric delimiters (like **) are not detected as starting.
    2. MatchAction.KEEP doesn't strip delimiters from the buffer.
    3. Warnings about multiple matches for KEEP patterns.
    """

    async def _process_complete_patterns(
        self, text: str, last_processed_position: int = 0
    ) -> Tuple[List[PatternMatch], str]:
        all_matches = []
        processed_text = text

        for type, pattern_info in self._patterns.items():
            start = re.escape(pattern_info["start"])
            end = re.escape(pattern_info["end"])
            action = pattern_info["action"]
            regex = f"{start}(.*?){end}"
            match_iter = re.finditer(regex, processed_text, re.DOTALL)
            matches = list(match_iter)

            for match in matches:
                content = match.group(1)
                full_match = match.group(0)
                pattern_match = PatternMatch(content=content.strip(), type=type, full_match=full_match)
                already_processed = match.end() <= last_processed_position

                if not already_processed and type in self._handlers:
                    try:
                        await self._handlers[type](pattern_match)
                    except Exception as e:
                        logger.error(f"Error in pattern handler for {type}: {e}")

                if action == MatchAction.REMOVE:
                    if not already_processed:
                        processed_text = processed_text.replace(full_match, "", 1)
                elif action == MatchAction.KEEP:
                    if not already_processed:
                        processed_text = processed_text.replace(full_match, content, 1)
                else:
                    if not already_processed or action == MatchAction.AGGREGATE:
                        all_matches.append(pattern_match)

        return all_matches, processed_text

    def _match_start_of_pattern(self, text: str) -> Optional[Tuple[int, dict]]:
        for type, pattern_info in self._patterns.items():
            start = pattern_info["start"]
            end = pattern_info["end"]
            start_count = text.count(start)
            end_count = text.count(end)

            if start == end:
                if start_count % 2 != 0:
                    start_index = text.find(start)
                    return [start_index, pattern_info]
                continue

            if start_count > end_count:
                start_index = text.find(start)
                return [start_index, pattern_info]

        return None
