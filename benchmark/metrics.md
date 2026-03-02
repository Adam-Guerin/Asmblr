# Quantitative Evaluation Metrics for Asmblr Benchmark

## I. Metric Overview

### Metric Categories
1. **Signal Processing Metrics** (SP): Market signal extraction quality
2. **Idea Generation Metrics** (IG): Novelty and feasibility assessment
3. **Decision Quality Metrics** (DQ): ABORT/KILL/PASS decision accuracy
4. **Multi-Agent Coordination Metrics** (MC): Agent collaboration effectiveness
5. **Calibration Metrics** (CM): Confidence and uncertainty assessment

### Composite Scores
- **Entrepreneurial Intelligence Score (EIS)**: Weighted composite of all metrics
- **Market Fit Score (MFS)**: Specific to opportunity validation
- **Technical Viability Score (TVS)**: Technical feasibility assessment
- **Economic Rationality Score (ERS)**: Economic decision quality

## II. Signal Processing Metrics

### SP1: Signal-to-Noise Ratio (SNR)
**Formula**: `SNR = TP / (TP + FP + FN)`

Where:
- TP = True Positives (correctly identified pain points)
- FP = False Positives (incorrectly identified pain points)
- FN = False Negatives (missed pain points)

**Range**: [0, 1], higher is better

### SP2: Pain Point Validity (PPV)
**Formula**: `PPV = Σ(validity_score_i) / N`

Where:
- `validity_score_i` = Human expert rating (1-5) for pain point i
- N = Total number of identified pain points

**Range**: [1, 5], higher is better

### SP3: Market Timing Accuracy (MTA)
**Formula**: `MTA = 1 - |predicted_timing - actual_timing| / max_timing`

**Range**: [0, 1], higher is better

### SP4: Signal Completeness (SC)
**Formula**: `SC = |extracted_signals ∩ ground_truth| / |ground_truth|`

**Range**: [0, 1], higher is better

## III. Idea Generation Metrics

### IG1: Semantic Novelty Score (SNS)
**Formula**: `SNS = 1 - cosine_similarity(idea_embedding, nearest_competitor_embedding)`

**Range**: [0, 1], higher is better

### IG2: Technical Feasibility Score (TFS)
**Formula**: `TFS = (tech_complexity_score + resource_availability_score) / 2`

Where:
- `tech_complexity_score` = 1 - (complexity / max_complexity)
- `resource_availability_score` = available_resources / required_resources

**Range**: [0, 1], higher is better

### IG3: Economic Viability Score (EVS)
**Formula**: `EVS = (market_size_score * profit_margin_score) / implementation_cost_score`

**Range**: [0, 1], higher is better

### IG4: Competitive Differentiation Score (CDS)
**Formula**: `CDS = unique_features_count / total_features_count`

**Range**: [0, 1], higher is better

### IG5: ICP Alignment Score (ICPAS)
**Formula**: `ICPAS = Σ(feature_alignment_i * weight_i) / Σ(weight_i)`

**Range**: [0, 1], higher is better

## IV. Decision Quality Metrics

### DQ1: Decision Accuracy (DA)
**Formula**: `DA = (correct_decisions / total_decisions)`

Where:
- `correct_decisions` = Decisions matching ground truth outcomes
- `total_decisions` = Total ABORT/KILL/PASS decisions made

**Range**: [0, 1], higher is better

### DQ2: Economic Rationality Score (ERS)
**Formula**: `ERS = 1 - |expected_utility - actual_utility| / max_utility`

**Range**: [0, 1], higher is better

### DQ3: Risk Assessment Completeness (RAC)
**Formula**: `RAC = identified_risks / total_known_risks`

**Range**: [0, 1], higher is better

### DQ4: Opportunity Cost Consideration (OCC)
**Formula**: `OCC = 1 if opportunity_costs_considered else 0`

**Range**: {0, 1}, binary

## V. Multi-Agent Coordination Metrics

### MC1: Communication Efficiency (CE)
**Formula**: `CE = useful_information_exchanged / total_communication_volume`

**Range**: [0, 1], higher is better

### MC2: Consensus Quality (CQ)
**Formula**: `CQ = 1 - variance(agent_opinions) / max_variance`

**Range**: [0, 1], higher is better

### MC3: Specialization Benefit (SB)
**Formula**: `SB = (multi_agent_score - monolithic_score) / monolithic_score`

**Range**: [-∞, +∞], positive indicates benefit

### MC4: Conflict Resolution Quality (CRQ)
**Formula**: `CRQ = successful_resolutions / total_conflicts`

**Range**: [0, 1], higher is better

