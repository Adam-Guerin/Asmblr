"""
DNA-based Storage Systems for Asmblr
Biological data storage using synthetic DNA sequences
"""

import asyncio
import logging
from datetime import datetime
from typing import Any
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import numpy as np
import hashlib
import zlib

logger = logging.getLogger(__name__)

class EncodingScheme(Enum):
    """DNA encoding schemes"""
    DNA_BASE64 = "dna_base64"
    QUATERNARY = "quaternary"
    HEDGES = "hedges"
    GOLDMAN = "goldman"
    BINARY_TO_DNA = "binary_to_dna"
    FIBONACCI = "fibonacci"
    PRIMES = "primes"

class StorageType(Enum):
    """DNA storage types"""
    SYNTHETIC_DNA = "synthetic_dna"
    PLASMID_DNA = "plasmid_dna"
    CHROMOSOMAL_DNA = "chromosomal_dna"
    CRISPR_DNA = "crispr_dna"
    PEPTIDE_DNA = "peptide_dna"
    RIBOZYME_DNA = "ribozyme_dna"

class CompressionType(Enum):
    """Compression types for DNA storage"""
    NONE = "none"
    ZLIB = "zlib"
    GZIP = "gzip"
    LZMA = "lzma"
    DNA_SPECIFIC = "dna_specific"

class ErrorCorrection(Enum):
    """Error correction schemes"""
    REED_SOLOMON = "reed_solomon"
    HAMMING = "hamming"
    BCH = "bch"
    LDPC = "ldpc"
    CONVOLUTIONAL = "convolutional"
    DNA_SPECIFIC = "dna_specific"

@dataclass
class DNASequence:
    """DNA sequence for storage"""
    id: str
    sequence: str
    length: int
    gc_content: float
    melting_temperature: float
    secondary_structure: str
    error_correction: str
    metadata: dict[str, Any]
    created_at: datetime
    expires_at: datetime | None

@dataclass
class StorageBlock:
    """DNA storage block"""
    id: str
    name: str
    data: bytes
    encoding_scheme: EncodingScheme
    compression_type: CompressionType
    error_correction: ErrorCorrection
    dna_sequences: list[DNASequence]
    redundancy_factor: int
    checksum: str
    created_at: datetime
    accessed_at: datetime
    access_count: int

@dataclass
class StorageMetrics:
    """DNA storage metrics"""
    total_sequences: int
    total_data_size: int
    compression_ratio: float
    error_rate: float
    retrieval_time: float
    storage_density: float  # bits per nucleotide
    stability_score: float
    cost_per_mb: float

