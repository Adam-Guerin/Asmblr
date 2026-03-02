"""
Dataset registry and loading utilities.
"""

from pathlib import Path
import logging

from .toy_pains import ToyPainsDataset
from .synthetic_market import SyntheticMarketDataset
from .realistic_corpus import RealisticCorpusDataset

logger = logging.getLogger(__name__)


class DatasetRegistry:
    """Registry for benchmark datasets."""
    
    _datasets: dict[str, type] = {
        "toy_pains_v1": ToyPainsDataset,
        "synthetic_market_v1": SyntheticMarketDataset,
        "realistic_corpus_v1": RealisticCorpusDataset
    }
    
    @classmethod
    def register(cls, name: str, dataset_class: type):
        """Register a new dataset."""
        cls._datasets[name] = dataset_class
        logger.info(f"Registered dataset: {name}")
    
    @classmethod
    def get_dataset_class(cls, name: str) -> type | None:
        """Get dataset class by name."""
        return cls._datasets.get(name)
    
    @classmethod
    def list_datasets(cls) -> list[str]:
        """List all registered datasets."""
        return list(cls._datasets.keys())
    
    @classmethod
    def dataset_info(cls, name: str) -> dict | None:
        """Get information about a dataset."""
        dataset_class = cls.get_dataset_class(name)
        if dataset_class is None:
            return None
        
        return {
            "name": name,
            "class": dataset_class.__name__,
            "description": getattr(dataset_class, "__doc__", ""),
            "has_ground_truth": hasattr(dataset_class, "has_ground_truth"),
            "size": getattr(dataset_class, "size", None)
        }


def load_dataset(name: str, custom_path: str | None = None) -> list[dict] | None:
    """Load a dataset by name."""
    dataset_class = DatasetRegistry.get_dataset_class(name)
    if dataset_class is None:
        logger.error(f"Unknown dataset: {name}")
        return None
    
    try:
        dataset = dataset_class(custom_path)
        return dataset.load()
    except Exception as e:
        logger.error(f"Failed to load dataset {name}: {e}")
        return None


def create_sample_dataset(output_path: str, size: int = 10):
    """Create a small sample dataset for testing."""
    import json
    
    sample_data = []
    
    for i in range(size):
        item = {
            "id": f"sample_{i:03d}",
            "topic": f"Sample topic {i+1}",
            "documents": [
                {
                    "source": "sample_source",
                    "url": f"local://sample_{i:03d}",
                    "text": f"This is sample text document {i+1} describing a problem in the sample domain."
                }
            ],
            "ground_truth": {
                "pains": [
                    {
                        "actor": f"User_{i+1}",
                        "context": f"Context_{i+1}",
                        "problem": f"Problem statement {i+1}",
                        "severity": (i % 5) + 1
                    }
                ],
                "clusters": [
                    {
                        "label": f"Cluster_{i+1}",
                        "pain_ids": [0]
                    }
                ],
                "competitors": [
                    {
                        "name": f"Competitor_{i+1}",
                        "positioning": f"Positioning statement {i+1}",
                        "pricing": f"Pricing model {i+1}"
                    }
                ],
                "best_opportunity": {
                    "title": f"Opportunity {i+1}",
                    "reason": f"Reasoning {i+1}"
                },
                "decision": "PASS" if i % 3 != 0 else ("KILL" if i % 3 == 1 else "ABORT"),
                "confidence": 0.5 + (i % 5) * 0.1
            }
        }
        sample_data.append(item)
    
    # Save sample dataset
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sample_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Created sample dataset with {size} items at {output_path}")
    return sample_data
