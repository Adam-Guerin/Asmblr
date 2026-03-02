"""
Utility functions for benchmark operations.
"""

import json
import random
import numpy as np
from pathlib import Path
from typing import Any
import logging

logger = logging.getLogger(__name__)


def set_seed(seed: int):
    """Set random seed for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    logger.info(f"Set random seed to {seed}")


def load_json(file_path: str | Path) -> dict[str, Any] | None:
    """Load JSON file safely."""
    try:
        path = Path(file_path)
        if not path.exists():
            logger.warning(f"File not found: {path}")
            return None
        
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading JSON from {file_path}: {e}")
        return None


def save_json(data: Any, file_path: str | Path, indent: int = 2):
    """Save data to JSON file."""
    try:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False, default=str)
        
        logger.debug(f"Saved JSON to {path}")
    except Exception as e:
        logger.error(f"Error saving JSON to {file_path}: {e}")


def load_jsonl(file_path: str | Path) -> list[dict[str, Any]]:
    """Load JSONL file."""
    try:
        path = Path(file_path)
        if not path.exists():
            logger.warning(f"File not found: {path}")
            return []
        
        data = []
        with open(path, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    data.append(json.loads(line))
        
        logger.debug(f"Loaded {len(data)} records from {path}")
        return data
    except Exception as e:
        logger.error(f"Error loading JSONL from {file_path}: {e}")
        return []


def save_jsonl(data: list[dict[str, Any]], file_path: str | Path):
    """Save data to JSONL file."""
    try:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False, default=str) + '\n')
        
        logger.debug(f"Saved {len(data)} records to {path}")
    except Exception as e:
        logger.error(f"Error saving JSONL to {file_path}: {e}")


def fuzzy_match(str1: str, str2: str, threshold: float = 0.8) -> bool:
    """Simple fuzzy string matching."""
    if not str1 or not str2:
        return False
    
    # Convert to lowercase and split into words
    words1 = set(str1.lower().split())
    words2 = set(str2.lower().split())
    
    # Calculate Jaccard similarity
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    if not union:
        return False
    
    similarity = len(intersection) / len(union)
    return similarity >= threshold


def extract_text_content(file_path: str | Path) -> str | None:
    """Extract text content from various file types."""
    path = Path(file_path)
    
    if not path.exists():
        return None
    
    try:
        if path.suffix.lower() in ['.txt', '.md']:
            with open(path, encoding='utf-8') as f:
                return f.read()
        elif path.suffix.lower() == '.json':
            with open(path, encoding='utf-8') as f:
                data = json.load(f)
                # Extract text from common JSON structures
                if isinstance(data, dict):
                    return json.dumps(data, indent=2)
                elif isinstance(data, list):
                    return '\n'.join(str(item) for item in data)
                else:
                    return str(data)
        else:
            logger.warning(f"Unsupported file type: {path.suffix}")
            return None
    except Exception as e:
        logger.error(f"Error extracting text from {file_path}: {e}")
        return None


def calculate_bootstrap_confidence_interval(
    values: list[float], 
    confidence_level: float = 0.95,
    n_samples: int = 1000
) -> tuple:
    """Calculate bootstrap confidence interval."""
    if not values:
        return (0.0, 0.0)
    
    values = np.array(values)
    n = len(values)
    
    # Bootstrap resampling
    bootstrap_means = []
    for _ in range(n_samples):
        bootstrap_sample = np.random.choice(values, size=n, replace=True)
        bootstrap_means.append(np.mean(bootstrap_sample))
    
    bootstrap_means = np.array(bootstrap_means)
    
    # Calculate percentiles
    alpha = 1 - confidence_level
    lower_percentile = (alpha / 2) * 100
    upper_percentile = (1 - alpha / 2) * 100
    
    ci_lower = np.percentile(bootstrap_means, lower_percentile)
    ci_upper = np.percentile(bootstrap_means, upper_percentile)
    
    return (float(ci_lower), float(ci_upper))


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safe division with default value for division by zero."""
    if denominator == 0:
        return default
    return numerator / denominator


def normalize_score(score: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Normalize score to [0, 1] range."""
    if max_val <= min_val:
        return 0.0
    
    normalized = (score - min_val) / (max_val - min_val)
    return max(0.0, min(1.0, normalized))


def create_directory_structure(base_path: str | Path, subdirs: list[str]):
    """Create directory structure."""
    base_path = Path(base_path)
    base_path.mkdir(parents=True, exist_ok=True)
    
    for subdir in subdirs:
        (base_path / subdir).mkdir(parents=True, exist_ok=True)


def get_file_size(file_path: str | Path) -> int:
    """Get file size in bytes."""
    try:
        return Path(file_path).stat().st_size
    except:
        return 0


def copy_file_with_metadata(src: str | Path, dst: str | Path):
    """Copy file while preserving metadata."""
    import shutil
    try:
        shutil.copy2(src, dst)
        logger.debug(f"Copied {src} to {dst}")
    except Exception as e:
        logger.error(f"Error copying file {src} to {dst}: {e}")


def merge_dicts(*dicts: dict[str, Any]) -> dict[str, Any]:
    """Merge multiple dictionaries."""
    result = {}
    for d in dicts:
        if d:
            result.update(d)
    return result


def flatten_dict(d: dict[str, Any], parent_key: str = '', sep: str = '.') -> dict[str, Any]:
    """Flatten nested dictionary."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def unflatten_dict(d: dict[str, Any], sep: str = '.') -> dict[str, Any]:
    """Unflatten dictionary."""
    result = {}
    for key, value in d.items():
        parts = key.split(sep)
        d = result
        for part in parts[:-1]:
            if part not in d:
                d[part] = {}
            d = d[part]
        d[parts[-1]] = value
    return result