class DNAEncoder:
    """DNA encoding and decoding"""
    
    def __init__(self, encoding_scheme: EncodingScheme):
        self.encoding_scheme = encoding_scheme
        self.dna_map = self._initialize_dna_map()
        
    def _initialize_dna_map(self) -> dict[str, str]:
        """Initialize DNA mapping based on encoding scheme"""
        if self.encoding_scheme == EncodingScheme.DNA_BASE64 or self.encoding_scheme == EncodingScheme.QUATERNARY:
            return {
                'A': '00', 'C': '01', 'G': '10', 'T': '11'
            }
        elif self.encoding_scheme == EncodingScheme.HEDGES:
            return {
                'AA': '00', 'AC': '01', 'AG': '10', 'AT': '11',
                'CA': '20', 'CC': '21', 'CG': '22', 'CT': '23',
                'GA': '30', 'GC': '31', 'GG': '32', 'GT': '33',
                'TA': '40', 'TC': '41', 'TG': '42', 'TT': '43'
            }
        elif self.encoding_scheme == EncodingScheme.GOLDMAN:
            return {
                'AAA': '000', 'AAC': '001', 'AAG': '010', 'AAT': '011',
                'ACA': '100', 'ACC': '101', 'ACG': '110', 'ACT': '111',
                'AGA': '0000', 'AGC': '0001', 'AGG': '0010', 'AGT': '0011',
                'ATA': '0100', 'ATC': '0101', 'ATG': '0110', 'ATT': '0111',
                # ... (simplified for brevity)
            }
        else:
            return {'A': '00', 'C': '01', 'G': '10', 'T': '11'}
    
    def encode_to_dna(self, data: bytes) -> str:
        """Encode binary data to DNA sequence"""
        try:
            # Convert bytes to binary string
            binary_data = ''.join(format(byte, '08b') for byte in data)
            
            if self.encoding_scheme == EncodingScheme.DNA_BASE64:
                return self._encode_dna_base64(binary_data)
            elif self.encoding_scheme == EncodingScheme.QUATERNARY:
                return self._encode_quaternary(binary_data)
            elif self.encoding_scheme == EncodingScheme.HEDGES:
                return self._encode_hedges(binary_data)
            elif self.encoding_scheme == EncodingScheme.GOLDMAN:
                return self._encode_goldman(binary_data)
            else:
                return self._encode_dna_base64(binary_data)
                
        except Exception as e:
            logger.error(f"Error encoding to DNA: {e}")
            raise
    
    def _encode_dna_base64(self, binary_data: str) -> str:
        """Encode using DNA Base64 scheme"""
        try:
            # Pad binary data to multiple of 2
            if len(binary_data) % 2 != 0:
                binary_data += '0'
            
            dna_sequence = []
            for i in range(0, len(binary_data), 2):
                bits = binary_data[i:i+2]
                
                if bits == '00':
                    dna_sequence.append('A')
                elif bits == '01':
                    dna_sequence.append('C')
                elif bits == '10':
                    dna_sequence.append('G')
                elif bits == '11':
                    dna_sequence.append('T')
                else:
                    # Invalid bits, default to A
                    dna_sequence.append('A')
            
            return ''.join(dna_sequence)
            
        except Exception as e:
            logger.error(f"Error in DNA Base64 encoding: {e}")
            raise
    
    def _encode_quaternary(self, binary_data: str) -> str:
        """Encode using quaternary scheme"""
        try:
            # Pad binary data to multiple of 2
            if len(binary_data) % 2 != 0:
                binary_data += '0'
            
            dna_sequence = []
            for i in range(0, len(binary_data), 2):
                bits = binary_data[i:i+2]
                
                if bits == '00':
                    dna_sequence.append('A')
                elif bits == '01':
                    dna_sequence.append('C')
                elif bits == '10':
                    dna_sequence.append('G')
                elif bits == '11':
                    dna_sequence.append('T')
                else:
                    dna_sequence.append('A')
            
            return ''.join(dna_sequence)
            
        except Exception as e:
            logger.error(f"Error in quaternary encoding: {e}")
            raise
    
    def _encode_hedges(self, binary_data: str) -> str:
        """Encode using Hedges scheme"""
        try:
            # Pad binary data to multiple of 4
            if len(binary_data) % 4 != 0:
                binary_data += '0' * (4 - len(binary_data) % 4)
            
            dna_sequence = []
            for i in range(0, len(binary_data), 4):
                bits = binary_data[i:i+4]
                
                # Map 4 bits to 2 nucleotides
                if bits == '0000':
                    dna_sequence.append('AA')
                elif bits == '0001':
                    dna_sequence.append('AC')
                elif bits == '0010':
                    dna_sequence.append('AG')
                elif bits == '0011':
                    dna_sequence.append('AT')
                elif bits == '0100':
                    dna_sequence.append('CA')
                elif bits == '0101':
                    dna_sequence.append('CC')
                elif bits == '0110':
                    dna_sequence.append('CG')
                elif bits == '0111':
                    dna_sequence.append('CT')
                elif bits == '1000':
                    dna_sequence.append('GA')
                elif bits == '1001':
                    dna_sequence.append('GC')
                elif bits == '1010':
                    dna_sequence.append('GG')
                elif bits == '1011':
                    dna_sequence.append('GT')
                elif bits == '1100':
                    dna_sequence.append('TA')
                elif bits == '1101':
                    dna_sequence.append('TC')
                elif bits == '1110':
                    dna_sequence.append('TG')
                elif bits == '1111':
                    dna_sequence.append('TT')
                else:
                    dna_sequence.append('AA')
            
            return ''.join(dna_sequence)
            
        except Exception as e:
            logger.error(f"Error in Hedges encoding: {e}")
            raise
    
    def _encode_goldman(self, binary_data: str) -> str:
        """Encode using Goldman scheme"""
        try:
            # Simplified Goldman encoding
            # In practice, would use more complex mapping
            return self._encode_dna_base64(binary_data)
            
        except Exception as e:
            logger.error(f"Error in Goldman encoding: {e}")
            raise
    
    def decode_from_dna(self, dna_sequence: str) -> bytes:
        """Decode DNA sequence to binary data"""
        try:
            if self.encoding_scheme == EncodingScheme.DNA_BASE64:
                binary_data = self._decode_dna_base64(dna_sequence)
            elif self.encoding_scheme == EncodingScheme.QUATERNARY:
                binary_data = self._decode_quaternary(dna_sequence)
            elif self.encoding_scheme == EncodingScheme.HEDGES:
                binary_data = self._decode_hedges(dna_sequence)
            elif self.encoding_scheme == EncodingScheme.GOLDMAN:
                binary_data = self._decode_goldman(dna_sequence)
            else:
                binary_data = self._decode_dna_base64(dna_sequence)
            
            # Convert binary string to bytes
            byte_array = []
            for i in range(0, len(binary_data), 8):
                byte_bits = binary_data[i:i+8]
                if len(byte_bits) == 8:
                    byte_array.append(int(byte_bits, 2))
            
            return bytes(byte_array)
            
        except Exception as e:
            logger.error(f"Error decoding from DNA: {e}")
            raise
    
    def _decode_dna_base64(self, dna_sequence: str) -> str:
        """Decode from DNA Base64 scheme"""
        try:
            binary_data = []
            
            for nucleotide in dna_sequence:
                if nucleotide == 'A':
                    binary_data.append('00')
                elif nucleotide == 'C':
                    binary_data.append('01')
                elif nucleotide == 'G':
                    binary_data.append('10')
                elif nucleotide == 'T':
                    binary_data.append('11')
                else:
                    binary_data.append('00')
            
            return ''.join(binary_data)
            
        except Exception as e:
            logger.error(f"Error in DNA Base64 decoding: {e}")
            raise
    
    def _decode_quaternary(self, dna_sequence: str) -> str:
        """Decode from quaternary scheme"""
        try:
            binary_data = []
            
            for nucleotide in dna_sequence:
                if nucleotide == 'A':
                    binary_data.append('00')
                elif nucleotide == 'C':
                    binary_data.append('01')
                elif nucleotide == 'G':
                    binary_data.append('10')
                elif nucleotide == 'T':
                    binary_data.append('11')
                else:
                    binary_data.append('00')
            
            return ''.join(binary_data)
            
        except Exception as e:
            logger.error(f"Error in quaternary decoding: {e}")
            raise
    
    def _decode_hedges(self, dna_sequence: str) -> str:
        """Decode from Hedges scheme"""
        try:
            binary_data = []
            
            # Process 2 nucleotides at a time
            for i in range(0, len(dna_sequence), 2):
                if i + 1 < len(dna_sequence):
                    dinucleotide = dna_sequence[i:i+2]
                    
                    if dinucleotide == 'AA':
                        binary_data.append('0000')
                    elif dinucleotide == 'AC':
                        binary_data.append('0001')
                    elif dinucleotide == 'AG':
                        binary_data.append('0010')
                    elif dinucleotide == 'AT':
                        binary_data.append('0011')
                    elif dinucleotide == 'CA':
                        binary_data.append('0100')
                    elif dinucleotide == 'CC':
                        binary_data.append('0101')
                    elif dinucleotide == 'CG':
                        binary_data.append('0110')
                    elif dinucleotide == 'CT':
                        binary_data.append('0111')
                    elif dinucleotide == 'GA':
                        binary_data.append('1000')
                    elif dinucleotide == 'GC':
                        binary_data.append('1001')
                    elif dinucleotide == 'GG':
                        binary_data.append('1010')
                    elif dinucleotide == 'GT':
                        binary_data.append('1011')
                    elif dinucleotide == 'TA':
                        binary_data.append('1100')
                    elif dinucleotide == 'TC':
                        binary_data.append('1101')
                    elif dinucleotide == 'TG':
                        binary_data.append('1110')
                    elif dinucleotide == 'TT':
                        binary_data.append('1111')
                    else:
                        binary_data.append('0000')
            
            return ''.join(binary_data)
            
        except Exception as e:
            logger.error(f"Error in Hedges decoding: {e}")
            raise
    
    def _decode_goldman(self, dna_sequence: str) -> str:
        """Decode from Goldman scheme"""
        try:
            # Simplified Goldman decoding
            return self._decode_dna_base64(dna_sequence)
            
        except Exception as e:
            logger.error(f"Error in Goldman decoding: {e}")
            raise

