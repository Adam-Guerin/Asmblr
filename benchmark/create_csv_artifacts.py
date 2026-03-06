#!/usr/bin/env python3
"""
Create CSV output artifacts for the scaled dataset.
"""

import json
import csv
from pathlib import Path
from collections import Counter

def create_csv_artifacts(dataset_path: str):
    """Create CSV artifacts for the scaled dataset."""
    dataset_dir = Path(dataset_path)
    
    # Load all contexts
    contexts = []
    for file_path in dataset_dir.glob("context_*.json"):
        with open(file_path, 'r', encoding='utf-8') as f:
            context = json.load(f)
            contexts.append(context)
    
    print(f"Loaded {len(contexts)} contexts")
    
    # Dataset summary CSV
    with open(dataset_dir / "dataset_summary_10k.csv", 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['metric', 'value'])
        writer.writerow(['total_contexts', len(contexts)])
        writer.writerow(['scaling_factor', len(contexts) / 1000])
        
        # Industry breakdown
        industries = Counter(c.get('industry_tag', 'other') for c in contexts)
        for industry, count in sorted(industries.items()):
            writer.writerow([f'industry_{industry}', count])
        
        # Geographic breakdown
        geo_clusters = Counter(c.get('geographic_cluster', 'global') for c in contexts)
        for geo, count in sorted(geo_clusters.items()):
            writer.writerow([f'geo_{geo}', count])
        
        # Stage breakdown
        stages = Counter(c.get('estimated_stage', 'idea') for c in contexts)
        for stage, count in sorted(stages.items()):
            writer.writerow([f'stage_{stage}', count])
        
        # Source breakdown
        sources = Counter(c.get('metadata', {}).get('platform', 'unknown') for c in contexts)
        for source, count in sorted(sources.items()):
            writer.writerow([f'source_{source}', count])
    
    # Uncertainty distribution CSV
    def infer_uncertainty(context):
        if context.get('metadata', {}).get('generated_for_uncertainty'):
            return context['metadata']['generated_for_uncertainty']
        
        raw_text = context.get('raw_text', '')
        pains = context.get('extracted_pains', [])
        competitors = context.get('extracted_competitors', [])
        
        uncertainty_score = 0
        
        if len(raw_text) < 100:
            uncertainty_score += 2
        elif len(raw_text) < 300:
            uncertainty_score += 1
            
        if not pains:
            uncertainty_score += 1
            
        if not competitors:
            uncertainty_score += 1
            
        if context.get('metadata', {}).get('platform') == 'synthetic_realistic':
            uncertainty_score += 1
        
        if uncertainty_score >= 4:
            return 'high'
        elif uncertainty_score >= 2:
            return 'medium'
        else:
            return 'low'
    
    uncertainty_levels = Counter(infer_uncertainty(c) for c in contexts)
    
    with open(dataset_dir / "uncertainty_distribution_10k.csv", 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['uncertainty_level', 'count', 'percentage'])
        total = sum(uncertainty_levels.values())
        
        for level in ['low', 'medium', 'high']:
            count = uncertainty_levels.get(level, 0)
            percentage = (count / total) * 100 if total > 0 else 0
            writer.writerow([level, count, f"{percentage:.1f}%"])
    
    # Industry distribution CSV
    with open(dataset_dir / "industry_distribution_10k.csv", 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['industry', 'count', 'percentage'])
        total = sum(industries.values())
        
        for industry, count in sorted(industries.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total) * 100 if total > 0 else 0
            writer.writerow([industry, count, f"{percentage:.1f}%"])
    
    print("Created CSV artifacts:")
    print(f"  - {dataset_dir}/dataset_summary_10k.csv")
    print(f"  - {dataset_dir}/uncertainty_distribution_10k.csv")
    print(f"  - {dataset_dir}/industry_distribution_10k.csv")

if __name__ == "__main__":
    create_csv_artifacts("dataset_10k")
