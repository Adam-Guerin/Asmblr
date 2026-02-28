"""
Blockchain Integration for Asmblr
Smart contracts, decentralized storage, and Web3 capabilities
"""

import json
import time
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum
import uuid
import hashlib
import secrets
from web3 import Web3
from web3.contract import Contract
from web3.middleware import geth_poa_middleware
from eth_account import Account
from eth_account.messages import encode_defunct
import ipfshttpclient
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, PublicFormat

logger = logging.getLogger(__name__)

class BlockchainNetwork(Enum):
    """Supported blockchain networks"""
    ETHEREUM_MAINNET = "ethereum_mainnet"
    ETHEREUM_SEPOLIA = "ethereum_sepolia"
    POLYGON = "polygon"
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"
    BASE = "base"
    LOCAL_GETH = "local_geth"

class ContractType(Enum):
    """Smart contract types"""
    MVP_REGISTRY = "mvp_registry"
    PROJECT_FUNDING = "project_funding"
    REPUTATION_SYSTEM = "reputation_system"
    DATA_MARKETPLACE = "data_marketplace"
    COLLABORATION DAO = "collaboration_dao"
    INTELLECTUAL_PROPERTY = "intellectual_property"

@dataclass
class BlockchainConfig:
    """Blockchain configuration"""
    network: BlockchainNetwork
    rpc_url: str
    chain_id: int
    gas_price_gwei: float
    max_gas_limit: int
    block_time_seconds: int
    confirmation_blocks: int

@dataclass
class SmartContract:
    """Smart contract information"""
    address: str
    abi: List[Dict[str, Any]]
    bytecode: str
    contract_type: ContractType
    deployed_at: datetime
    deployer: str
    transaction_hash: str
    block_number: int
    gas_used: int

@dataclass
class Transaction:
    """Blockchain transaction"""
    hash: str
    from_address: str
    to_address: Optional[str]
    value: int
    gas_price: int
    gas_limit: int
    gas_used: int
    block_number: int
    timestamp: datetime
    status: str  # pending, confirmed, failed
    data: str

@dataclass
class DecentralizedIdentity:
    """Decentralized identity (DID)"""
    did: str
    public_key: str
    verification_methods: List[Dict[str, Any]]
    services: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

