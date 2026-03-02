# Benchmark Datasets

## Overview
This directory contains the datasets used for evaluating the Asmblr system according to the benchmark framework.

## Dataset Structure
```
datasets/
├── README.md                    # This file
├── raw/                        # Raw, unprocessed data
├── processed/                  # Cleaned and standardized data
├── annotations/                # Human expert annotations
├── splits/                     # Train/validation/test splits
└── metadata/                   # Dataset documentation and schemas
```

## Dataset Categories

### 1. Market Signals Dataset
**Source**: Reddit entrepreneurship threads, Product Hunt launches, industry reports
**Size**: ~10,000 market signals
**Format**: JSON with standardized schema
**Time Period**: 2020-2024
**Languages**: English (with some multilingual content)

### 2. Ground Truth Dataset
**Source**: Human expert annotations, historical startup data
**Size**: ~2,000 annotated cases
**Format**: Structured annotations with inter-rater reliability metrics
**Experts**: 3+ domain experts per case
**Reliability**: κ ≥ 0.7 threshold

### 3. Baseline Comparison Dataset
**Source**: Human entrepreneur evaluations, business analyst assessments
**Size**: ~500 human evaluations
**Format**: Standardized evaluation templates
**Participants**: Expert entrepreneurs, business consultants, novices

## Data Quality Standards
- **Completeness**: Minimum 95% data completeness
- **Accuracy**: Expert-validated ground truth
- **Consistency**: Standardized annotation protocols
- **Diversity**: Balanced representation across industries and demographics

## Usage Guidelines
1. Use processed datasets for evaluation
2. Respect data licensing agreements
3. Maintain participant privacy and confidentiality
4. Follow ethical guidelines for AI evaluation

## Citation
If you use these datasets in your research, please cite the Asmblr Benchmark Framework.