class DNAStorageManager:
    """DNA-based storage management system"""
    
    def __init__(self):
        self.storage_blocks: dict[str, StorageBlock] = {}
        self.dna_sequences: dict[str, DNASequence] = {}
        self.encoding_schemes = {
            EncodingScheme.DNA_BASE64: DNAEncoder(EncodingScheme.DNA_BASE64),
            EncodingScheme.QUATERNARY: DNAEncoder(EncodingScheme.QUATERNARY),
            EncodingScheme.HEDGES: DNAEncoder(EncodingScheme.HEDGES),
            EncodingScheme.GOLDMAN: DNAEncoder(EncodingScheme.GOLDMAN)
        }
        
        # Initialize storage metrics
        self.metrics = StorageMetrics(
            total_sequences=0,
            total_data_size=0,
            compression_ratio=1.0,
            error_rate=0.0,
            retrieval_time=0.0,
            storage_density=1.75,  # ~1.75 bits per nucleotide
            stability_score=0.95,
            cost_per_mb=1000.0  # $1000 per MB
        )
        
        # Start background tasks
        asyncio.create_task(self._stability_monitoring())
        asyncio.create_task(self._error_correction_monitoring())
    
    async def store_data(self, data: bytes, name: str, 
                         encoding_scheme: EncodingScheme = EncodingScheme.DNA_BASE64,
                         compression_type: CompressionType = CompressionType.ZLIB,
                         error_correction: ErrorCorrection = ErrorCorrection.REED_SOLOMON,
                         redundancy_factor: int = 3) -> StorageBlock:
        """Store data in DNA"""
        try:
            # Compress data if requested
            if compression_type == CompressionType.ZLIB:
                compressed_data = zlib.compress(data)
            elif compression_type == CompressionType.GZIP or compression_type == CompressionType.LZMA:
                compressed_data = zlib.compress(data)  # Simplified
            else:
                compressed_data = data
            
            # Calculate compression ratio
            compression_ratio = len(data) / len(compressed_data) if len(compressed_data) > 0 else 1.0
            
            # Encode to DNA
            encoder = self.encoding_schemes[encoding_scheme]
            dna_sequence = encoder.encode_to_dna(compressed_data)
            
            # Split into multiple sequences for redundancy
            sequence_length = 200  # nucleotides per sequence
            sequences = []
            
            for i in range(0, len(dna_sequence), sequence_length):
                seq_segment = dna_sequence[i:i+sequence_length]
                if len(seq_segment) < sequence_length:
                    seq_segment += 'A' * (sequence_length - len(seq_segment))
                
                # Create DNA sequence object
                dna_seq = DNASequence(
                    id=str(uuid.uuid4()),
                    sequence=seq_segment,
                    length=len(seq_segment),
                    gc_content=self._calculate_gc_content(seq_segment),
                    melting_temperature=self._calculate_melting_temperature(seq_segment),
                    secondary_structure=self._predict_secondary_structure(seq_segment),
                    error_correction=error_correction.value,
                    metadata={
                        "encoding_scheme": encoding_scheme.value,
                        "compression_type": compression_type.value,
                        "original_size": len(data),
                        "compressed_size": len(compressed_data)
                    },
                    created_at=datetime.now(),
                    expires_at=None
                )
                
                sequences.append(dna_seq)
                self.dna_sequences[dna_seq.id] = dna_seq
            
            # Create storage block
            block = StorageBlock(
                id=str(uuid.uuid4()),
                name=name,
                data=data,
                encoding_scheme=encoding_scheme,
                compression_type=compression_type,
                error_correction=error_correction,
                dna_sequences=sequences,
                redundancy_factor=redundancy_factor,
                checksum=hashlib.sha256(data).hexdigest(),
                created_at=datetime.now(),
                accessed_at=datetime.now(),
                access_count=0
            )
            
            self.storage_blocks[block.id] = block
            
            # Update metrics
            self._update_metrics(block, compression_ratio)
            
            logger.info(f"Stored data in DNA: {name}, {len(data)} bytes")
            return block
            
        except Exception as e:
            logger.error(f"Error storing data in DNA: {e}")
            raise
    
    async def retrieve_data(self, block_id: str) -> bytes:
        """Retrieve data from DNA storage"""
        try:
            block = self.storage_blocks.get(block_id)
            if not block:
                raise ValueError(f"Storage block {block_id} not found")
            
            # Update access metrics
            block.accessed_at = datetime.now()
            block.access_count += 1
            
            # Retrieve and decode sequences
            decoded_data = None
            successful_decodings = 0
            
            for dna_seq in block.dna_sequences:
                try:
                    # Decode DNA sequence
                    encoder = self.encoding_schemes[block.encoding_scheme]
                    decoded_segment = encoder.decode_from_dna(dna_seq.sequence)
                    
                    if decoded_data is None:
                        continue
                    
                    if decoded_data is None:
                        continue
                    
                    if successful_decodings == 0:
                        decoded_data = decoded_segment
                    else:
                        # Verify data integrity
                        if decoded_segment == decoded_data:
                            successful_decodings += 1
                        else:
                            continue
                    
                except Exception as e:
                    logger.error(f"Error decoding DNA sequence {dna_seq.id}: {e}")
                    continue
            
            if decoded_data is None:
                raise ValueError("Failed to decode any DNA sequences")
            
            # Decompress if needed
            if block.compression_type == CompressionType.ZLIB or block.compression_type == CompressionType.GZIP or block.compression_type == CompressionType.LZMA:
                retrieved_data = zlib.decompress(decoded_data)
            else:
                retrieved_data = decoded_data
            
            # Verify checksum
            calculated_checksum = hashlib.sha256(retrieved_data).hexdigest()
            if calculated_checksum != block.checksum:
                raise ValueError("Data integrity check failed")
            
            logger.info(f"Retrieved data from DNA: {block.name}")
            return retrieved_data
            
        except Exception as e:
            logger.error(f"Error retrieving data from DNA: {e}")
            raise
    
    def _calculate_gc_content(self, sequence: str) -> float:
        """Calculate GC content of DNA sequence"""
        try:
            gc_count = sequence.count('G') + sequence.count('C')
            total_count = len(sequence)
            return (gc_count / total_count) * 100 if total_count > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating GC content: {e}")
            return 50.0
    
    def _calculate_melting_temperature(self, sequence: str) -> float:
        """Calculate melting temperature of DNA sequence"""
        try:
            # Simplified melting temperature calculation
            # Tm = 64.9 + 41*(GC-16.4)/length
            gc_content = self._calculate_gc_content(sequence)
            length = len(sequence)
            
            if length == 0:
                return 50.0
            
            tm = 64.9 + 41 * (gc_content - 16.4) / length
            return tm
            
        except Exception as e:
            logger.error(f"Error calculating melting temperature: {e}")
            return 50.0
    
    def _predict_secondary_structure(self, sequence: str) -> str:
        """Predict secondary structure of DNA sequence"""
        try:
            # Simplified secondary structure prediction
            # In practice, would use more sophisticated algorithms
            
            gc_content = self._calculate_gc_content(sequence)
            
            if gc_content > 60:
                return "high_gc_stable"
            elif gc_content > 40:
                return "moderate_gc"
            else:
                return "low_gc_unstable"
                
        except Exception as e:
            logger.error(f"Error predicting secondary structure: {e}")
            return "unknown"
    
    def _update_metrics(self, block: StorageBlock, compression_ratio: float):
        """Update storage metrics"""
        try:
            self.metrics.total_sequences += len(block.dna_sequences)
            self.metrics.total_data_size += len(block.data)
            self.metrics.compression_ratio = (self.metrics.compression_ratio + compression_ratio) / 2
            
            # Update storage density
            total_nucleotides = sum(len(seq.sequence) for seq in block.dna_sequences)
            if total_nucleotides > 0:
                bits_stored = len(block.data) * 8
                self.metrics.storage_density = bits_stored / total_nucleotides
            
        except Exception as e:
            logger.error(f"Error updating metrics: {e}")
    
    async def _stability_monitoring(self):
        """Background stability monitoring"""
        while True:
            try:
                current_time = datetime.now()
                
                # Check for expired sequences
                expired_sequences = []
                for seq_id, dna_seq in self.dna_sequences.items():
                    if dna_seq.expires_at and current_time > dna_seq.expires_at:
                        expired_sequences.append(seq_id)
                
                # Remove expired sequences
                for seq_id in expired_sequences:
                    del self.dna_sequences[seq_id]
                    logger.info(f"Removed expired DNA sequence: {seq_id}")
                
                # Update stability score based on degradation
                # In practice, would use actual degradation models
                self.metrics.stability_score *= 0.999  # Gradual degradation
                
                # Wait before next monitoring
                await asyncio.sleep(3600)  # Check every hour
                
            except Exception as e:
                logger.error(f"Error in stability monitoring: {e}")
                await asyncio.sleep(300)
    
    async def _error_correction_monitoring(self):
        """Background error correction monitoring"""
        while True:
            try:
                # Simulate error detection and correction
                total_sequences = len(self.dna_sequences)
                detected_errors = 0
                
                for dna_seq in self.dna_sequences.values():
                    # Simulate error detection
                    if np.random.random() < 0.001:  # 0.1% error rate
                        detected_errors += 1
                
                # Update error rate
                if total_sequences > 0:
                    self.metrics.error_rate = detected_errors / total_sequences
                
                # Wait before next monitoring
                await asyncio.sleep(1800)  # Check every 30 minutes
                
            except Exception as e:
                logger.error(f"Error in error correction monitoring: {e}")
                await asyncio.sleep(300)
    
    def get_storage_info(self, block_id: str) -> dict[str, Any]:
        """Get storage block information"""
        try:
            block = self.storage_blocks.get(block_id)
            if not block:
                return {"error": "Storage block not found"}
            
            return {
                "id": block.id,
                "name": block.name,
                "encoding_scheme": block.encoding_scheme.value,
                "compression_type": block.compression_type.value,
                "error_correction": block.error_correction.value,
                "data_size": len(block.data),
                "compressed_size": sum(len(seq.sequence) for seq in block.dna_sequences) * 2,
                "redundancy_factor": block.redundancy_factor,
                "num_sequences": len(block.dna_sequences),
                "created_at": block.created_at.isoformat(),
                "accessed_at": block.accessed_at.isoformat(),
                "access_count": block.access_count
            }
            
        except Exception as e:
            logger.error(f"Error getting storage info: {e}")
            return {"error": str(e)}
    
    def list_storage_blocks(self) -> list[dict[str, Any]]:
        """List all storage blocks"""
        try:
            blocks = []
            
            for block in self.storage_blocks.values():
                blocks.append({
                    "id": block.id,
                    "name": block.name,
                    "encoding_scheme": block.encoding_scheme.value,
                    "data_size": len(block.data),
                    "num_sequences": len(block.dna_sequences),
                    "created_at": block.created_at.isoformat(),
                    "access_count": block.access_count
                })
            
            return blocks
            
        except Exception as e:
            logger.error(f"Error listing storage blocks: {e}")
            return []
    
    def get_dna_sequence_info(self, sequence_id: str) -> dict[str, Any]:
        """Get DNA sequence information"""
        try:
            dna_seq = self.dna_sequences.get(sequence_id)
            if not dna_seq:
                return {"error": "DNA sequence not found"}
            
            return {
                "id": dna_seq.id,
                "sequence": dna_seq.sequence,
                "length": dna_seq.length,
                "gc_content": dna_seq.gc_content,
                "melting_temperature": dna_seq.melting_temperature,
                "secondary_structure": dna_seq.secondary_structure,
                "error_correction": dna_seq.error_correction,
                "created_at": dna_seq.created_at.isoformat(),
                "expires_at": dna_seq.expires_at.isoformat() if dna_seq.expires_at else None,
                "metadata": dna_seq.metadata
            }
            
        except Exception as e:
            logger.error(f"Error getting DNA sequence info: {e}")
            return {"error": str(e)}
    
    def calculate_storage_cost(self, data_size: int, encoding_scheme: EncodingScheme,
                              redundancy_factor: int = 3) -> dict[str, Any]:
        """Calculate storage cost"""
        try:
            # Estimate DNA synthesis cost
            cost_per_nucleotide = 0.10  # $0.10 per nucleotide
            
            # Estimate sequence length based on encoding scheme
            if encoding_scheme == EncodingScheme.DNA_BASE64 or encoding_scheme == EncodingScheme.QUATERNARY:
                nucleotides_per_byte = 4
            elif encoding_scheme == EncodingScheme.HEDGES:
                nucleotides_per_byte = 2
            else:
                nucleotides_per_byte = 4
            
            total_nucleotides = data_size * nucleotides_per_byte * redundancy_factor
            synthesis_cost = total_nucleotides * cost_per_nucleotide
            
            # Add storage and handling costs
            storage_cost = synthesis_cost * 0.5  # 50% of synthesis cost
            handling_cost = synthesis_cost * 0.2  # 20% of synthesis cost
            
            total_cost = synthesis_cost + storage_cost + handling_cost
            
            return {
                "data_size": data_size,
                "encoding_scheme": encoding_scheme.value,
                "redundancy_factor": redundancy_factor,
                "nucleotides_per_byte": nucleotides_per_byte,
                "total_nucleotides": total_nucleotides,
                "synthesis_cost": synthesis_cost,
                "storage_cost": storage_cost,
                "handling_cost": handling_cost,
                "total_cost": total_cost,
                "cost_per_mb": total_cost / (data_size / (1024 * 1024))
            }
            
        except Exception as e:
            logger.error(f"Error calculating storage cost: {e}")
            return {"error": str(e)}
    
    def get_storage_metrics(self) -> StorageMetrics:
        """Get storage metrics"""
        return self.metrics

