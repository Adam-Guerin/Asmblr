"""
Quantum-Resistant Cryptography for Asmblr
Post-quantum cryptographic algorithms and security systems
"""

import json
import time
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum
import uuid
import numpy as np
import hashlib
import os
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import base64

logger = logging.getLogger(__name__)

class PostQuantumAlgorithm(Enum):
    """Post-quantum cryptographic algorithms"""
    LATTICE_BASED = "lattice_based"
    CODE_BASED = "code_based"
    MULTIVARIATE = "multivariate"
    HASH_BASED = "hash_based"
    ISOGENY_BASED = "isogeny_based"
    SUPERSINGULAR = "supersingular"
    RING_LWE = "ring_lwe"
    NTRU = "ntru"
    SPHINCS = "sphincs"
    DILITHIUM = "dilithium"
    FALCON = "falcon"

class SecurityLevel(Enum):
    """Security levels for quantum-resistant cryptography"""
    LOW = "low"          # 128-bit classical security
    MEDIUM = "medium"    # 192-bit classical security
    HIGH = "high"        # 256-bit classical security
    ULTRA = "ultra"      # 384-bit classical security

class KeyType(Enum):
    """Key types"""
    PUBLIC_KEY = "public_key"
    PRIVATE_KEY = "private_key"
    SYMMETRIC_KEY = "symmetric_key"
    SIGNATURE_KEY = "signature_key"
    ENCRYPTION_KEY = "encryption_key"

@dataclass
class QuantumResistantKey:
    """Quantum-resistant cryptographic key"""
    id: str
    algorithm: PostQuantumAlgorithm
    security_level: SecurityLevel
    key_type: KeyType
    key_data: bytes
    public_key: Optional[bytes]
    private_key: Optional[bytes]
    signature: Optional[bytes]
    metadata: Dict[str, Any]
    created_at: datetime
    expires_at: Optional[datetime]
    is_active: bool

@dataclass
class CipherText:
    """Encrypted data with quantum-resistant cryptography"""
    id: str
    algorithm: PostQuantumAlgorithm
    key_id: str
    ciphertext: bytes
    nonce: Optional[bytes]
    tag: Optional[bytes]
    metadata: Dict[str, Any]
    encrypted_at: datetime

@dataclass
class DigitalSignature:
    """Digital signature using quantum-resistant algorithms"""
    id: str
    algorithm: PostQuantumAlgorithm
    key_id: str
    message_hash: bytes
    signature: bytes
    public_key: bytes
    metadata: Dict[str, Any]
    signed_at: datetime
    verified: bool = False