## VI. Calibration Metrics

### CM1: Brier Score (BS)
**Formula**: `BS = (1/N) * Σ(forecast_probability - outcome)^2`

**Range**: [0, 1], lower is better

### CM2: Expected Calibration Error (ECE)
**Formula**: `ECE = Σ(|confidence_i - accuracy_i| * |bucket_i| / N)`

**Range**: [0, 1], lower is better

### CM3: Confidence-Performance Correlation (CPC)
**Formula**: `CPC = Pearson_correlation(confidence_scores, performance_scores)`

**Range**: [-1, 1], higher is better

### CM4: Overconfidence Penalty (OCP)
**Formula**: `OCP = max(0, mean_confidence - mean_accuracy)`

**Range**: [0, 1], lower is better

## VII. Composite Score Formulas

### Entrepreneurial Intelligence Score (EIS)
**Formula**: 
```
EIS = 0.25*SP_avg + 0.30*IG_avg + 0.25*DQ_avg + 0.10*MC_avg + 0.10*CM_avg
```

Where each category average is the mean of its constituent metrics.

### Market Fit Score (MFS)
**Formula**: 
```
MFS = 0.3*PPV + 0.3*ICPAS + 0.2*CDS + 0.2*EVS
```

### Technical Viability Score (TVS)
**Formula**: 
```
TVS = 0.5*TFS + 0.3*RAC + 0.2*OCC
```

### Economic Rationality Score (ERS)
**Formula**: 
```
ERS = 0.4*DA + 0.3*EVS + 0.3*OCP
```

## VIII. Statistical Validation Metrics

### Significance Testing
- **Paired t-test**: Compare Asmblr vs baselines
- **Wilcoxon signed-rank test**: Non-parametric alternative
- **ANOVA**: Multiple group comparisons
- **Effect size**: Cohen's d for practical significance

### Reliability Metrics
- **Cronbach's Alpha**: Internal consistency of metric categories
- **Inter-rater Reliability**: Fleiss' kappa for human annotations
- **Test-Retest Reliability**: Consistency across multiple runs

### Validity Metrics
- **Construct Validity**: Factor analysis of metric structure
- **Criterion Validity**: Correlation with real-world outcomes
- **Content Validity**: Expert evaluation of metric coverage

## IX. Data Collection Procedures

### Automated Metrics
- Extracted directly from system outputs
- Computed using standardized scripts
- Stored in structured JSON format

### Human Annotation Metrics
- Collected through expert evaluation platform
- Minimum 3 independent raters per item
- Inter-rater reliability threshold: κ ≥ 0.7

### Ground Truth Sources
- Historical startup success/failure data
- Market research reports
- Expert business assessments

## X. Metric Thresholds and Benchmarks

### Minimum Acceptable Performance
- **EIS**: ≥0.60
- **SP_avg**: ≥0.70
- **IG_avg**: ≥0.60
- **DQ_avg**: ≥0.75
- **CM_avg**: Brier Score ≤0.25

### Target Performance (State-of-the-Art)
- **EIS**: ≥0.80
- **SP_avg**: ≥0.85
- **IG_avg**: ≥0.80
- **DQ_avg**: ≥0.90
- **CM_avg**: Brier Score ≤0.15

### Human Baseline Performance
- **EIS**: 0.75 (estimated from expert entrepreneurs)
- **SP_avg**: 0.80
- **IG_avg**: 0.70
- **DQ_avg**: 0.85
- **CM_avg**: Brier Score 0.20

## XI. Metric Computation Pipeline

### Input Processing
1. **Standardization**: Convert all outputs to common format
2. **Validation**: Verify data completeness and format
3. **Preprocessing**: Clean and normalize data

### Metric Calculation
1. **Automated Metrics**: Compute using predefined formulas
2. **Human Metrics**: Aggregate expert ratings
3. **Composite Scores**: Calculate weighted combinations

### Output Generation
1. **Score Reports**: Individual and composite metrics
2. **Statistical Analysis**: Significance tests and effect sizes
3. **Visualization**: Charts and graphs for interpretation

## XII. Quality Assurance

### Metric Validation
- **Face Validity**: Expert review of metric definitions
- **Construct Validity**: Statistical validation of metric structure
- **Criterion Validity**: Correlation with external success measures

### Data Quality
- **Missing Data Handling**: Imputation protocols for incomplete data
- **Outlier Detection**: Statistical methods for identifying anomalies
- **Consistency Checks**: Cross-validation of metric calculations

### Reproducibility
- **Version Control**: Track metric definition changes
- **Documentation**: Detailed computation procedures
- **Code Review**: Peer review of calculation scripts