# Global DNA storage manager
dna_storage_manager = DNAStorageManager()

# API endpoints
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/dna_storage", tags=["dna_storage"])

class StorageRequest(BaseModel):
    name: str
    encoding_scheme: str = "dna_base64"
    compression_type: str = "zlib"
    error_correction: str = "reed_solomon"
    redundancy_factor: int = 3

class CostCalculationRequest(BaseModel):
    data_size: int
    encoding_scheme: str = "dna_base64"
    redundancy_factor: int = 3

@router.post("/store")
async def store_data(request: StorageRequest):
    """Store data in DNA"""
    try:
        # Get data from request (simplified - in real implementation would come from file upload)
        data = b"Sample data for DNA storage"  # Placeholder
        
        encoding_scheme = EncodingScheme(request.encoding_scheme)
        compression_type = CompressionType(request.compression_type)
        error_correction = ErrorCorrection(request.error_correction)
        
        block = await dna_storage_manager.store_data(
            data, request.name, encoding_scheme, compression_type, 
            error_correction, request.redundancy_factor
        )
        
        return {
            "block_id": block.id,
            "name": block.name,
            "encoding_scheme": block.encoding_scheme.value,
            "data_size": len(block.data),
            "num_sequences": len(block.dna_sequences),
            "created_at": block.created_at.isoformat()
        }
    except Exception as e:
        logger.error(f"Error storing data in DNA: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/retrieve/{block_id}")