class LatticeBasedCrypto:
    """Lattice-based cryptography implementation"""
    
    def __init__(self, security_level: SecurityLevel = SecurityLevel.HIGH):
        self.security_level = security_level
        self.n = self._get_parameter_n()
        self.q = self._get_parameter_q()
        self.m = self._get_parameter_m()
        
    def _get_parameter_n(self) -> int:
        """Get lattice dimension based on security level"""
        params = {
            SecurityLevel.LOW: 512,
            SecurityLevel.MEDIUM: 768,
            SecurityLevel.HIGH: 1024,
            SecurityLevel.ULTRA: 1536
        }
        return params[self.security_level]
    
    def _get_parameter_q(self) -> int:
        """Get modulus based on security level"""
        params = {
            SecurityLevel.LOW: 2**15 - 1,
            SecurityLevel.MEDIUM: 2**20 - 1,
            SecurityLevel.HIGH: 2**25 - 1,
            SecurityLevel.ULTRA: 2**30 - 1
        }
        return params[self.security_level]
    
    def _get_parameter_m(self) -> int:
        """Get error bound parameter"""
        return self.n // 4
    
    def generate_keypair(self) -> Tuple[bytes, bytes]:
        """Generate lattice-based keypair"""
        try:
            # Generate random matrix A (n x m)
            A = np.random.randint(0, self.q, size=(self.n, self.m), dtype=np.int64)
            
            # Generate random secret vector s (m-dimensional)
            s = np.random.randint(-self.m, self.m + 1, size=self.m, dtype=np.int64)
            
            # Generate random error vector e (n-dimensional)
            e = np.random.randint(-1, 2, size=self.n, dtype=np.int64)
            
            # Compute public key: t = A * s + e mod q
            As = np.dot(A, s) % self.q
            t = (As + e) % self.q
            
            # Serialize keys
            public_key = self._serialize_public_key(A, t)
            private_key = self._serialize_private_key(A, s, e)
            
            return public_key, private_key
            
        except Exception as e:
            logger.error(f"Error generating lattice keypair: {e}")
            raise
    
    def _serialize_public_key(self, A: np.ndarray, t: np.ndarray) -> bytes:
        """Serialize public key"""
        try:
            data = {
                'A': A.tolist(),
                't': t.tolist(),
                'n': self.n,
                'q': self.q,
                'm': self.m
            }
            return json.dumps(data).encode()
        except Exception as e:
            logger.error(f"Error serializing public key: {e}")
            raise
    
    def _serialize_private_key(self, A: np.ndarray, s: np.ndarray, e: np.ndarray) -> bytes:
        """Serialize private key"""
        try:
            data = {
                'A': A.tolist(),
                's': s.tolist(),
                'e': e.tolist(),
                'n': self.n,
                'q': self.q,
                'm': self.m
            }
            return json.dumps(data).encode()
        except Exception as e:
            logger.error(f"Error serializing private key: {e}")
            raise
    
    def encrypt(self, plaintext: bytes, public_key: bytes) -> bytes:
        """Encrypt using lattice-based cryptography"""
        try:
            # Deserialize public key
            key_data = json.loads(public_key.decode())
            A = np.array(key_data['A'], dtype=np.int64)
            t = np.array(key_data['t'], dtype=np.int64)
            
            # Convert plaintext to vector
            plaintext_int = int.from_bytes(plaintext, 'big')
            plaintext_vector = np.array([plaintext_int % self.q] + [0] * (self.m - 1), dtype=np.int64)
            
            # Generate random error vectors
            r = np.random.randint(-1, 2, size=self.m, dtype=np.int64)
            e1 = np.random.randint(-1, 2, size=self.n, dtype=np.int64)
            e2 = np.random.randint(-1, 2, dtype=np.int64)
            
            # Compute ciphertext: (u, v) where u = A^T * r + e1, v = t^T * r + e2 + plaintext
            u = (np.dot(A.T, r) + e1) % self.q
            v = (np.dot(t, r) + e2 + plaintext_vector[0]) % self.q
            
            # Serialize ciphertext
            ciphertext_data = {
                'u': u.tolist(),
                'v': int(v),
                'n': self.n,
                'q': self.q
            }
            
            return json.dumps(ciphertext_data).encode()
            
        except Exception as e:
            logger.error(f"Error encrypting with lattice crypto: {e}")
            raise
    
    def decrypt(self, ciphertext: bytes, private_key: bytes) -> bytes:
        """Decrypt using lattice-based cryptography"""
        try:
            # Deserialize private key
            key_data = json.loads(private_key.decode())
            A = np.array(key_data['A'], dtype=np.int64)
            s = np.array(key_data['s'], dtype=np.int64)
            
            # Deserialize ciphertext
            cipher_data = json.loads(ciphertext.decode())
            u = np.array(cipher_data['u'], dtype=np.int64)
            v = int(cipher_data['v'])
            
            # Decrypt: plaintext = v - s^T * u mod q
            sTu = np.dot(s, u) % self.q
            plaintext_int = (v - sTu) % self.q
            
            # Convert back to bytes
            # Determine byte length needed
            byte_length = (plaintext_int.bit_length() + 7) // 8
            return plaintext_int.to_bytes(byte_length, 'big')
            
        except Exception as e:
            logger.error(f"Error decrypting with lattice crypto: {e}")
            raise
    
    def sign(self, message: bytes, private_key: bytes) -> bytes:
        """Sign message using lattice-based signature"""
        try:
            # Hash message
            message_hash = hashlib.sha256(message).digest()
            hash_int = int.from_bytes(message_hash, 'big')
            
            # Deserialize private key
            key_data = json.loads(private_key.decode())
            A = np.array(key_data['A'], dtype=np.int64)
            s = np.array(key_data['s'], dtype=np.int64)
            
            # Generate signature using Fiat-Shamir with aborts
            # Simplified version - in practice would use proper lattice signature scheme
            
            # Generate random vector y
            y = np.random.randint(-self.m, self.m + 1, size=self.m, dtype=np.int64)
            
            # Compute commitment: w = A * y mod q
            w = np.dot(A, y) % self.q
            
            # Compute challenge: c = H(A, w, message)
            challenge_data = {
                'A_hash': hashlib.sha256(A.tobytes()).hexdigest(),
                'w_hash': hashlib.sha256(w.tobytes()).hexdigest(),
                'message_hash': hashlib.sha256(message).hexdigest()
            }
            c = int(hashlib.sha256(json.dumps(challenge_data).encode()).hexdigest(), 16) % self.q
            
            # Compute response: z = y + c * s
            z = (y + c * s) % self.q
            
            # Serialize signature
            signature_data = {
                'z': z.tolist(),
                'w': w.tolist(),
                'c': c,
                'n': self.n,
                'q': self.q
            }
            
            return json.dumps(signature_data).encode()
            
        except Exception as e:
            logger.error(f"Error signing with lattice crypto: {e}")
            raise
    
    def verify(self, message: bytes, signature: bytes, public_key: bytes) -> bool:
        """Verify signature using lattice-based cryptography"""
        try:
            # Deserialize public key
            key_data = json.loads(public_key.decode())
            A = np.array(key_data['A'], dtype=np.int64)
            t = np.array(key_data['t'], dtype=np.int64)
            
            # Deserialize signature
            sig_data = json.loads(signature.decode())
            z = np.array(sig_data['z'], dtype=np.int64)
            w = np.array(sig_data['w'], dtype=np.int64)
            c = sig_data['c']
            
            # Recompute challenge: c' = H(A, A*z - c*w, message)
            Az_cw = (np.dot(A, z) - c * w) % self.q
            challenge_data = {
                'A_hash': hashlib.sha256(A.tobytes()).hexdigest(),
                'w_hash': hashlib.sha256(Az_cw.tobytes()).hexdigest(),
                'message_hash': hashlib.sha256(message).hexdigest()
            }
            c_prime = int(hashlib.sha256(json.dumps(challenge_data).encode()).hexdigest(), 16) % self.q
            
            # Verify c == c'
            return c == c_prime
            
        except Exception as e:
            logger.error(f"Error verifying lattice signature: {e}")
            return False

