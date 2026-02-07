"""Centralized threshold definitions with documentation.

This module provides well-documented constants for all thresholds, limits,
and magic numbers used throughout the codebase. Each value includes
rationale, impact analysis, and recommended ranges.
"""

from __future__ import annotations
from typing import Final


# ============================================================================
# SIGNAL PROCESSING THRESHOLDS
# ============================================================================

SIGNAL_SOURCES_TARGET: Final[int] = 6
"""Minimum number of diverse sources needed for reliable market signal analysis.

Rationale: Ensures sufficient data diversity for reliable market insights.
Impact: Lower values may result in insufficient market diversity; 
         higher values increase processing time and may include noise.
Recommended Range: 3-10
"""

SIGNAL_PAINS_TARGET: Final[int] = 8
"""Target number of validated pain points for comprehensive market understanding.

Rationale: Balances thoroughness with focus on key market needs.
Impact: Fewer pains may miss key market needs; 
         more may dilute focus and increase noise.
Recommended Range: 5-15
"""

SIGNAL_DOMAIN_TARGET: Final[int] = 4
"""Minimum unique domains for cross-validation of market signals.

Rationale: Prevents over-reliance on single source echo chambers.
Impact: Ensures signals aren't all from the same domain.
Recommended Range: 2-8
"""

SIGNAL_REPEAT_TARGET: Final[int] = 2
"""Minimum repetitions of pain points to indicate market significance.

Rationale: Multiple mentions indicate genuine market pain vs. isolated incidents.
Impact: Higher values indicate stronger market validation but may reduce novelty.
Recommended Range: 1-5
"""

SIGNAL_RECENCY_DAYS: Final[int] = 365
"""Time window for considering market signals as relevant (in days).

Rationale: One year provides good balance of recent trends and historical context.
Impact: Shorter windows focus on recent trends; 
         longer windows include historical context but may include outdated data.
Recommended Range: 90-730
"""

MIN_UNIQUE_DOMAINS: Final[int] = 2
"""Minimum unique domains to ensure source diversity.

Rationale: Basic diversity requirement for signal validation.
Impact: Prevents over-reliance on single source.
Recommended Range: 2-5
"""

MIN_AVG_TEXT_LEN: Final[int] = 200
"""Minimum average text length for meaningful signal extraction.

Rationale: Ensures sufficient context for reliable analysis.
Impact: Shorter texts may lack context; longer texts provide more detail.
Recommended Range: 100-500
"""

MARKET_SIGNAL_THRESHOLD: Final[int] = 40
"""Minimum market signal score for idea validation.

Rationale: Baseline threshold for market validation.
Impact: Higher thresholds require stronger market evidence.
Recommended Range: 30-60
"""


# ============================================================================
# IDEA SCORING AND ACTIONABILITY
# ============================================================================

IDEA_ACTIONABILITY_MIN_SCORE: Final[int] = 55
"""Threshold for considering an idea "actionable" (minimum viable for MVP).

Rationale: Based on 50% being neutral, +5 for minimum viability buffer.
Impact: Lower values allow more experimental ideas; 
         higher values require stronger validation.
Recommended Range: 40-70
"""

IDEA_ACTIONABILITY_ADJUSTMENT_MAX: Final[int] = 12
"""Maximum score adjustment for actionability to prevent over-inflation.

Rationale: Caps actionability influence at 25% of total score range (0-50).
Impact: Prevents actionability from overwhelming other scoring factors.
Recommended Range: 5-25
"""

IDEA_ACTIONABILITY_REQUIRE_ELIGIBLE_TOP: Final[bool] = False
"""Require at least one actionable idea to proceed.

Rationale: Default to flexible execution while maintaining quality standards.
Impact: True = stricter quality control, False = use best available idea.
"""


# ============================================================================
# HISTORICAL LEARNING
# ============================================================================

LEARNING_HISTORY_MAX_RUNS: Final[int] = 200
"""Maximum historical runs to consider for learning.

Rationale: Balances learning data with processing performance.
Impact: Larger values provide more data but increase processing time.
Recommended Range: 50-500
"""

LEARNING_EXPLORATION_RATE: Final[float] = 0.18
"""Default exploration rate for balancing known patterns vs. new ideas.

Rationale: 18% exploration encourages innovation while leveraging proven patterns.
Impact: Higher = more exploration, Lower = more exploitation.
Recommended Range: 0.1-0.3
"""

LEARNING_SUCCESS_BONUS_MAX: Final[int] = 8
"""Maximum bonus for success patterns in historical learning.

Rationale: Rewards proven patterns without over-emphasizing them.
Impact: Higher values reward proven patterns more strongly.
Recommended Range: 5-15
"""

LEARNING_FAILURE_PENALTY_MAX: Final[int] = 10
"""Maximum penalty for failure patterns in historical learning.

Rationale: Penalizes failed patterns to guide away from risks.
Impact: Higher values penalize failed patterns more strongly.
Recommended Range: 5-20
"""

LEARNING_NOVELTY_BONUS_MAX: Final[int] = 6
"""Maximum bonus for novel ideas in historical learning.

Rationale: Encourages innovation while maintaining practicality.
Impact: Higher values encourage innovation more.
Recommended Range: 3-10
"""

