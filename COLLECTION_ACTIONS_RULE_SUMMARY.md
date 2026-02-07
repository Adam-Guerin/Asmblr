# Collection Actions Rule Implementation

## Overview

Added a new rule to automatically propose collection actions when critical fields are marked as "unknown" in the data source tracking system.

## Rule Details

**Rule Name**: `auto-propose-collection-for-unknown-critical-fields`

**Trigger**: Any critical field in `data_source` has value `"unknown"`

**Location**: `app/core/pipeline.py` - `_propose_collection_actions_for_unknown_fields()` method

## Implementation

### Core Method
```python
def _propose_collection_actions_for_unknown_fields(
    self, 
    run_id: str, 
    data_source: dict[str, str], 
    topic: str, 
    decision_missing: list[str]
) -> None:
```

### Integration Point
Called after `data_source` creation but before `PreRunGate` evaluation in the main pipeline.

### Supported Critical Fields

| Field | Priority | Impact | Next Step |
|-------|----------|---------|-----------|
| `pages` | HIGH | CRITICAL - No market signals available | Configure pain_sources in configs/sources.yaml |
| `pains` | HIGH | HIGH - Limited problem understanding | Add more diverse sources or improve extraction |
| `competitors` | MEDIUM | MEDIUM - No competitive analysis | Configure competitor_sources in configs/sources.yaml |
| `seeds` | MEDIUM | LOW - Can proceed with generic analysis | Provide seed inputs via UI or API |

## Outputs

### 1. Collection Actions JSON (`collection_actions.json`)
```json
{
  "topic": "AI productivity tools",
  "unknown_fields": ["pages", "competitors"],
  "actions": [
    {
      "field": "pages",
      "source_missing": "No web sources configured or accessible",
      "next_step": "Configure pain_sources in configs/sources.yaml with valid URLs and APIs",
      "priority": "HIGH",
      "estimated_impact": "CRITICAL - No market signals available"
    }
  ],
  "generated_at": "2026-02-07T14:30:00Z",
  "rule_applied": "auto-propose-collection-for-unknown-critical-fields"
}
```

### 2. Pipeline Progress Logging
```
Collection actions auto-proposed for unknown critical fields: pages (HIGH), competitors (MEDIUM)
```

### 3. Decision Missing Integration
Each action adds entries to `decision_missing` list:
```
"Unknown critical field 'pages': Configure pain_sources in configs/sources.yaml with valid URLs and APIs"
"Unknown critical field 'competitors': Configure competitor_sources in configs/sources.yaml or add competitor analysis tools"
```

## Testing

Comprehensive test suite in `tests/test_collection_actions_rule.py`:

- ✅ **test_collection_actions_proposed_for_unknown_fields** - Verifies actions are generated for unknown fields
- ✅ **test_no_collection_actions_for_all_real_fields** - Verifies no actions when all fields are real  
- ✅ **test_field_impact_estimation** - Verifies impact classification
- ✅ **test_collection_actions_json_structure** - Verifies JSON output format

All tests pass: `4 passed, 13 warnings in 16.14s`

## Benefits

1. **Proactive Guidance**: Automatically suggests specific actions instead of generic failures
2. **Prioritized**: High-impact issues get higher priority recommendations
3. **Structured Output**: JSON format enables downstream automation
4. **Integrated**: Seamlessly fits into existing decision pipeline
5. **Traceable**: Clear rule identification and timestamps

## Usage Examples

### Scenario 1: Missing Market Signals
```
data_source = {
  "pages": "unknown",     // ❌ No web sources
  "pains": "real",        // ✅ Pain statements available
  "competitors": "real",   // ✅ Competitor data available  
  "seeds": "seed"         // ✅ Seed inputs provided
}
```

**Result**: HIGH priority action to configure pain_sources

### Scenario 2: Multiple Unknown Fields
```
data_source = {
  "pages": "unknown",       // ❌ No web sources
  "pains": "unknown",       // ❌ No pain statements
  "competitors": "unknown",  // ❌ No competitor data
  "seeds": "none"          // ⚪ No seed inputs
}
```

**Result**: 3 actions generated with priorities HIGH (pages, pains) and MEDIUM (competitors)

## Files Modified

1. **`app/core/pipeline.py`** - Added rule method and integration
2. **`tests/test_collection_actions_rule.py`** - Comprehensive test suite
3. **`scripts/demo_collection_actions_rule.py`** - Demonstration script
4. **`rule_demo_output.json`** - Rule specification and examples

## Future Enhancements

- [ ] Add dynamic priority calculation based on topic context
- [ ] Integrate with external knowledge base for next steps
- [ ] Add automatic retry mechanisms for failed source configurations
- [ ] Support for custom critical fields beyond the 4 standard ones

---

**Rule Status**: ✅ IMPLEMENTED AND TESTED