class HashBasedCrypto:
    """Hash-based cryptography (SPHINCS+) implementation"""
    
    def __init__(self, security_level: SecurityLevel = SecurityLevel.HIGH):
        self.security_level = security_level
        self.n = self._get_parameter_n()
        self.w = self._get_parameter_w()
        self.h = self._get_parameter_h()
        
    def _get_parameter_n(self) -> int:
        """Get parameter n based on security level"""
        params = {
            SecurityLevel.LOW: 16,
            SecurityLevel.MEDIUM: 32,
            SecurityLevel.HIGH: 64,
            SecurityLevel.ULTRA: 128
        }
        return params[self.security_level]
    
    def _get_parameter_w(self) -> int:
        """Get Winternitz parameter"""
        params = {
            SecurityLevel.LOW: 16,
            SecurityLevel.MEDIUM: 16,
            SecurityLevel.HIGH: 16,
            SecurityLevel.ULTRA: 16
        }
        return params[self.security_level]
    
    def _get_parameter_h(self) -> int:
        """Get height parameter"""
        params = {
            SecurityLevel.LOW: 64,
            SecurityLevel.MEDIUM: 64,
            SecurityLevel.HIGH: 64,
            SecurityLevel.ULTRA: 64
        }
        return params[self.security_level]
    
    def generate_keypair(self) -> Tuple[bytes, bytes]:
        """Generate SPHINCS+ keypair"""
        try:
            # Generate secret key (simplified)
            secret_key = os.urandom(64)
            
            # Generate public key from secret key
            public_key = hashlib.sha256(secret_key).digest()
            
            # Serialize keys
            public_key_data = {
                'public_key': public_key.hex(),
                'n': self.n,
                'w': self.w,
                'h': self.h
            }
            
            private_key_data = {
                'secret_key': secret_key.hex(),
                'public_key': public_key.hex(),
                'n': self.n,
                'w': self.w,
                'h': self.h
            }
            
            return json.dumps(public_key_data).encode(), json.dumps(private_key_data).encode()
            
        except Exception as e:
            logger.error(f"Error generating SPHINCS+ keypair: {e}")
            raise
    
    def sign(self, message: bytes, private_key: bytes) -> bytes:
        """Sign message using SPHINCS+"""
        try:
            # Deserialize private key
            key_data = json.loads(private_key.decode())
            secret_key = bytes.fromhex(key_data['secret_key'])
            
            # Generate one-time signature (simplified)
            # In real SPHINCS+, would use WOTS+ and Merkle trees
            
            # Generate random nonce
            nonce = os.urandom(32)
            
            # Compute message hash
            message_hash = hashlib.sha256(message + nonce).digest()
            
            # Generate signature using secret key
            signature_data = {
                'nonce': nonce.hex(),
                'message_hash': message_hash.hex(),
                'signature': hashlib.sha256(secret_key + message_hash).hexdigest(),
                'n': self.n,
                'w': self.w,
                'h': self.h
            }
            
            return json.dumps(signature_data).encode()
            
        except Exception as e:
            logger.error(f"Error signing with SPHINCS+: {e}")
            raise
    
    def verify(self, message: bytes, signature: bytes, public_key: bytes) -> bool:
        """Verify SPHINCS+ signature"""
        try:
            # Deserialize public key
            key_data = json.loads(public_key.decode())
            public_key_hash = bytes.fromhex(key_data['public_key'])
            
            # Deserialize signature
            sig_data = json.loads(signature.decode())
            nonce = bytes.fromhex(sig_data['nonce'])
            message_hash = bytes.fromhex(sig_data['message_hash'])
            signature_hash = sig_data['signature']
            
            # Recompute message hash
            computed_hash = hashlib.sha256(message + nonce).digest()
            
            # Verify hash matches
            if computed_hash != message_hash:
                return False
            
            # Verify signature (simplified)
            expected_signature = hashlib.sha256(public_key_hash + message_hash).hexdigest()
            
            return signature_hash == expected_signature
            
        except Exception as e:
            logger.error(f"Error verifying SPHINCS+ signature: {e}")
            return False

