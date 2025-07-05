"""
Logging utilities for data extraction and graph database operations.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class DataLogger:
    """Enhanced logger for tracking data extraction and graph operations."""
    
    def __init__(self, log_file: Optional[str] = None):
        """
        Initialize data logger.
        
        Args:
            log_file: Optional file path for structured data logs
        """
        self.log_file = log_file
        if log_file:
            # Ensure log directory exists
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    
    def _write_structured_log(self, log_entry: Dict[str, Any]):
        """Write structured log entry to file."""
        if self.log_file:
            try:
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(log_entry, default=str) + '\n')
            except Exception as e:
                logger.error(f"Failed to write structured log: {e}")
    
    def log_document_processing(
        self,
        document_path: str,
        title: str,
        source: str,
        content_length: int,
        metadata: Dict[str, Any]
    ):
        """Log document processing start."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "document_processing_start",
            "document_path": document_path,
            "title": title,
            "source": source,
            "content_length": content_length,
            "metadata": metadata
        }
        
        logger.info(f"📄 Processing document: {title} ({content_length:,} chars)")
        logger.info(f"   Source: {source}")
        logger.info(f"   Metadata: {json.dumps(metadata, indent=2)}")
        
        self._write_structured_log(log_entry)
    
    def log_chunking_results(
        self,
        document_title: str,
        chunk_count: int,
        chunk_sizes: List[int],
        chunking_method: str,
        config: Dict[str, Any]
    ):
        """Log document chunking results."""
        avg_size = sum(chunk_sizes) / len(chunk_sizes) if chunk_sizes else 0
        min_size = min(chunk_sizes) if chunk_sizes else 0
        max_size = max(chunk_sizes) if chunk_sizes else 0
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "chunking_complete",
            "document_title": document_title,
            "chunk_count": chunk_count,
            "chunking_method": chunking_method,
            "chunk_stats": {
                "min_size": min_size,
                "max_size": max_size,
                "avg_size": round(avg_size, 1),
                "total_chars": sum(chunk_sizes)
            },
            "config": config
        }
        
        logger.info(f"✂️  Chunking complete: {chunk_count} chunks created")
        logger.info(f"   Method: {chunking_method}")
        logger.info(f"   Size stats: min={min_size}, max={max_size}, avg={avg_size:.1f}")
        
        self._write_structured_log(log_entry)
    
    def log_entity_extraction_start(
        self,
        document_title: str,
        content_length: int,
        extraction_config: Dict[str, bool]
    ):
        """Log entity extraction start."""
        enabled_types = [k for k, v in extraction_config.items() if v]
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "entity_extraction_start",
            "document_title": document_title,
            "content_length": content_length,
            "enabled_entity_types": enabled_types,
            "extraction_config": extraction_config
        }
        
        logger.info(f"🔍 Starting entity extraction for: {document_title}")
        logger.info(f"   Content length: {content_length:,} chars")
        logger.info(f"   Enabled types: {', '.join(enabled_types)}")
        
        self._write_structured_log(log_entry)
    
    def log_extracted_entities(
        self,
        document_title: str,
        entities: Dict[str, Any],
        extraction_method: str,
        processing_time_ms: Optional[float] = None
    ):
        """Log extracted entities with detailed counts."""
        # Count entities by type
        entity_counts = {}
        total_entities = 0
        
        for entity_type, entity_data in entities.items():
            if isinstance(entity_data, list):
                count = len(entity_data)
                entity_counts[entity_type] = count
                total_entities += count
            elif isinstance(entity_data, dict):
                # Handle nested entity structures
                nested_count = 0
                nested_counts = {}
                for sub_type, sub_data in entity_data.items():
                    if isinstance(sub_data, list):
                        sub_count = len(sub_data)
                        nested_counts[sub_type] = sub_count
                        nested_count += sub_count
                entity_counts[entity_type] = nested_counts
                total_entities += nested_count
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "entity_extraction_complete",
            "document_title": document_title,
            "extraction_method": extraction_method,
            "total_entities": total_entities,
            "entity_counts": entity_counts,
            "entities": entities,
            "processing_time_ms": processing_time_ms
        }
        
        logger.info(f"🎯 Entity extraction complete: {total_entities} entities found")
        logger.info(f"   Method: {extraction_method}")
        if processing_time_ms:
            logger.info(f"   Processing time: {processing_time_ms:.1f}ms")
        
        # Log detailed counts
        for entity_type, count_data in entity_counts.items():
            if isinstance(count_data, dict):
                logger.info(f"   {entity_type}:")
                for sub_type, count in count_data.items():
                    if count > 0:
                        logger.info(f"     {sub_type}: {count}")
            else:
                if count_data > 0:
                    logger.info(f"   {entity_type}: {count_data}")
        
        self._write_structured_log(log_entry)


# Global data logger instance
data_logger = DataLogger(log_file="logs/data_extraction.jsonl")
