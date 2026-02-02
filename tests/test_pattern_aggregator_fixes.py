
import pytest
import asyncio
from pattern_aggregator_fixed import FixedPatternPairAggregator, MatchAction

@pytest.mark.asyncio
async def test_symmetric_delimiters_keep():
    agg = FixedPatternPairAggregator()
    agg.add_pattern(type="Bold", start_pattern="**", end_pattern="**", action=MatchAction.KEEP)

    # Test streaming input
    results = []
    text = "This is **bold** text."
    for char in text:
        async for match in agg.aggregate(char):
            results.append(match)

    remaining = await agg.flush()
    if remaining:
        results.append(remaining)

    # Expectation: The final flushed text should have ** removed.
    assert len(results) == 1
    assert results[0].text == "This is bold text."

@pytest.mark.asyncio
async def test_multiple_symmetric_delimiters_no_warning(caplog):
    agg = FixedPatternPairAggregator()
    agg.add_pattern(type="Bold", start_pattern="**", end_pattern="**", action=MatchAction.KEEP)

    text = "This is **bold**, **so** is **this**."
    async for _ in agg.aggregate(text):
        pass

    remaining = await agg.flush()
    assert remaining.text == "This is bold, so is this."

    # Check that there were no "Multiple patterns matched" warnings
    for record in caplog.records:
        assert "Multiple patterns matched" not in record.message

@pytest.mark.asyncio
async def test_asymmetric_delimiters_keep():
    agg = FixedPatternPairAggregator()
    agg.add_pattern(type="Code", start_pattern="<code>", end_pattern="</code>", action=MatchAction.KEEP)

    text = "Here is <code>some code</code>."
    async for _ in agg.aggregate(text):
        pass

    remaining = await agg.flush()
    assert remaining.text == "Here is some code."

@pytest.mark.asyncio
async def test_mixed_delimiters():
    agg = FixedPatternPairAggregator()
    agg.add_pattern(type="Bold", start_pattern="**", end_pattern="**", action=MatchAction.KEEP)
    agg.add_pattern(type="Italic", start_pattern="*", end_pattern="*", action=MatchAction.KEEP)

    text = "This is **bold** and *italic*."
    async for _ in agg.aggregate(text):
        pass

    remaining = await agg.flush()
    assert remaining.text == "This is bold and italic."