class CodeBasedCrypto:
    """Code-based cryptography (McEliece) implementation"""
    
    def __init__(self, security_level: SecurityLevel = SecurityLevel.HIGH):
        self.security_level = security_level
        self.n = self._get_parameter_n()
        self.k = self._get_parameter_k()
        self.t = self._get_parameter_t()
        
    def _get_parameter_n(self) -> int:
        """Get code length"""
        params = {
            SecurityLevel.LOW: 2048,
            SecurityLevel.MEDIUM: 3488,
            SecurityLevel.HIGH: 6960,
            SecurityLevel.ULTRA: 8192
        }
        return params[self.security_level]
    
    def _get_parameter_k(self) -> int:
        """Get message length"""
        params = {
            SecurityLevel.LOW: 1600,
            SecurityLevel.MEDIUM: 2720,
            SecurityLevel.HIGH: 5412,
            SecurityLevel.ULTRA: 6528
        }
        return params[self.security_level]
    
    def _get_parameter_t(self) -> int:
        """Get error correction capability"""
        params = {
            SecurityLevel.LOW: 40,
            SecurityLevel.MEDIUM: 56,
            SecurityLevel.HIGH: 119,
            SecurityLevel.ULTRA: 128
        }
        return params[self.security_level]
    
    def generate_keypair(self) -> Tuple[bytes, bytes]:
        """Generate McEliece keypair"""
        try:
            # Generate random generator matrix G (simplified)
            # In real McEliece, would use binary Goppa codes
            G = np.random.randint(0, 2, size=(self.k, self.n), dtype=np.uint8)
            
            # Generate random permutation matrix P
            P = np.eye(self.n, dtype=np.uint8)
            np.random.shuffle(P.T)
            
            # Compute public key: G' = G * P
            G_prime = np.dot(G, P) % 2
            
            # Generate error vector e
            e = np.zeros(self.n, dtype=np.uint8)
            error_positions = np.random.choice(self.n, self.t, replace=False)
            e[error_positions] = 1
            
            # Serialize keys
            public_key_data = {
                'G_prime': G_prime.tolist(),
                'n': self.n,
                'k': self.k,
                't': self.t
            }
            
            private_key_data = {
                'G': G.tolist(),
                'P': P.tolist(),
                'n': self.n,
                'k': self.k,
                't': self.t
            }
            
            return json.dumps(public_key_data).encode(), json.dumps(private_key_data).encode()
            
        except Exception as e:
            logger.error(f"Error generating McEliece keypair: {e}")
            raise
    
    def encrypt(self, plaintext: bytes, public_key: bytes) -> bytes:
        """Encrypt using McEliece"""
        try:
            # Deserialize public key
            key_data = json.loads(public_key.decode())
            G_prime = np.array(key_data['G_prime'], dtype=np.uint8)
            
            # Convert plaintext to binary vector
            plaintext_bits = ''.join(format(byte, '08b') for byte in plaintext)
            if len(plaintext_bits) < self.k:
                plaintext_bits += '0' * (self.k - len(plaintext_bits))
            else:
                plaintext_bits = plaintext_bits[:self.k]
            
            m = np.array([int(bit) for bit in plaintext_bits], dtype=np.uint8)
            
            # Generate random error vector e
            e = np.zeros(self.n, dtype=np.uint8)
            error_positions = np.random.choice(self.n, self.t, replace=False)
            e[error_positions] = 1
            
            # Compute ciphertext: c = m * G' + e
            c = (np.dot(m, G_prime) + e) % 2
            
            # Serialize ciphertext
            ciphertext_data = {
                'c': c.tolist(),
                'n': self.n,
                't': self.t
            }
            
            return json.dumps(ciphertext_data).encode()
            
        except Exception as e:
            logger.error(f"Error encrypting with McEliece: {e}")
            raise
    
    def decrypt(self, ciphertext: bytes, private_key: bytes) -> bytes:
        """Decrypt using McEliece"""
        try:
            # Deserialize private key
            key_data = json.loads(private_key.decode())
            G = np.array(key_data['G'], dtype=np.uint8)
            P = np.array(key_data['P'], dtype=np.uint8)
            
            # Deserialize ciphertext
            cipher_data = json.loads(ciphertext.decode())
            c = np.array(cipher_data['c'], dtype=np.uint8)
            
            # Apply inverse permutation: c' = c * P^(-1)
            P_inv = np.linalg.inv(P.astype(float)) % 2
            c_prime = np.dot(c, P_inv) % 2
            
            # Decode using error correction (simplified)
            # In real McEliece, would use Berlekamp-Massey algorithm
            m = c_prime[:self.k]  # Simplified - just take first k bits
            
            # Convert back to bytes
            bits = ''.join(str(bit) for bit in m)
            byte_length = len(bits) // 8
            plaintext = int(bits, 2).to_bytes(byte_length, 'big')
            
            return plaintext
            
        except Exception as e:
            logger.error(f"Error decrypting with McEliece: {e}")
            raise