async def retrieve_data(block_id: str):
    """Retrieve data from DNA storage"""
    try:
        data = await dna_storage_manager.retrieve_data(block_id)
        
        return {
            "block_id": block_id,
            "data_size": len(data),
            "data": data.decode('utf-8', errors='ignore')  # Simplified
        }
    except Exception as e:
        logger.error(f"Error retrieving data from DNA: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/blocks/{block_id}")
async def get_storage_info(block_id: str):
    """Get storage block information"""
    try:
        info = dna_storage_manager.get_storage_info(block_id)
        return info
    except Exception as e:
        logger.error(f"Error getting storage info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/blocks")
async def list_storage_blocks():
    """List all storage blocks"""
    try:
        blocks = dna_storage_manager.list_storage_blocks()
        return {"blocks": blocks}
    except Exception as e:
        logger.error(f"Error listing storage blocks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sequences/{sequence_id}")
async def get_dna_sequence_info(sequence_id: str):
    """Get DNA sequence information"""
    try:
        info = dna_storage_manager.get_dna_sequence_info(sequence_id)
        return info
    except Exception as e:
        logger.error(f"Error getting DNA sequence info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cost/calculate")
async def calculate_storage_cost(request: CostCalculationRequest):
    """Calculate storage cost"""
    try:
        encoding_scheme = EncodingScheme(request.encoding_scheme)
        cost_info = dna_storage_manager.calculate_storage_cost(
            request.data_size, encoding_scheme, request.redundancy_factor
        )
        return cost_info
    except Exception as e:
        logger.error(f"Error calculating storage cost: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/encoding-schemes")
