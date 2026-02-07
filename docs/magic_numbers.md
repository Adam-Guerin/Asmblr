# Magic Numbers and Configuration Thresholds

This document provides rationale for all hardcoded values, thresholds, and limits used throughout the Asmblr codebase.

## Table of Contents

- [Signal Processing](#signal-processing)
- [Idea Scoring](#idea-scoring)
- [Actionability Assessment](#actionability-assessment)
- [Historical Learning](#historical-learning)
- [Time and Budget Limits](#time-and-budget-limits)
- [Text Processing Limits](#text-processing-limits)
- [Retry and Error Handling](#retry-and-error-handling)
- [Web and Network](#web-and-network)
- [LLM Configuration](#llm-configuration)

## Signal Processing

### `SIGNAL_SOURCES_TARGET=6`
**Rationale**: Minimum number of diverse sources needed for reliable market signal analysis.
**Impact**: Lower values may result in insufficient market diversity; higher values increase processing time.
**Range**: 3-10 recommended.

### `SIGNAL_PAINS_TARGET=8`
**Rationale**: Target number of validated pain points for comprehensive market understanding.
**Impact**: Fewer pains may miss key market needs; more may dilute focus.
**Range**: 5-15 recommended.

### `SIGNAL_DOMAIN_TARGET=4`
**Rationale**: Minimum unique domains for cross-validation of market signals.
**Impact**: Ensures signals aren't from a single source echo chamber.
**Range**: 2-8 recommended.

### `SIGNAL_REPEAT_TARGET=2`
**Rationale**: Minimum repetitions of pain points to indicate market significance.
**Impact**: Higher values indicate stronger market validation but may reduce novelty.
**Range**: 1-5 recommended.

### `SIGNAL_RECENCY_DAYS=365`
**Rationale**: Time window for considering market signals as relevant.
**Impact**: Shorter windows focus on recent trends; longer windows include historical context.
**Range**: 90-730 recommended.

### `MIN_UNIQUE_DOMAINS=2`
**Rationale**: Minimum unique domains to ensure source diversity.
**Impact**: Prevents over-reliance on single source.
**Range**: 2-5 recommended.

### `MIN_AVG_TEXT_LEN=200`
**Rationale**: Minimum average text length for meaningful signal extraction.
**Impact**: Shorter texts may lack context; longer texts provide more detail.
**Range**: 100-500 recommended.

## Idea Scoring

### `IDEA_ACTIONABILITY_MIN_SCORE=55`
**Rationale**: Threshold for considering an idea "actionable" (minimum viable for MVP).
**Impact**: Lower values allow more experimental ideas; higher values require stronger validation.
**Range**: 40-70 recommended.
**Calculation**: Based on 50% being neutral, +5 for minimum viability buffer.

### `IDEA_ACTIONABILITY_ADJUSTMENT_MAX=12`
**Rationale**: Maximum score adjustment for actionability to prevent over-inflation.
**Impact**: Caps the influence of actionability on final scores.
**Range**: 5-25 recommended.
**Formula**: `max_score_adjustment = 25% of total score range`.

### `MARKET_SIGNAL_THRESHOLD=40`
**Rationale**: Minimum market signal score for idea validation.
**Impact**: Higher thresholds require stronger market evidence.
**Range**: 30-60 recommended.

## Actionability Assessment

### Topic Length Limits
- **Minimum**: 3 characters
- **Maximum**: 200 characters
**Rationale**: Ensures topics are meaningful but concise.

### Pain Point Extraction
- **Minimum sentence length**: 20 characters
- **Maximum pains considered**: 50
- **Keywords**: ["pain", "problem", "struggle", "hard", "difficult", "need"]
**Rationale**: Filters for genuine pain points vs. generic statements.

### Testability Assessment
- **Minimum hits**: 1
- **Maximum hits**: 5
**Rationale**: Balances thoroughness with practicality.

## Historical Learning

### `LEARNING_HISTORY_MAX_RUNS=200`
**Rationale**: Maximum historical runs to consider for learning to prevent memory bloat.
**Impact**: Larger values provide more data but increase processing time.
**Range**: 50-500 recommended.

### Learning Rate Defaults
- **Default exploration rate**: 0.1 (10%)
- **Success/failure keywords**: Limited to 8 each
**Rationale**: Balances exploitation of known patterns with exploration.

## Time and Budget Limits

### Execution Profiles
- **Standard**: 60 minutes, 50,000 tokens, 10 sources, 5 ideas
- **Fast**: 20 minutes, 20,000 tokens, 5 sources, 3 ideas
- **Comprehensive**: 120 minutes, 100,000 tokens, 15 sources, 8 ideas

**Rationale**: Different trade-offs between speed and thoroughness.

### Retry Timeouts
- **Stage retry attempts**: 3
- **Budget check interval**: 30 seconds
**Rationale**: Allows transient failures while preventing infinite loops.

## Text Processing Limits

### Content Truncation
- **Failure reason**: 800 characters
- **Traceback hint**: 1200 characters
- **Theme cleaning**: 240 characters
- **Project name**: 80 characters
**Rationale**: Prevents log bloat while preserving essential information.

### Pain Point Processing
- **Sentence minimum**: 20 characters
- **Pain list maximum**: 50 items
**Rationale**: Filters noise while capturing comprehensive feedback.

## Retry and Error Handling

### LLM Retry Configuration
- **Max attempts**: 3
- **Base delay**: 0.5 seconds
- **Max jitter**: 0.2 seconds
**Rationale**: Exponential backoff with jitter to prevent thundering herd.

### Web Request Timeouts
- **Min timeout**: 5 seconds
- **Max timeout**: 60 seconds
- **Connect timeout**: 5 seconds
- **Write timeout**: 10 seconds
- **Pool timeout**: 5 seconds
**Rationale**: Balances responsiveness with reliability.

### Rate Limiting
- **Minimum rate**: 0.1 requests/second
- **Bucket multiplier**: 2.0
- **Jitter range**: 0.05-0.2
**Rationale**: Prevents overwhelming external services.

## Web and Network

### `WEB_MAX_WORKERS=4`
**Rationale**: Optimal balance between concurrency and resource usage.
**Impact**: Higher values may overwhelm targets; lower values reduce throughput.
**Range**: 2-8 recommended.

### User Agent
- **Format**: `AI-Venture-Factory/1.0`
**Rationale**: Identifies traffic source for debugging and rate limiting.

## LLM Configuration

### Token Estimation
- **General model**: Estimated based on input/output length
- **Code model**: Estimated based on code generation patterns
**Rationale**: Prevents unexpected cost overruns.

### Model Selection
- **General model**: Configurable via `GENERAL_MODEL`
- **Code model**: Configurable via `CODE_MODEL`
- **Fallback models**: Built-in defaults for reliability

## Configuration Guidelines

### When to Adjust These Values

1. **Increase `IDEA_ACTIONABILITY_MIN_SCORE`** when:
   - Market has high barriers to entry
   - Ideas require more validation
   - Quality standards are stricter

2. **Decrease `IDEA_ACTIONABILITY_MIN_SCORE`** when:
   - Market moves quickly
   - Rapid prototyping is viable
   - Learning is prioritized over perfection

3. **Adjust Signal Targets** based on:
   - Industry complexity (higher for complex industries)
   - Data availability (lower when data is scarce)
   - Competitive intensity (higher for competitive markets)

4. **Modify Time Limits** for:
   - Resource constraints (reduce for limited resources)
   - Quality requirements (increase for higher quality needs)
   - Development speed (reduce for rapid iteration)

### Monitoring Recommendations

Track these metrics to optimize thresholds:
- **Actionability pass rate**: Target 60-80%
- **Signal quality scores**: Monitor average and distribution
- **Processing time vs. quality**: Find optimal trade-offs
- **Historical learning effectiveness**: Measure prediction accuracy

### Safety Considerations

- **Never set thresholds to 0 or 100** without explicit reasoning
- **Document any deviations** from recommended ranges
- **Test changes** in non-production environments first
- **Monitor system behavior** after adjustments

## Future Improvements

1. **Dynamic Thresholds**: Consider making some thresholds adaptive based on historical performance
2. **Context-Aware Limits**: Adjust limits based on topic complexity and market conditions
3. **User Configuration**: Allow per-project or per-user customization of key thresholds
4. **Automated Optimization**: Use ML to optimize thresholds based on success metrics

---

*Last updated: February 2026*
*For questions or suggestions, please open an issue in the repository.*