class QuantumResistantCryptoManager:
    """Manager for quantum-resistant cryptography"""
    
    def __init__(self):
        self.algorithms = {
            PostQuantumAlgorithm.LATTICE_BASED: LatticeBasedCrypto,
            PostQuantumAlgorithm.HASH_BASED: HashBasedCrypto,
            PostQuantumAlgorithm.CODE_BASED: CodeBasedCrypto
        }
        
        self.keys: Dict[str, QuantumResistantKey] = {}
        self.ciphertexts: Dict[str, CipherText] = {}
        self.signatures: Dict[str, DigitalSignature] = {}
        
        # Start background tasks
        asyncio.create_task(self._key_rotation_loop())
        asyncio.create_task(self._security_audit_loop())
    
    async def generate_key(self, algorithm: PostQuantumAlgorithm, 
                          security_level: SecurityLevel,
                          key_type: KeyType,
                          expires_in_days: int = 365) -> QuantumResistantKey:
        """Generate quantum-resistant key"""
        try:
            if algorithm not in self.algorithms:
                raise ValueError(f"Algorithm {algorithm} not supported")
            
            crypto_class = self.algorithms[algorithm](security_level)
            
            # Generate keypair
            if key_type in [KeyType.PUBLIC_KEY, KeyType.SIGNATURE_KEY]:
                public_key, private_key = crypto_class.generate_keypair()
            else:
                # Generate symmetric key
                public_key = None
                private_key = os.urandom(32)  # 256-bit key
            
            # Create key object
            key = QuantumResistantKey(
                id=str(uuid.uuid4()),
                algorithm=algorithm,
                security_level=security_level,
                key_type=key_type,
                key_data=private_key,
                public_key=public_key,
                private_key=private_key,
                signature=None,
                metadata={
                    'key_size': len(private_key),
                    'algorithm_params': {
                        'n': crypto_class.n if hasattr(crypto_class, 'n') else None,
                        'q': crypto_class.q if hasattr(crypto_class, 'q') else None
                    }
                },
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(days=expires_in_days),
                is_active=True
            )
            
            self.keys[key.id] = key
            
            logger.info(f"Generated quantum-resistant key: {key.id}")
            return key
            
        except Exception as e:
            logger.error(f"Error generating quantum-resistant key: {e}")
            raise
    
    async def encrypt_data(self, data: bytes, key_id: str) -> CipherText:
        """Encrypt data with quantum-resistant cryptography"""
        try:
            key = self.keys.get(key_id)
            if not key:
                raise ValueError(f"Key {key_id} not found")
            
            if not key.is_active:
                raise ValueError(f"Key {key_id} is not active")
            
            # Check expiration
            if key.expires_at and datetime.now() > key.expires_at:
                raise ValueError(f"Key {key_id} has expired")
            
            # Get crypto implementation
            crypto_class = self.algorithms[key.algorithm](key.security_level)
            
            # Encrypt data
            if key.algorithm == PostQuantumAlgorithm.LATTICE_BASED:
                ciphertext = crypto_class.encrypt(data, key.public_key)
            elif key.algorithm == PostQuantumAlgorithm.CODE_BASED:
                ciphertext = crypto_class.encrypt(data, key.public_key)
            else:
                # For hash-based, use symmetric encryption
                from cryptography.fernet import Fernet
                fernet_key = base64.urlsafe_b64encode(key.key_data)
                fernet = Fernet(fernet_key)
                ciphertext = fernet.encrypt(data)
            
            # Create ciphertext object
            cipher_obj = CipherText(
                id=str(uuid.uuid4()),
                algorithm=key.algorithm,
                key_id=key_id,
                ciphertext=ciphertext,
                nonce=None,
                tag=None,
                metadata={
                    'algorithm': key.algorithm.value,
                    'security_level': key.security_level.value,
                    'key_type': key.key_type.value
                },
                encrypted_at=datetime.now()
            )
            
            self.ciphertexts[cipher_obj.id] = cipher_obj
            
            logger.info(f"Encrypted data with quantum-resistant crypto: {cipher_obj.id}")
            return cipher_obj
            
        except Exception as e:
            logger.error(f"Error encrypting data: {e}")
            raise
    
    async def decrypt_data(self, ciphertext_id: str) -> bytes:
        """Decrypt data with quantum-resistant cryptography"""
        try:
            cipher_obj = self.ciphertexts.get(ciphertext_id)
            if not cipher_obj:
                raise ValueError(f"Ciphertext {ciphertext_id} not found")
            
            key = self.keys.get(cipher_obj.key_id)
            if not key:
                raise ValueError(f"Key {cipher_obj.key_id} not found")
            
            if not key.is_active:
                raise ValueError(f"Key {cipher_obj.key_id} is not active")
            
            # Get crypto implementation
            crypto_class = self.algorithms[key.algorithm](key.security_level)
            
            # Decrypt data
            if key.algorithm == PostQuantumAlgorithm.LATTICE_BASED:
                plaintext = crypto_class.decrypt(cipher_obj.ciphertext, key.private_key)
            elif key.algorithm == PostQuantumAlgorithm.CODE_BASED:
                plaintext = crypto_class.decrypt(cipher_obj.ciphertext, key.private_key)
            else:
                # For hash-based, use symmetric decryption
                from cryptography.fernet import Fernet
                fernet_key = base64.urlsafe_b64encode(key.key_data)
                fernet = Fernet(fernet_key)
                plaintext = fernet.decrypt(cipher_obj.ciphertext)
            
            logger.info(f"Decrypted data with quantum-resistant crypto: {ciphertext_id}")
            return plaintext
            
        except Exception as e:
            logger.error(f"Error decrypting data: {e}")
            raise
    
    async def sign_message(self, message: bytes, key_id: str) -> DigitalSignature:
        """Sign message with quantum-resistant signature"""
        try:
            key = self.keys.get(key_id)
            if not key:
                raise ValueError(f"Key {key_id} not found")
            
            if key.key_type not in [KeyType.SIGNATURE_KEY, KeyType.PRIVATE_KEY]:
                raise ValueError(f"Key {key_id} is not a signing key")
            
            # Get crypto implementation
            crypto_class = self.algorithms[key.algorithm](key.security_level)
            
            # Sign message
            signature = crypto_class.sign(message, key.private_key)
            
            # Create signature object
            signature_obj = DigitalSignature(
                id=str(uuid.uuid4()),
                algorithm=key.algorithm,
                key_id=key_id,
                message_hash=hashlib.sha256(message).digest(),
                signature=signature,
                public_key=key.public_key,
                metadata={
                    'algorithm': key.algorithm.value,
                    'security_level': key.security_level.value
                },
                signed_at=datetime.now()
            )
            
            self.signatures[signature_obj.id] = signature_obj
            
            logger.info(f"Signed message with quantum-resistant signature: {signature_obj.id}")
            return signature_obj
            
        except Exception as e:
            logger.error(f"Error signing message: {e}")
            raise
    
    async def verify_signature(self, message: bytes, signature_id: str) -> bool:
        """Verify quantum-resistant signature"""
        try:
            signature_obj = self.signatures.get(signature_id)
            if not signature_obj:
                raise ValueError(f"Signature {signature_id} not found")
            
            # Get crypto implementation
            crypto_class = self.algorithms[signature_obj.algorithm](SecurityLevel.HIGH)
            
            # Verify signature
            is_valid = crypto_class.verify(message, signature_obj.signature, signature_obj.public_key)
            
            # Update verification status
            signature_obj.verified = is_valid
            
            logger.info(f"Verified quantum-resistant signature: {signature_id}, valid: {is_valid}")
            return is_valid
            
        except Exception as e:
            logger.error(f"Error verifying signature: {e}")
            return False
    
    async def rotate_key(self, key_id: str) -> QuantumResistantKey:
        """Rotate quantum-resistant key"""
        try:
            old_key = self.keys.get(key_id)
            if not old_key:
                raise ValueError(f"Key {key_id} not found")
            
            # Generate new key
            new_key = await self.generate_key(
                old_key.algorithm,
                old_key.security_level,
                old_key.key_type,
                expires_in_days=365
            )
            
            # Deactivate old key
            old_key.is_active = False
            
            logger.info(f"Rotated quantum-resistant key: {key_id} -> {new_key.id}")
            return new_key
            
        except Exception as e:
            logger.error(f"Error rotating key: {e}")
            raise
    
    async def _key_rotation_loop(self):
        """Background key rotation loop"""
        while True:
            try:
                # Check for keys that need rotation
                current_time = datetime.now()
                
                for key_id, key in self.keys.items():
                    if key.is_active and key.expires_at:
                        # Rotate keys that expire within 7 days
                        if (key.expires_at - current_time).days <= 7:
                            await self.rotate_key(key_id)
                
                # Wait before next check
                await asyncio.sleep(86400)  # Check daily
                
            except Exception as e:
                logger.error(f"Error in key rotation loop: {e}")
                await asyncio.sleep(3600)
    
    async def _security_audit_loop(self):
        """Background security audit loop"""
        while True:
            try:
                # Perform security audit
                audit_results = await self._perform_security_audit()
                
                # Log audit results
                logger.info(f"Security audit completed: {audit_results}")
                
                # Wait before next audit
                await asyncio.sleep(604800)  # Audit weekly
                
            except Exception as e:
                logger.error(f"Error in security audit loop: {e}")
                await asyncio.sleep(86400)
    
    async def _perform_security_audit(self) -> Dict[str, Any]:
        """Perform security audit"""
        try:
            audit_results = {
                'total_keys': len(self.keys),
                'active_keys': len([k for k in self.keys.values() if k.is_active]),
                'expired_keys': len([k for k in self.keys.values() if k.expires_at and datetime.now() > k.expires_at]),
                'total_ciphertexts': len(self.ciphertexts),
                'total_signatures': len(self.signatures),
                'algorithm_distribution': {},
                'security_level_distribution': {},
                'key_type_distribution': {}
            }
            
            # Analyze key distribution
            for key in self.keys.values():
                # Algorithm distribution
                algo = key.algorithm.value
                audit_results['algorithm_distribution'][algo] = audit_results['algorithm_distribution'].get(algo, 0) + 1
                
                # Security level distribution
                level = key.security_level.value
                audit_results['security_level_distribution'][level] = audit_results['security_level_distribution'].get(level, 0) + 1
                
                # Key type distribution
                key_type = key.key_type.value
                audit_results['key_type_distribution'][key_type] = audit_results['key_type_distribution'].get(key_type, 0) + 1
            
            return audit_results
            
        except Exception as e:
            logger.error(f"Error performing security audit: {e}")
            return {}
    
    def get_key_info(self, key_id: str) -> Dict[str, Any]:
        """Get key information"""
        try:
            key = self.keys.get(key_id)
            if not key:
                return {"error": "Key not found"}
            
            return {
                "id": key.id,
                "algorithm": key.algorithm.value,
                "security_level": key.security_level.value,
                "key_type": key.key_type.value,
                "created_at": key.created_at.isoformat(),
                "expires_at": key.expires_at.isoformat() if key.expires_at else None,
                "is_active": key.is_active,
                "metadata": key.metadata
            }
            
        except Exception as e:
            logger.error(f"Error getting key info: {e}")
            return {"error": str(e)}
    
    def list_keys(self, algorithm: Optional[PostQuantumAlgorithm] = None,
                  security_level: Optional[SecurityLevel] = None,
                  key_type: Optional[KeyType] = None) -> List[Dict[str, Any]]:
        """List keys with optional filters"""
        try:
            keys = []
            
            for key in self.keys.values():
                # Apply filters
                if algorithm and key.algorithm != algorithm:
                    continue
                if security_level and key.security_level != security_level:
                    continue
                if key_type and key.key_type != key_type:
                    continue
                
                keys.append({
                    "id": key.id,
                    "algorithm": key.algorithm.value,
                    "security_level": key.security_level.value,
                    "key_type": key.key_type.value,
                    "created_at": key.created_at.isoformat(),
                    "expires_at": key.expires_at.isoformat() if key.expires_at else None,
                    "is_active": key.is_active
                })
            
            return keys
            
        except Exception as e:
            logger.error(f"Error listing keys: {e}")
            return []

