"""Streaming data processor for large datasets.

This module provides memory-efficient processing of large datasets
through streaming and chunked operations, reducing memory footprint.
"""

from __future__ import annotations
from typing import Any
from collections.abc import Iterator
import json
import logging
from pathlib import Path


logger = logging.getLogger(__name__)


class StreamingDataProcessor:
    """Memory-efficient processor for large datasets."""
    
    def __init__(self, chunk_size: int = 1000, max_memory_mb: int = 100):
        """Initialize streaming processor.
        
        Args:
            chunk_size: Number of items to process at once
            max_memory_mb: Maximum memory usage in MB
        """
        self.chunk_size = chunk_size
        self.max_memory_mb = max_memory_mb
    
    def _estimate_memory_usage(self, items: list[Any]) -> float:
        """Estimate memory usage for a list of items."""
        if not items:
            return 0.0
        
        # Rough estimation: each item ~100 bytes + overhead
        total_bytes = sum(len(str(item)) * 100 for item in items)
        return total_bytes / (1024 * 1024)  # Convert to MB
    
    def _should_stream(self, items: list[Any]) -> bool:
        """Determine if dataset should be streamed."""
        estimated_mb = self._estimate_memory_usage(items)
        return estimated_mb > self.max_memory_mb
    
    def _process_chunk(self, chunk: list[Any]) -> list[Any]:
        """Process a chunk of items."""
        return chunk  # Override in subclasses
    
    def _stream_json_file(self, file_path: Path, processor_func) -> Iterator[dict[str, Any]]:
        """Stream JSON file line by line."""
        with open(file_path, encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    item = json.loads(line.strip())
                    yield processor_func(item, line_num, line)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON line {line_num}: {e}")
                    continue
    
    def _stream_feedback_records(self, file_path: Path) -> Iterator[dict[str, Any]]:
        """Stream feedback records with memory efficiency."""
        processed_count = 0
        
        for item in self._stream_json_file(file_path, self._process_feedback_record):
            processed_count += 1
            yield item
            
            # Log progress every 1000 records
            if processed_count % 1000 == 0:
                logger.info(f"Processed {processed_count} feedback records")
    
    def _process_feedback_record(self, record: dict[str, Any], line_num: int, line: str) -> dict[str, Any]:
        """Process individual feedback record."""
        # Basic validation
        if not isinstance(record, dict):
            return {"error": "Invalid record format", "line": line_num, "data": str(record)}
        
        # Sanitize sensitive data
        sanitized = {
            key: self._sanitize_text(record.get("key", "")),
            "topic": self._sanitize_text(record.get("topic", "")),
            "feedback": self._sanitize_text(record.get("feedback", "")),
            "score": record.get("score", 0),
            "timestamp": record.get("timestamp", ""),
        }
        
        return sanitized
    
    def _sanitize_text(self, text: str) -> str:
        """Sanitize text for memory efficiency."""
        if not text:
            return text
        
        # Truncate very long texts
        if len(text) > 1000:
            return text[:1000] + "..."
        
        return text
    
    def process_feedback_file(self, file_path: Path) -> dict[str, Any]:
        """Process entire feedback file with streaming."""
        total_records = 0
        valid_records = []
        
        for record in self._stream_feedback_records(file_path, self._process_feedback_record):
            total_records += 1
            
            # Only keep valid records
            if "error" not in record:
                valid_records.append(record)
        
        return {
            "total_records": total_records,
            "valid_records": len(valid_records),
            "processing_method": "streaming" if total_records > 10000 else "standard"
        }


class HistoricalLearningProcessor:
    """Memory-efficient processor for historical learning data."""
    
    def __init__(self, max_runs: int = 200, max_memory_mb: int = 100):
        """Initialize historical learning processor."""
        self.max_runs = max_runs
        self.max_memory_mb = max_memory_mb
    
    def _should_stream_runs(self, run_count: int) -> bool:
        """Determine if runs should be streamed."""
        return run_count > self.max_runs
    
    def _process_run_chunk(self, chunk: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Process a chunk of historical runs."""
        processed_runs = []
        
        for run in chunk:
            # Basic validation and sanitization
            if isinstance(run, dict):
                sanitized_run = {
                    "id": self._sanitize_text(run.get("id", "")),
                    "status": self._sanitize_text(run.get("status", "")),
                    "topic": self._sanitize_text(run.get("topic", "")),
                }
                processed_runs.append(sanitized_run)
        
        return processed_runs
    
    def process_historical_runs(self, file_path: Path) -> dict[str, Any]:
        """Process historical runs file with streaming."""
        total_runs = 0
        valid_runs = []
        
        for run_chunk in self._stream_json_file(file_path, self._process_run_chunk):
            total_runs += len(run_chunk)
            
            # Only keep valid runs
            valid_runs.extend([run for run in run_chunk if run.get("status") in {"completed", "aborted", "killed", "failed"}])
        
        return {
            "total_runs": total_runs,
            "valid_runs": len(valid_runs),
            "processing_method": "streaming" if total_runs > self.max_runs else "standard"
        }


def create_streaming_processor(chunk_size: int = 1000, max_memory_mb: int = 100) -> StreamingDataProcessor:
    """Create a streaming data processor."""
    return StreamingDataProcessor(chunk_size, max_memory_mb)


def process_large_feedback_file(file_path: Path) -> dict[str, Any]:
    """Process large feedback file using streaming."""
    processor = create_streaming_processor()
    return processor.process_feedback_file(file_path)


def process_large_historical_runs(file_path: Path) -> dict[str, Any]:
    """Process large historical runs file using streaming."""
    processor = create_streaming_processor()
    return processor.process_historical_runs(file_path)