class BlockchainManager:
    """Blockchain integration manager"""
    
    def __init__(self, config: BlockchainConfig):
        self.config = config
        self.w3 = None
        self.account = None
        self.contracts: Dict[str, SmartContract] = {}
        self.ipfs_client = None
        self.identities: Dict[str, DecentralizedIdentity] = {}
        
        # Initialize blockchain connection
        self._initialize_blockchain()
        
        # Initialize IPFS
        self._initialize_ipfs()
        
        # Load contract ABIs
        self._load_contract_abis()
    
    def _initialize_blockchain(self):
        """Initialize blockchain connection"""
        try:
            self.w3 = Web3(Web3.HTTPProvider(self.config.rpc_url))
            
            # Add POA middleware for test networks
            if self.config.network in [BlockchainNetwork.ETHEREUM_SEPOLIA, BlockchainNetwork.POLYGON]:
                self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
            
            # Check connection
            if self.w3.is_connected():
                logger.info(f"Connected to {self.config.network.value}")
                
                # Get chain info
                chain_id = self.w3.eth.chain_id
                if chain_id != self.config.chain_id:
                    logger.warning(f"Chain ID mismatch: expected {self.config.chain_id}, got {chain_id}")
            else:
                raise ConnectionError("Failed to connect to blockchain")
                
        except Exception as e:
            logger.error(f"Error initializing blockchain: {e}")
            raise
    
    def _initialize_ipfs(self):
        """Initialize IPFS client"""
        try:
            self.ipfs_client = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001')
            self.ipfs_client.stats()
            logger.info("Connected to IPFS node")
        except Exception as e:
            logger.error(f"Error initializing IPFS: {e}")
            self.ipfs_client = None
    
    def _load_contract_abis(self):
        """Load contract ABIs"""
        self.contract_abis = {
            ContractType.MVP_REGISTRY: self._get_mvp_registry_abi(),
            ContractType.PROJECT_FUNDING: self._get_project_funding_abi(),
            ContractType.REPUTATION_SYSTEM: self._get_reputation_system_abi(),
            ContractType.DATA_MARKETPLACE: self._get_data_marketplace_abi(),
            ContractType.COLLABORATION_DAO: self._get_collaboration_dao_abi(),
            ContractType.INTELLECTUAL_PROPERTY: self._get_intellectual_property_abi()
        }
    
    def _get_mvp_registry_abi(self) -> List[Dict[str, Any]]:
        """Get MVP Registry contract ABI"""
        return [
            {
                "type": "constructor",
                "inputs": [{"name": "name", "type": "string"}, {"name": "symbol", "type": "string"}],
                "stateMutability": "nonpayable"
            },
            {
                "type": "function",
                "name": "registerMVP",
                "inputs": [
                    {"name": "projectId", "type": "string"},
                    {"name": "name", "type": "string"},
                    {"name": "description", "type": "string"},
                    {"name": "ipfsHash", "type": "string"},
                    {"name": "category", "type": "string"}
                ],
                "outputs": [{"name": "", "type": "bool"}],
                "stateMutability": "nonpayable"
            },
            {
                "type": "function",
                "name": "getMVP",
                "inputs": [{"name": "projectId", "type": "string"}],
                "outputs": [
                    {"name": "name", "type": "string"},
                    {"name": "description", "type": "string"},
                    {"name": "ipfsHash", "type": "string"},
                    {"name": "category", "type": "string"},
                    {"name": "creator", "type": "address"},
                    {"name": "timestamp", "type": "uint256"},
                    {"name": "active", "type": "bool"}
                ],
                "stateMutability": "view"
            },
            {
                "type": "function",
                "name": "updateMVP",
                "inputs": [
                    {"name": "projectId", "type": "string"},
                    {"name": "name", "type": "string"},
                    {"name": "description", "type": "string"},
                    {"name": "ipfsHash", "type": "string"}
                ],
                "outputs": [{"name": "", "type": "bool"}],
                "stateMutability": "nonpayable"
            },
            {
                "type": "function",
                "name": "deactivateMVP",
                "inputs": [{"name": "projectId", "type": "string"}],
                "outputs": [{"name": "", "type": "bool"}],
                "stateMutability": "nonpayable"
            },
            {
                "type": "function",
                "name": "getAllMVPs",
                "inputs": [],
                "outputs": [{"name": "", "type": "string[]"}],
                "stateMutability": "view"
            },
            {
                "type": "event",
                "name": "MVPRegistered",
                "inputs": [
                    {"name": "projectId", "type": "string", "indexed": True},
                    {"name": "creator", "type": "address", "indexed": True},
                    {"name": "name", "type": "string"},
                    {"name": "category", "type": "string"}
                ]
            },
            {
                "type": "event",
                "name": "MVPUpdated",
                "inputs": [
                    {"name": "projectId", "type": "string", "indexed": True},
                    {"name": "updater", "type": "address", "indexed": True}
                ]
            }
        ]
    
    def _get_project_funding_abi(self) -> List[Dict[str, Any]]:
        """Get Project Funding contract ABI"""
        return [
            {
                "type": "constructor",
                "inputs": [{"name": "tokenAddress", "type": "address"}],
                "stateMutability": "nonpayable"
            },
            {
                "type": "function",
                "name": "createFundingRound",
                "inputs": [
                    {"name": "projectId", "type": "string"},
                    {"name": "goal", "type": "uint256"},
                    {"name": "duration", "type": "uint256"},
                    {"name": "minContribution", "type": "uint256"}
                ],
                "outputs": [{"name": "", "type": "bool"}],
                "stateMutability": "nonpayable"
            },
            {
                "type": "function",
                "name": "contribute",
                "inputs": [
                    {"name": "projectId", "type": "string"},
                    {"name": "amount", "type": "uint256"}
                ],
                "outputs": [{"name": "", "type": "bool"}],
                "stateMutability": "payable"
            },
            {
                "type": "function",
                "name": "withdrawFunds",
                "inputs": [{"name": "projectId", "type": "string"}],
                "outputs": [{"name": "", "type": "bool"}],
                "stateMutability": "nonpayable"
            },
            {
                "type": "function",
                "name": "refundContribution",
                "inputs": [{"name": "projectId", "type": "string"}],
                "outputs": [{"name": "", "type": "bool"}],
                "stateMutability": "nonpayable"
            },
            {
                "type": "function",
                "name": "getFundingInfo",
                "inputs": [{"name": "projectId", "type": "string"}],
                "outputs": [
                    {"name": "goal", "type": "uint256"},
                    {"name": "raised", "type": "uint256"},
                    {"name": "contributorCount", "type": "uint256"},
                    {"name": "deadline", "type": "uint256"},
                    {"name": "active", "type": "bool"}
                ],
                "stateMutability": "view"
            },
            {
                "type": "event",
                "name": "FundingRoundCreated",
                "inputs": [
                    {"name": "projectId", "type": "string", "indexed": True},
                    {"name": "creator", "type": "address", "indexed": True},
                    {"name": "goal", "type": "uint256"},
                    {"name": "deadline", "type": "uint256"}
                ]
            },
            {
                "type": "event",
                "name": "ContributionMade",
                "inputs": [
                    {"name": "projectId", "type": "string", "indexed": True},
                    {"name": "contributor", "type": "address", "indexed": True},
                    {"name": "amount", "type": "uint256"}
                ]
            }
        ]
    
    def _get_reputation_system_abi(self) -> List[Dict[str, Any]]:
        """Get Reputation System contract ABI"""
        return [
            {
                "type": "constructor",
                "inputs": [],
                "stateMutability": "nonpayable"
            },
            {
                "type": "function",
                "name": "updateReputation",
                "inputs": [
                    {"name": "user", "type": "address"},
                    {"name": "projectId", "type": "string"},
                    {"name": "rating", "type": "uint8"},
                    {"name": "comment", "type": "string"}
                ],
                "outputs": [{"name": "", "type": "bool"}],
                "stateMutability": "nonpayable"
            },
            {
                "type": "function",
                "name": "getReputation",
                "inputs": [{"name": "user", "type": "address"}],
                "outputs": [
                    {"name": "score", "type": "uint256"},
                    {"name": "reviewCount", "type": "uint256"},
                    {"name": "averageRating", "type": "uint8"}
                ],
                "stateMutability": "view"
            },
            {
                "type": "function",
                "name": "getUserReviews",
                "inputs": [
                    {"name": "user", "type": "address"},
                    {"name": "offset", "type": "uint256"},
                    {"name": "limit", "type": "uint256"}
                ],
                "outputs": [
                    {"name": "projectIds", "type": "string[]"},
                    {"name": "ratings", "type": "uint8[]"},
                    {"name": "comments", "type": "string[]"},
                    {"name": "timestamps", "type": "uint256[]"}
                ],
                "stateMutability": "view"
            },
            {
                "type": "event",
                "name": "ReputationUpdated",
                "inputs": [
                    {"name": "user", "type": "address", "indexed": True},
                    {"name": "projectId", "type": "string", "indexed": True},
                    {"name": "rating", "type": "uint8"},
                    {"name": "newScore", "type": "uint256"}
                ]
            }
        ]
    
    def _get_data_marketplace_abi(self) -> List[Dict[str, Any]]:
        """Get Data Marketplace contract ABI"""
        return [
            {
                "type": "constructor",
                "inputs": [{"name": "tokenAddress", "type": "address"}],
                "stateMutability": "nonpayable"
            },
            {
                "type": "function",
                "name": "listData",
                "inputs": [
                    {"name": "dataId", "type": "string"},
                    {"name": "ipfsHash", "type": "string"},
                    {"name": "price", "type": "uint256"},
                    {"name": "metadata", "type": "string"}
                ],
                "outputs": [{"name": "", "type": "bool"}],
                "stateMutability": "nonpayable"
            },
            {
                "type": "function",
                "name": "purchaseData",
                "inputs": [
                    {"name": "dataId", "type": "string"},
                    {"name": "price", "type": "uint256"}
                ],
                "outputs": [{"name": "", "type": "bool"}],
                "stateMutability": "payable"
            },
            {
                "type": "function",
                "name": "getDataInfo",
                "inputs": [{"name": "dataId", "type": "string"}],
                "outputs": [
                    {"name": "seller", "type": "address"},
                    {"name": "ipfsHash", "type": "string"},
                    {"name": "price", "type": "uint256"},
                    {"name": "metadata", "type": "string"},
                    {"name": "active", "type": "bool"}
                ],
                "stateMutability": "view"
            },
            {
                "type": "event",
                "name": "DataListed",
                "inputs": [
                    {"name": "dataId", "type": "string", "indexed": True},
                    {"name": "seller", "type": "address", "indexed": True},
                    {"name": "price", "type": "uint256"}
                ]
            },
            {
                "type": "event",
                "name": "DataPurchased",
                "inputs": [
                    {"name": "dataId", "type": "string", "indexed": True},
                    {"name": "buyer", "type": "address", "indexed": True},
                    {"name": "price", "type": "uint256"}
                ]
            }
        ]
    
    def _get_collaboration_dao_abi(self) -> List[Dict[str, Any]]:
        """Get Collaboration DAO contract ABI"""
        return [
            {
                "type": "constructor",
                "inputs": [
                    {"name": "name", "type": "string"},
                    {"name": "tokenAddress", "type": "address"},
                    {"name": "quorum", "type": "uint256"},
                    {"name": "votingPeriod", "type": "uint256"}
                ],
                "stateMutability": "nonpayable"
            },
            {
                "type": "function",
                "name": "createProposal",
                "inputs": [
                    {"name": "title", "type": "string"},
                    {"name": "description", "type": "string"},
                    {"name": "targets", "type": "address[]"},
                    {"name": "values", "type": "uint256[]"},
                    {"name": "calldatas", "type": "bytes[]"}
                ],
                "outputs": [{"name": "", "type": "uint256"}],
                "stateMutability": "nonpayable"
            },
            {
                "type": "function",
                "name": "vote",
                "inputs": [
                    {"name": "proposalId", "type": "uint256"},
                    {"name": "support", "type": "bool"}
                ],
                "outputs": [{"name": "", "type": "bool"}],
                "stateMutability": "nonpayable"
            },
            {
                "type": "function",
                "name": "execute",
                "inputs": [{"name": "proposalId", "type": "uint256"}],
                "outputs": [{"name": "", "type": "bool"}],
                "stateMutability": "nonpayable"
            },
            {
                "type": "function",
                "name": "getProposal",
                "inputs": [{"name": "proposalId", "type": "uint256"}],
                "outputs": [
                    {"name": "title", "type": "string"},
                    {"name": "description", "type": "string"},
                    {"name": "creator", "type": "address"},
                    {"name": "forVotes", "type": "uint256"},
                    {"name": "againstVotes", "type": "uint256"},
                    {"name": "deadline", "type": "uint256"},
                    {"name": "executed", "type": "bool"}
                ],
                "stateMutability": "view"
            },
            {
                "type": "event",
                "name": "ProposalCreated",
                "inputs": [
                    {"name": "proposalId", "type": "uint256", "indexed": True},
                    {"name": "creator", "type": "address", "indexed": True},
                    {"name": "title", "type": "string"}
                ]
            },
            {
                "type": "event",
                "name": "VoteCast",
                "inputs": [
                    {"name": "proposalId", "type": "uint256", "indexed": True},
                    {"name": "voter", "type": "address", "indexed": True},
                    {"name": "support", "type": "bool"}
                ]
            }
        ]
    
    def _get_intellectual_property_abi(self) -> List[Dict[str, Any]]:
        """Get Intellectual Property contract ABI"""
        return [
            {
                "type": "constructor",
                "inputs": [],
                "stateMutability": "nonpayable"
            },
            {
                "type": "function",
                "name": "registerIP",
                "inputs": [
                    {"name": "ipId", "type": "string"},
                    {"name": "title", "type": "string"},
                    {"name": "description", "type": "string"},
                    {"name": "ipfsHash", "type": "string"},
                    {"name": "licenseType", "type": "uint8"}
                ],
                "outputs": [{"name": "", "type": "bool"}],
                "stateMutability": "nonpayable"
            },
            {
                "type": "function",
                "name": "transferIP",
                "inputs": [
                    {"name": "ipId", "type": "string"},
                    {"name": "to", "type": "address"}
                ],
                "outputs": [{"name": "", "type": "bool"}],
                "stateMutability": "nonpayable"
            },
            {
                "type": "function",
                "name": "licenseIP",
                "inputs": [
                    {"name": "ipId", "type": "string"},
                    {"name": "licensee", "type": "address"},
                    {"name": "terms", "type": "string"},
                    {"name": "royalty", "type": "uint256"}
                ],
                "outputs": [{"name": "", "type": "bool"}],
                "stateMutability": "nonpayable"
            },
            {
                "type": "function",
                "name": "getIPInfo",
                "inputs": [{"name": "ipId", "type": "string"}],
                "outputs": [
                    {"name": "title", "type": "string"},
                    {"name": "description", "type": "string"},
                    {"name": "ipfsHash", "type": "string"},
                    {"name": "owner", "type": "address"},
                    {"name": "licenseType", "type": "uint8"},
                    {"name": "timestamp", "type": "uint256"}
                ],
                "stateMutability": "view"
            },
            {
                "type": "event",
                "name": "IPRegistered",
                "inputs": [
                    {"name": "ipId", "type": "string", "indexed": True},
                    {"name": "owner", "type": "address", "indexed": True},
                    {"name": "title", "type": "string"}
                ]
            }
        ]
    
    def create_account(self, private_key: Optional[str] = None) -> Account:
        """Create or load blockchain account"""
        if private_key:
            self.account = Account.from_key(private_key)
        else:
            self.account = Account.create()
        
        logger.info(f"Created account: {self.account.address}")
        return self.account
    
    def get_balance(self, address: Optional[str] = None) -> float:
        """Get ETH balance"""
        addr = address or self.account.address
        try:
            balance_wei = self.w3.eth.get_balance(addr)
            return self.w3.from_wei(balance_wei, 'ether')
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            return 0.0
    
    async def deploy_contract(self, contract_type: ContractType, constructor_args: List[Any] = None) -> SmartContract:
        """Deploy smart contract"""
        try:
            if not self.account:
                raise ValueError("No account available")
            
            # Get ABI and bytecode
            abi = self.contract_abis[contract_type]
            bytecode = self._get_contract_bytecode(contract_type)
            
            # Create contract instance
            contract = self.w3.eth.contract(abi=abi, bytecode=bytecode)
            
            # Build transaction
            constructor_args = constructor_args or []
            transaction = contract.constructor(*constructor_args).build_transaction({
                'from': self.account.address,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
                'gas': self.config.max_gas_limit,
                'gasPrice': self.w3.to_wei(self.config.gas_price_gwei, 'gwei')
            })
            
            # Sign transaction
            signed_txn = self.w3.eth.account.sign_transaction(transaction, self.account.key)
            
            # Send transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # Wait for confirmation
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(
                tx_hash, 
                timeout=120, 
                poll_latency=2
            )
            
            if tx_receipt.status == 1:
                # Create contract object
                deployed_contract = self.w3.eth.contract(
                    address=tx_receipt.contractAddress,
                    abi=abi
                )
                
                # Store contract info
                smart_contract = SmartContract(
                    address=tx_receipt.contractAddress,
                    abi=abi,
                    bytecode=bytecode,
                    contract_type=contract_type,
                    deployed_at=datetime.now(),
                    deployer=self.account.address,
                    transaction_hash=tx_hash.hex(),
                    block_number=tx_receipt.blockNumber,
                    gas_used=tx_receipt.gasUsed
                )
                
                self.contracts[contract_type.value] = smart_contract
                
                logger.info(f"Deployed {contract_type.value} at {tx_receipt.contractAddress}")
                return smart_contract
            else:
                raise Exception("Contract deployment failed")
                
        except Exception as e:
            logger.error(f"Error deploying contract: {e}")
            raise
    
    def _get_contract_bytecode(self, contract_type: ContractType) -> str:
        """Get contract bytecode (placeholder)"""
        # In production, load from compiled contracts
        return "0x608060405234801561001057600080fd5b50"
    
    async def store_on_ipfs(self, data: Dict[str, Any]) -> str:
        """Store data on IPFS"""
        try:
            if not self.ipfs_client:
                raise Exception("IPFS client not available")
            
            # Convert data to JSON
            json_data = json.dumps(data, indent=2)
            
            # Add to IPFS
            result = self.ipfs_client.add_json(json_data)
            ipfs_hash = result['Hash']
            
            logger.info(f"Stored data on IPFS: {ipfs_hash}")
            return ipfs_hash
            
        except Exception as e:
            logger.error(f"Error storing on IPFS: {e}")
            raise
    
    async def retrieve_from_ipfs(self, ipfs_hash: str) -> Dict[str, Any]:
        """Retrieve data from IPFS"""
        try:
            if not self.ipfs_client:
                raise Exception("IPFS client not available")
            
            # Get from IPFS
            json_data = self.ipfs_client.get_json(ipfs_hash)
            data = json.loads(json_data)
            
            logger.info(f"Retrieved data from IPFS: {ipfs_hash}")
            return data
            
        except Exception as e:
            logger.error(f"Error retrieving from IPFS: {e}")
            raise
    
    async def register_mvp(self, project_data: Dict[str, Any]) -> str:
        """Register MVP on blockchain"""
        try:
            contract = self.contracts.get(ContractType.MVP_REGISTRY.value)
            if not contract:
                raise Exception("MVP Registry contract not deployed")
            
            # Store project data on IPFS
            ipfs_hash = await self.store_on_ipfs(project_data)
            
            # Create contract instance
            mvp_contract = self.w3.eth.contract(
                address=contract.address,
                abi=contract.abi
            )
            
            # Build transaction
            transaction = mvp_contract.functions.registerMVP(
                project_data['id'],
                project_data['name'],
                project_data['description'],
                ipfs_hash,
                project_data.get('category', 'general')
            ).build_transaction({
                'from': self.account.address,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
                'gas': 200000,
                'gasPrice': self.w3.to_wei(self.config.gas_price_gwei, 'gwei')
            })
            
            # Sign and send transaction
            signed_txn = self.w3.eth.account.sign_transaction(transaction, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # Wait for confirmation
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if tx_receipt.status == 1:
                logger.info(f"MVP registered: {project_data['id']}")
                return tx_hash.hex()
            else:
                raise Exception("MVP registration failed")
                
        except Exception as e:
            logger.error(f"Error registering MVP: {e}")
            raise
    
    async def get_mvp(self, project_id: str) -> Dict[str, Any]:
        """Get MVP from blockchain"""
        try:
            contract = self.contracts.get(ContractType.MVP_REGISTRY.value)
            if not contract:
                raise Exception("MVP Registry contract not deployed")
            
            # Create contract instance
            mvp_contract = self.w3.eth.contract(
                address=contract.address,
                abi=contract.abi
            )
            
            # Call contract
            result = mvp_contract.functions.getMVP(project_id).call()
            
            # Retrieve full data from IPFS
            full_data = await self.retrieve_from_ipfs(result[2])  # ipfsHash
            
            # Combine blockchain data with IPFS data
            mvp_data = {
                'id': project_id,
                'name': result[0],
                'description': result[1],
                'ipfsHash': result[2],
                'category': result[3],
                'creator': result[4],
                'timestamp': result[5],
                'active': result[6],
                'fullData': full_data
            }
            
            return mvp_data
            
        except Exception as e:
            logger.error(f"Error getting MVP: {e}")
            raise
    
    async def create_funding_round(self, project_id: str, goal_eth: float, 
                                  duration_days: int, min_contribution_eth: float) -> str:
        """Create funding round for project"""
        try:
            contract = self.contracts.get(ContractType.PROJECT_FUNDING.value)
            if not contract:
                raise Exception("Project Funding contract not deployed")
            
            # Create contract instance
            funding_contract = self.w3.eth.contract(
                address=contract.address,
                abi=contract.abi
            )
            
            # Convert to wei
            goal_wei = self.w3.to_wei(goal_eth, 'ether')
            min_contribution_wei = self.w3.to_wei(min_contribution_eth, 'ether')
            duration_seconds = duration_days * 24 * 3600
            
            # Build transaction
            transaction = funding_contract.functions.createFundingRound(
                project_id,
                goal_wei,
                duration_seconds,
                min_contribution_wei
            ).build_transaction({
                'from': self.account.address,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
                'gas': 300000,
                'gasPrice': self.w3.to_wei(self.config.gas_price_gwei, 'gwei')
            })
            
            # Sign and send transaction
            signed_txn = self.w3.eth.account.sign_transaction(transaction, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # Wait for confirmation
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if tx_receipt.status == 1:
                logger.info(f"Funding round created for {project_id}")
                return tx_hash.hex()
            else:
                raise Exception("Funding round creation failed")
                
        except Exception as e:
            logger.error(f"Error creating funding round: {e}")
            raise
    
    async def contribute_to_project(self, project_id: str, amount_eth: float) -> str:
        """Contribute to project funding"""
        try:
            contract = self.contracts.get(ContractType.PROJECT_FUNDING.value)
            if not contract:
                raise Exception("Project Funding contract not deployed")
            
            # Create contract instance
            funding_contract = self.w3.eth.contract(
                address=contract.address,
                abi=contract.abi
            )
            
            # Convert to wei
            amount_wei = self.w3.to_wei(amount_eth, 'ether')
            
            # Build transaction
            transaction = funding_contract.functions.contribute(
                project_id,
                amount_wei
            ).build_transaction({
                'from': self.account.address,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
                'gas': 200000,
                'gasPrice': self.w3.to_wei(self.config.gas_price_gwei, 'gwei'),
                'value': amount_wei
            })
            
            # Sign and send transaction
            signed_txn = self.w3.eth.account.sign_transaction(transaction, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # Wait for confirmation
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if tx_receipt.status == 1:
                logger.info(f"Contributed {amount_eth} ETH to {project_id}")
                return tx_hash.hex()
            else:
                raise Exception("Contribution failed")
                
        except Exception as e:
            logger.error(f"Error contributing to project: {e}")
            raise
    
    async def update_reputation(self, user_address: str, project_id: str, 
                             rating: int, comment: str) -> str:
        """Update user reputation"""
        try:
            contract = self.contracts.get(ContractType.REPUTATION_SYSTEM.value)
            if not contract:
                raise Exception("Reputation System contract not deployed")
            
            # Create contract instance
            reputation_contract = self.w3.eth.contract(
                address=contract.address,
                abi=contract.abi
            )
            
            # Validate rating
            if rating < 1 or rating > 5:
                raise ValueError("Rating must be between 1 and 5")
            
            # Build transaction
            transaction = reputation_contract.functions.updateReputation(
                user_address,
                project_id,
                rating,
                comment
            ).build_transaction({
                'from': self.account.address,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
                'gas': 150000,
                'gasPrice': self.w3.to_wei(self.config.gas_price_gwei, 'gwei')
            })
            
            # Sign and send transaction
            signed_txn = self.w3.eth.account.sign_transaction(transaction, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # Wait for confirmation
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if tx_receipt.status == 1:
                logger.info(f"Updated reputation for {user_address}")
                return tx_hash.hex()
            else:
                raise Exception("Reputation update failed")
                
        except Exception as e:
            logger.error(f"Error updating reputation: {e}")
            raise
    
    async def get_reputation(self, user_address: str) -> Dict[str, Any]:
        """Get user reputation"""
        try:
            contract = self.contracts.get(ContractType.REPUTATION_SYSTEM.value)
            if not contract:
                raise Exception("Reputation System contract not deployed")
            
            # Create contract instance
            reputation_contract = self.w3.eth.contract(
                address=contract.address,
                abi=contract.abi
            )
            
            # Call contract
            result = reputation_contract.functions.getReputation(user_address).call()
            
            reputation_data = {
                'user': user_address,
                'score': result[0],
                'reviewCount': result[1],
                'averageRating': result[2]
            }
            
            return reputation_data
            
        except Exception as e:
            logger.error(f"Error getting reputation: {e}")
            raise
    
    def create_decentralized_identity(self, user_id: str) -> DecentralizedIdentity:
        """Create decentralized identity"""
        try:
            # Generate key pair
            private_key = ec.generate_private_key(ec.SECP256R1())
            public_key = private_key.public_key()
            
            # Create DID
            did = f"did:ethr:{self.config.chain_id}:{user_id}"
            
            # Create verification methods
            verification_methods = [
                {
                    "id": f"{did}#key-1",
                    "type": "EcdsaSecp256k1VerificationKey2019",
                    "controller": did,
                    "publicKeyHex": public_key.public_bytes(
                        Encoding.X962, 
                        PublicFormat.CompressedPoint
                    ).hex()
                }
            ]
            
            # Create services
            services = [
                {
                    "id": f"{did}#hub",
                    "type": "IdentityHub",
                    "serviceEndpoint": f"https://hub.asmblr.com/{user_id}"
                }
            ]
            
            # Create identity
            identity = DecentralizedIdentity(
                did=did,
                public_key=public_key.public_bytes(
                    Encoding.X962, 
                    PublicFormat.CompressedPoint
                ).hex(),
                verification_methods=verification_methods,
                services=services,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            self.identities[user_id] = identity
            
            logger.info(f"Created DID: {did}")
            return identity
            
        except Exception as e:
            logger.error(f"Error creating decentralized identity: {e}")
            raise
    
    def sign_message(self, message: str) -> str:
        """Sign message with private key"""
        try:
            if not self.account:
                raise ValueError("No account available")
            
            # Create message hash
            message_hash = encode_defunct(text=message)
            
            # Sign message
            signed_message = self.w3.eth.account.sign_message(message_hash, self.account.key)
            
            return signed_message.signature.hex()
            
        except Exception as e:
            logger.error(f"Error signing message: {e}")
            raise
    
    def verify_signature(self, message: str, signature: str, address: str) -> bool:
        """Verify message signature"""
        try:
            # Create message hash
            message_hash = encode_defunct(text=message)
            
            # Recover address
            recovered_address = self.w3.eth.account.recover_message(message_hash, signature=signature)
            
            return recovered_address.lower() == address.lower()
            
        except Exception as e:
            logger.error(f"Error verifying signature: {e}")
            return False

# Global blockchain manager
blockchain_manager = None

async def initialize_blockchain(network: BlockchainNetwork = BlockchainNetwork.ETHEREUM_SEPOLIA):
    """Initialize blockchain manager"""
    global blockchain_manager
    
    configs = {
        BlockchainNetwork.ETHEREUM_MAINNET: BlockchainConfig(
            network=BlockchainNetwork.ETHEREUM_MAINNET,
            rpc_url="https://mainnet.infura.io/v3/YOUR_PROJECT_ID",
            chain_id=1,
            gas_price_gwei=20.0,
            max_gas_limit=8000000,
            block_time_seconds=12,
            confirmation_blocks=12
        ),
        BlockchainNetwork.ETHEREUM_SEPOLIA: BlockchainConfig(
            network=BlockchainNetwork.ETHEREUM_SEPOLIA,
            rpc_url="https://sepolia.infura.io/v3/YOUR_PROJECT_ID",
            chain_id=11155111,
            gas_price_gwei=20.0,
            max_gas_limit=8000000,
            block_time_seconds=12,
            confirmation_blocks=3
        ),
        BlockchainNetwork.POLYGON: BlockchainConfig(
            network=BlockchainNetwork.POLYGON,
            rpc_url="https://polygon-rpc.com",
            chain_id=137,
            gas_price_gwei=30.0,
            max_gas_limit=20000000,
            block_time_seconds=2,
            confirmation_blocks=5
        ),
        BlockchainNetwork.LOCAL_GETH: BlockchainConfig(
            network=BlockchainNetwork.LOCAL_GETH,
            rpc_url="http://localhost:8545",
            chain_id=1337,
            gas_price_gwei=1.0,
            max_gas_limit=8000000,
            block_time_seconds=15,
            confirmation_blocks=1
        )
    }
    
    config = configs.get(network, configs[BlockchainNetwork.LOCAL_GETH])
    blockchain_manager = BlockchainManager(config)
    
    # Deploy contracts
    await blockchain_manager.deploy_contract(ContractType.MVP_REGISTRY, ["Asmblr MVP Registry", "ASM"])
    await blockchain_manager.deploy_contract(ContractType.PROJECT_FUNDING, ["0x0000000000000000000000000000000000000000"])
    await blockchain_manager.deploy_contract(ContractType.REPUTATION_SYSTEM, [])
    await blockchain_manager.deploy_contract(ContractType.DATA_MARKETPLACE, ["0x0000000000000000000000000000000000000000"])
    await blockchain_manager.deploy_contract(ContractType.COLLABORATION_DAO, ["Asmblr DAO", "0x0000000000000000000000000000000000000000", 51, 604800])
    await blockchain_manager.deploy_contract(ContractType.INTELLECTUAL_PROPERTY, [])
    
    logger.info("Blockchain initialized with all contracts deployed")

# API endpoints
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/blockchain", tags=["blockchain"])

class MVPRegistrationRequest(BaseModel):
    id: str
    name: str
    description: str
    category: str
    tech_stack: Dict[str, List[str]]
    features: List[str]
    team_members: List[str]

class FundingRoundRequest(BaseModel):
    project_id: str
    goal_eth: float
    duration_days: int
    min_contribution_eth: float

class ContributionRequest(BaseModel):
    project_id: str
    amount_eth: float

class ReputationUpdateRequest(BaseModel):
    user_address: str
    project_id: str
    rating: int
    comment: str

@router.post("/mvp/register")
async def register_mvp(request: MVPRegistrationRequest):
    """Register MVP on blockchain"""
    try:
        if not blockchain_manager:
            raise HTTPException(status_code=500, detail="Blockchain not initialized")
        
        project_data = {
            'id': request.id,
            'name': request.name,
            'description': request.description,
            'category': request.category,
            'tech_stack': request.tech_stack,
            'features': request.features,
            'team_members': request.team_members,
            'created_at': datetime.now().isoformat()
        }
        
        tx_hash = await blockchain_manager.register_mvp(project_data)
        return {"transaction_hash": tx_hash, "status": "registered"}
    except Exception as e:
        logger.error(f"Error registering MVP: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/mvp/{project_id}")
async def get_mvp(project_id: str):
    """Get MVP from blockchain"""
    try:
        if not blockchain_manager:
            raise HTTPException(status_code=500, detail="Blockchain not initialized")
        
        mvp_data = await blockchain_manager.get_mvp(project_id)
        return mvp_data
    except Exception as e:
        logger.error(f"Error getting MVP: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/funding/create")
async def create_funding_round(request: FundingRoundRequest):
    """Create funding round"""
    try:
        if not blockchain_manager:
            raise HTTPException(status_code=500, detail="Blockchain not initialized")
        
        tx_hash = await blockchain_manager.create_funding_round(
            request.project_id,
            request.goal_eth,
            request.duration_days,
            request.min_contribution_eth
        )
        return {"transaction_hash": tx_hash, "status": "funding_round_created"}
    except Exception as e:
        logger.error(f"Error creating funding round: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/funding/contribute")
async def contribute_to_project(request: ContributionRequest):
    """Contribute to project funding"""
    try:
        if not blockchain_manager:
            raise HTTPException(status_code=500, detail="Blockchain not initialized")
        
        tx_hash = await blockchain_manager.contribute_to_project(
            request.project_id,
            request.amount_eth
        )
        return {"transaction_hash": tx_hash, "status": "contribution_made"}
    except Exception as e:
        logger.error(f"Error contributing to project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reputation/update")
async def update_reputation(request: ReputationUpdateRequest):
    """Update user reputation"""
    try:
        if not blockchain_manager:
            raise HTTPException(status_code=500, detail="Blockchain not initialized")
        
        tx_hash = await blockchain_manager.update_reputation(
            request.user_address,
            request.project_id,
            request.rating,
            request.comment
        )
        return {"transaction_hash": tx_hash, "status": "reputation_updated"}
    except Exception as e:
        logger.error(f"Error updating reputation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reputation/{user_address}")
async def get_reputation(user_address: str):
    """Get user reputation"""
    try:
        if not blockchain_manager:
            raise HTTPException(status_code=500, detail="Blockchain not initialized")
        
        reputation = await blockchain_manager.get_reputation(user_address)
        return reputation
    except Exception as e:
        logger.error(f"Error getting reputation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/identity/create")
async def create_identity(user_id: str):
    """Create decentralized identity"""
    try:
        if not blockchain_manager:
            raise HTTPException(status_code=500, detail="Blockchain not initialized")
        
        identity = blockchain_manager.create_decentralized_identity(user_id)
        return asdict(identity)
    except Exception as e:
        logger.error(f"Error creating identity: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/balance/{address}")
async def get_balance(address: str):
    """Get ETH balance"""
    try:
        if not blockchain_manager:
            raise HTTPException(status_code=500, detail="Blockchain not initialized")
        
        balance = blockchain_manager.get_balance(address)
        return {"address": address, "balance_eth": balance}
    except Exception as e:
        logger.error(f"Error getting balance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sign")
async def sign_message(message: str):
    """Sign message"""
    try:
        if not blockchain_manager:
            raise HTTPException(status_code=500, detail="Blockchain not initialized")
        
        signature = blockchain_manager.sign_message(message)
        return {"message": message, "signature": signature}
    except Exception as e:
        logger.error(f"Error signing message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/verify")
async def verify_signature(message: str, signature: str, address: str):
    """Verify message signature"""
    try:
        if not blockchain_manager:
            raise HTTPException(status_code=500, detail="Blockchain not initialized")
        
        is_valid = blockchain_manager.verify_signature(message, signature, address)
        return {"message": message, "signature": signature, "address": address, "valid": is_valid}
    except Exception as e:
        logger.error(f"Error verifying signature: {e}")
        raise HTTPException(status_code=500, detail=str(e))