# Global quantum-resistant crypto manager
qr_crypto_manager = QuantumResistantCryptoManager()

# API endpoints
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/quantum_crypto", tags=["quantum_resistant_crypto"])

class KeyGenerationRequest(BaseModel):
    algorithm: str
    security_level: str = "high"
    key_type: str = "public_key"
    expires_in_days: int = 365

class EncryptionRequest(BaseModel):
    data: str  # Base64 encoded
    key_id: str

class SignatureRequest(BaseModel):
    message: str  # Base64 encoded
    key_id: str

@router.post("/keys/generate")
async def generate_quantum_key(request: KeyGenerationRequest):
    """Generate quantum-resistant key"""
    try:
        algorithm = PostQuantumAlgorithm(request.algorithm)
        security_level = SecurityLevel(request.security_level)
        key_type = KeyType(request.key_type)
        
        key = await qr_crypto_manager.generate_key(
            algorithm, security_level, key_type, request.expires_in_days
        )
        
        return asdict(key)
    except Exception as e:
        logger.error(f"Error generating quantum key: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/encrypt")
async def encrypt_data(request: EncryptionRequest):
    """Encrypt data with quantum-resistant cryptography"""
    try:
        import base64
        data = base64.b64decode(request.data)
        
        ciphertext = await qr_crypto_manager.encrypt_data(data, request.key_id)
        
        return {
            "ciphertext_id": ciphertext.id,
            "algorithm": ciphertext.algorithm.value,
            "encrypted_at": ciphertext.encrypted_at.isoformat()
        }
    except Exception as e:
        logger.error(f"Error encrypting data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/decrypt")
