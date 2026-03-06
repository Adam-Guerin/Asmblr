#!/usr/bin/env python3
"""
Generate example contexts from each uncertainty level for demonstration.
"""

import json
from pathlib import Path

def generate_examples():
    """Generate example contexts from each uncertainty level."""
    dataset_path = Path("dataset_10k")
    
    # Load contexts and categorize by uncertainty
    contexts = {'low': [], 'medium': [], 'high': []}
    
    for file_path in dataset_path.glob("context_*.json"):
        with open(file_path, 'r', encoding='utf-8') as f:
            context = json.load(f)
            
        # Determine uncertainty level
        if context.get('metadata', {}).get('generated_for_uncertainty'):
            level = context['metadata']['generated_for_uncertainty']
        else:
            # Simple inference for original contexts
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
                level = 'high'
            elif uncertainty_score >= 2:
                level = 'medium'
            else:
                level = 'low'
        
        contexts[level].append(context)
    
    # Create examples file
    examples = {
        "examples_by_uncertainty_level": {},
        "summary": {
            "total_contexts": sum(len(v) for v in contexts.values()),
            "low_uncertainty_count": len(contexts['low']),
            "medium_uncertainty_count": len(contexts['medium']),
            "high_uncertainty_count": len(contexts['high'])
        }
    }
    
    for level in ['low', 'medium', 'high']:
        if contexts[level]:
            # Take first 2 examples from each level
            examples["examples_by_uncertainty_level"][level] = contexts[level][:2]
    
    # Save examples
    with open(dataset_path / "uncertainty_examples.json", 'w') as f:
        json.dump(examples, f, indent=2)
    
    print("Generated uncertainty level examples:")
    for level in ['low', 'medium', 'high']:
        count = len(contexts[level])
        print(f"  {level}: {count} contexts")
    
    print(f"Examples saved to: {dataset_path}/uncertainty_examples.json")
    
    return examples

if __name__ == "__main__":
    generate_examples()