async def list_encoding_schemes():
    """List supported encoding schemes"""
    try:
        schemes = [scheme.value for scheme in EncodingScheme]
        return {"encoding_schemes": schemes}
    except Exception as e:
        logger.error(f"Error listing encoding schemes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/compression-types")
async def list_compression_types():
    """List supported compression types"""
    try:
        types = [ctype.value for ctype in CompressionType]
        return {"compression_types": types}
    except Exception as e:
        logger.error(f"Error listing compression types: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/error-correction")
async def list_error_correction_schemes():
    """List supported error correction schemes"""
    try:
        schemes = [scheme.value for scheme in ErrorCorrection]
        return {"error_correction_schemes": schemes}
    except Exception as e:
        logger.error(f"Error listing error correction schemes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics")
async def get_storage_metrics():
    """Get DNA storage metrics"""
    try:
        metrics = dna_storage_manager.get_storage_metrics()
        return asdict(metrics)
    except Exception as e:
        logger.error(f"Error getting storage metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_dna_storage_status():
    """Get DNA storage system status"""
    try:
        metrics = dna_storage_manager.get_storage_metrics()
        return {
            "total_blocks": len(dna_storage_manager.storage_blocks),
            "total_sequences": metrics.total_sequences,
            "total_data_size": metrics.total_data_size,
            "compression_ratio": metrics.compression_ratio,
            "error_rate": metrics.error_rate,
            "storage_density": metrics.storage_density,
            "stability_score": metrics.stability_score,
            "cost_per_mb": metrics.cost_per_mb
        }
    except Exception as e:
        logger.error(f"Error getting DNA storage status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