LEARNING_CLONE_PENALTY_START: Final[float] = 0.75
"""Starting point for clone penalty in historical learning.

Rationale: Begins penalizing similarity at 75% match threshold.
Impact: Higher values penalize similar ideas more strongly.
Recommended Range: 0.5-0.9
"""


# ============================================================================
# TEXT PROCESSING LIMITS
# ============================================================================

TOPIC_MIN_LENGTH: Final[int] = 3
"""Minimum topic length in characters."""
TOPIC_MAX_LENGTH: Final[int] = 200
"""Maximum topic length in characters.

Rationale: Ensures topics are meaningful but concise.
Impact: Prevents overly brief or excessively long topics.
"""

PAIN_SENTENCE_MIN_LENGTH: Final[int] = 20
"""Minimum sentence length for pain point extraction."""
PAIN_LIST_MAX_SIZE: Final[int] = 50
"""Maximum number of pain points to consider."""

PAIN_KEYWORDS: Final[list[str]] = [
    "pain", "problem", "struggle", "hard", "difficult", "need"
]
"""Keywords indicating genuine pain points vs. generic statements."""


# ============================================================================
# RETRY AND ERROR HANDLING
# ============================================================================

STAGE_RETRY_ATTEMPTS: Final[int] = 3
"""Maximum retry attempts for pipeline stages."""
BUDGET_CHECK_INTERVAL: Final[int] = 30
"""Budget status check interval in seconds."""

FAILURE_REASON_MAX_LENGTH: Final[int] = 800
"""Maximum length for failure reason truncation."""
TRACEBACK_HINT_MAX_LENGTH: Final[int] = 1200
"""Maximum length for traceback hint truncation."""
RECENT_FAILURES_COUNT: Final[int] = 10
"""Number of recent failures to display in reports."""


# ============================================================================
# CONTENT GENERATION LIMITS
# ============================================================================

PROJECT_NAME_MAX_LENGTH: Final[int] = 80
"""Maximum project name length in characters."""
THEME_CLEAN_MAX_LENGTH: Final[int] = 240
"""Maximum theme description length after cleaning."""

# ============================================================================
# LEARNING AND ADJUSTMENT LIMITS
# ============================================================================

KEYWORD_LIST_MAX_SIZE: Final[int] = 8
"""Maximum number of success/failure keywords to store."""
ICP_ALIGNMENT_BONUS_MAX: Final[int] = 8
"""Maximum ICP alignment bonus score."""


# ============================================================================
# VALIDATION HELPERS
# ============================================================================

def validate_threshold_range(
    value: int | float,
    min_val: int | float,
    max_val: int | float,
    name: str,
) -> None:
    """Validate that a threshold value is within recommended range.
    
    Args:
        value: The value to validate
        min_val: Minimum recommended value
        max_val: Maximum recommended value  
        name: Name of the threshold for error messages
        
    Raises:
        ValueError: If value is outside recommended range
    """
    if not (min_val <= value <= max_val):
        raise ValueError(
            f"{name}={value} is outside recommended range [{min_val}, {max_val}]. "
            f"See docs/magic_numbers.md for guidance."
        )


def get_threshold_summary() -> dict[str, dict[str, str | int | float]]:
    """Get summary of all thresholds with their documentation.
    
    Returns:
        Dictionary mapping threshold names to their values and documentation
    """
    return {
        "signal_processing": {
            "sources_target": SIGNAL_SOURCES_TARGET,
            "pains_target": SIGNAL_PAINS_TARGET,
            "domain_target": SIGNAL_DOMAIN_TARGET,
            "repeat_target": SIGNAL_REPEAT_TARGET,
            "recency_days": SIGNAL_RECENCY_DAYS,
            "min_unique_domains": MIN_UNIQUE_DOMAINS,
            "min_avg_text_len": MIN_AVG_TEXT_LEN,
            "market_threshold": MARKET_SIGNAL_THRESHOLD,
        },
        "idea_scoring": {
            "actionability_min_score": IDEA_ACTIONABILITY_MIN_SCORE,
            "actionability_adjustment_max": IDEA_ACTIONABILITY_ADJUSTMENT_MAX,
            "require_eligible_top": IDEA_ACTIONABILITY_REQUIRE_ELIGIBLE_TOP,
        },
        "historical_learning": {
            "history_max_runs": LEARNING_HISTORY_MAX_RUNS,
            "exploration_rate": LEARNING_EXPLORATION_RATE,
            "success_bonus_max": LEARNING_SUCCESS_BONUS_MAX,
            "failure_penalty_max": LEARNING_FAILURE_PENALTY_MAX,
            "novelty_bonus_max": LEARNING_NOVELTY_BONUS_MAX,
            "clone_penalty_start": LEARNING_CLONE_PENALTY_START,
        },
        "text_processing": {
            "topic_min_length": TOPIC_MIN_LENGTH,
            "topic_max_length": TOPIC_MAX_LENGTH,
            "pain_sentence_min_length": PAIN_SENTENCE_MIN_LENGTH,
            "pain_list_max_size": PAIN_LIST_MAX_SIZE,
        },
    }