async def decrypt_data(ciphertext_id: str):
    """Decrypt data with quantum-resistant cryptography"""
    try:
        plaintext = await qr_crypto_manager.decrypt_data(ciphertext_id)
        
        import base64
        return {
            "plaintext": base64.b64encode(plaintext).decode()
        }
    except Exception as e:
        logger.error(f"Error decrypting data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sign")
async def sign_message(request: SignatureRequest):
    """Sign message with quantum-resistant signature"""
    try:
        import base64
        message = base64.b64decode(request.message)
        
        signature = await qr_crypto_manager.sign_message(message, request.key_id)
        
        return asdict(signature)
    except Exception as e:
        logger.error(f"Error signing message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/verify")
async def verify_signature(message: str, signature_id: str):
    """Verify quantum-resistant signature"""
    try:
        import base64
        message_bytes = base64.b64decode(message)
        
        is_valid = await qr_crypto_manager.verify_signature(message_bytes, signature_id)
        
        return {"valid": is_valid}
    except Exception as e:
        logger.error(f"Error verifying signature: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/keys/{key_id}/rotate")
async def rotate_key(key_id: str):
    """Rotate quantum-resistant key"""
    try:
        new_key = await qr_crypto_manager.rotate_key(key_id)
        return asdict(new_key)
    except Exception as e:
        logger.error(f"Error rotating key: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/keys/{key_id}")
async def get_key_info(key_id: str):
    """Get key information"""
    try:
        info = qr_crypto_manager.get_key_info(key_id)
        return info
    except Exception as e:
        logger.error(f"Error getting key info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/keys")
async def list_keys(algorithm: Optional[str] = None,
                   security_level: Optional[str] = None,
                   key_type: Optional[str] = None):
    """List quantum-resistant keys"""
    try:
        algo = PostQuantumAlgorithm(algorithm) if algorithm else None
        level = SecurityLevel(security_level) if security_level else None
        ktype = KeyType(key_type) if key_type else None
        
        keys = qr_crypto_manager.list_keys(algo, level, ktype)
        return {"keys": keys}
    except Exception as e:
        logger.error(f"Error listing keys: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/algorithms")
async def list_algorithms():
    """List supported quantum-resistant algorithms"""
    try:
        algorithms = [algo.value for algo in PostQuantumAlgorithm]
        return {"algorithms": algorithms}
    except Exception as e:
        logger.error(f"Error listing algorithms: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/security-levels")
async def list_security_levels():
    """List security levels"""
    try:
        levels = [level.value for level in SecurityLevel]
        return {"security_levels": levels}
    except Exception as e:
        logger.error(f"Error listing security levels: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_quantum_crypto_status():
    """Get quantum-resistant crypto status"""
    try:
        audit_results = await qr_crypto_manager._perform_security_audit()
        return audit_results
    except Exception as e:
        logger.error(f"Error getting quantum crypto status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
