"""
Advanced Database Query Optimizer for Asmblr
High-performance database operations with query optimization and connection pooling
"""

import asyncio
import time
import json
import hashlib
import re
from typing import Dict, Any, Optional, List, Union, Callable, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from contextlib import asynccontextmanager
import asyncpg
import aiomysql
import motor.motor_asyncio
from loguru import logger
import psutil

class QueryType(Enum):
    """Query types for optimization"""
    SELECT = "select"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    CREATE = "create"
    DROP = "drop"
    ALTER = "alter"

class OptimizationLevel(Enum):
    """Query optimization levels"""
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

@dataclass
class QueryPlan:
    """Query execution plan"""
    query: str
    estimated_cost: float
    estimated_rows: int
    execution_time: float
    indexes_used: List[str]
    tables_scanned: List[str]
    optimization_level: OptimizationLevel
    recommendations: List[str]
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class QueryMetrics:
    """Query performance metrics"""
    query_hash: str
    execution_count: int = 0
    total_time: float = 0.0
    avg_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    success_count: int = 0
    error_count: int = 0
    last_executed: Optional[datetime] = None
    optimization_applied: bool = False

class DatabaseOptimizer:
    """Advanced database query optimizer"""
    
    def __init__(self, db_type: str = "postgresql"):
        self.db_type = db_type.lower()
        self.query_plans = {}
        self.query_metrics = {}
        self.index_recommendations = {}
        
        # Optimization settings
        self.query_timeout = 30.0
        self.max_query_time = 10.0
        self.enable_query_caching = True
        self.enable_auto_indexing = True
        self.enable_query_rewrite = True
        
        # Performance thresholds
        self.slow_query_threshold = 1.0
        self.expensive_query_threshold = 5.0
        self.high_cost_threshold = 1000.0
        
        # Connection pools
        self.connection_pools = {}
        
        # Query patterns
        self.query_patterns = {
            'select_single': re.compile(r'SELECT\s+\*\*\s+FROM\s+\w+\s+WHERE\s+\w+\s*=\s*'),
            'select_join': re.compile(r'SELECT\s+.*\s+FROM\s+.*\s+JOIN\s+.*'),
            'select_aggregate': re.compile(r'SELECT\s+.*\s+COUNT\(|SUM\(|AVG\(|MIN\(|MAX\('),
            'insert_batch': re.compile(r'INSERT\s+INTO\s+.*\s+VALUES\s*\(.*\),\s*\)'),
            'update_batch': re.compile(r'UPDATE\s+.*\s+SET\s+.*\s+WHERE\s+.*'),
            'delete_batch': re.compile(r'DELETE\s+FROM\s+.*\s+WHERE\s+.*')
        }
        
        # Index patterns
        self.index_patterns = {
            'where_clause': re.compile(r'WHERE\s+(\w+)\s*='),
            'join_clause': re.compile(r'JOIN\s+(\w+)\s+ON'),
            'order_by': re.compile(r'ORDER\s+BY\s+(\w+)'),
            'group_by': re.compile(r'GROUP\s+BY\s+(\w+)'),
            'subquery': re.compile(r'\(\s*SELECT\s+.*\s*\)')
        }
    
    async def initialize(self):
        """Initialize the database optimizer"""
        try:
            logger.info(f"Initializing database optimizer for {self.db_type}")
            
            # Initialize connection pools
            await self._initialize_connection_pools()
            
            # Load existing query metrics
            await self._load_query_metrics()
            
            # Start background optimization
            await self.start_background_optimization()
            
            logger.info("Database optimizer initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database optimizer: {e}")
            raise
    
    async def _initialize_connection_pools(self):
        """Initialize database connection pools"""
        if self.db_type == "postgresql":
            self.connection_pools['postgresql'] = await self._create_postgresql_pool()
        elif self.db_type == "mysql":
            self.connection_pools['mysql'] = await self._create_mysql_pool()
        elif self.db_type == "mongodb":
            self.connection_pools['mongodb'] = await self._create_mongodb_pool()
    
    async def _create_postgresql_pool(self):
        """Create PostgreSQL connection pool"""
        return await asyncpg.create_pool(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME", "asmblr"),
            min_size=5,
            max_size=20,
            command_timeout=30,
            server_settings={
                'application_name': 'asmblr_optimizer',
                'jit': 'off',
                'work_mem': '256MB',
                'maintenance_work_mem': '64MB',
                'effective_cache_size': '1GB'
            }
        )
    
    async def _create_mysql_pool(self):
        """Create MySQL connection pool"""
        return await aiomysql.create_pool(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD"),
            db=os.getenv("DB_NAME", "asmblr"),
            minsize=5,
            maxsize=20,
            autocommit=True,
            sql_mode="STRICT_TRANS_TABLES",
            init_command="SET SESSION sql_mode='STRICT_TRANS_TABLES'"
        )
    
    async def _create_mongodb_pool(self):
        """Create MongoDB connection pool"""
        return motor.motor_asyncio.AsyncIOMotorClient(
            f"mongodb://{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '27017')}",
            maxPoolSize=20,
            minPoolSize=5,
            serverSelectionTimeoutMS=5000,
            socketTimeoutMS=30000,
            connectTimeoutMS=10000
        )
    
    async def optimize_query(self, query: str, params: Optional[Tuple] = None) -> str:
        """Optimize a database query"""
        try:
            query_hash = self._generate_query_hash(query)
            
            # Check cache
            if self.enable_query_caching and query_hash in self.query_plans:
                plan = self.query_plans[query_hash]
                if plan.optimization_applied:
                    return plan.query
            
            # Parse and analyze query
            query_type = self._detect_query_type(query)
            
            # Apply optimizations based on query type
            optimized_query = query
            
            if query_type == QueryType.SELECT:
                optimized_query = await self._optimize_select_query(query)
            elif query_type == QueryType.INSERT:
                optimized_query = await self._optimize_insert_query(query)
            elif query_type == QueryType.UPDATE:
                optimized_query = await self._optimize_update_query(query)
            elif query_type == QueryType.DELETE:
                optimized_query = await self._optimize_delete_query(query)
            
            # Generate execution plan
            plan = await self._generate_execution_plan(optimized_query)
            
            # Cache the plan
            if self.enable_query_caching:
                self.query_plans[query_hash] = plan
            
            return optimized_query
            
        except Exception as e:
            logger.error(f"Query optimization error: {e}")
            return query
    
    async def _optimize_select_query(self, query: str) -> str:
        """Optimize SELECT query"""
        try:
            optimized = query
            
            # Add LIMIT if not present for large tables
            if 'LIMIT' not in optimized.upper() and 'WHERE' in optimized.upper():
                optimized += ' LIMIT 1000'
            
            # Optimize JOIN order
            if 'JOIN' in optimized.upper():
                optimized = self._optimize_join_order(optimized)
            
            # Add appropriate indexes hints
            if self.enable_auto_indexing:
                optimized = self._add_index_hints(optimized)
            
            return optimized
            
        except Exception as e:
            logger.error(f"SELECT optimization error: {e}")
            return query
    
    async def _optimize_insert_query(self, query: str) -> str:
        """Optimize INSERT query"""
        try:
            optimized = query
            
            # Use batch inserts for multiple values
            if 'VALUES' in optimized.upper() and 'VALUES' not in optimized.upper():
                # Single row insert, check if can be batched
                pass
            
            # Add ON CONFLICT handling for PostgreSQL
            if self.db_type == "postgresql" and 'ON CONFLICT' not in optimized.upper():
                table_match = re.search(r'INSERT\s+INTO\s+(\w+)', optimized, re.IGNORECASE)
                if table_match:
                    table_name = table_match.group(1)
                    optimized += f" ON CONFLICT ({table_name}_pkey) DO NOTHING"
            
            return optimized
            
        except Exception as e:
            logger.error(f"INSERT optimization error: {e}")
            return query
    
    async def _optimize_update_query(self, query: str) -> str:
        """Optimize UPDATE query"""
        try:
            optimized = query
            
            # Add LIMIT if not present
            if 'LIMIT' not in optimized.upper() and 'WHERE' in optimized.upper():
                optimized += ' LIMIT 1000'
            
            return optimized
            
        except Exception as e:
            logger.error(f"UPDATE optimization error: {e}")
            return query
    
    async def _optimize_delete_query(self, query: str) -> str:
        """Optimize DELETE query"""
        try:
            optimized = query
            
            # Add LIMIT if not present
            if 'LIMIT' not in optimized.upper():
                optimized += ' LIMIT 1000'
            
            return optimized
            
        except Exception as e:
            logger.error(f"DELETE optimization error: {e}")
            return query
    
    def _optimize_join_order(self, query: str) -> str:
        """Optimize JOIN order based on table sizes"""
        try:
            # Extract tables from JOIN clauses
            join_matches = re.findall(r'JOIN\s+(\w+)\s+ON', query, re.IGNORECASE)
            
            if len(join_matches) <= 1:
                return query
            
            # Simple heuristic: put smaller tables first
            # In practice, you'd query actual table sizes
            tables = [match.group(1) for match in join_matches]
            
            # Reorder joins (simplified)
            tables.sort()  # Sort alphabetically for now
            
            # Rebuild query with optimized join order
            parts = query.split('JOIN')
            new_parts = [parts[0]]  # Keep first part
            
            for i, table in enumerate(tables):
                for part in parts[1:]:
                    if table.lower() in part.lower():
                        new_parts.append(part)
                        break
            
            return 'JOIN'.join(new_parts)
            
        except Exception as e:
            logger.error(f"JOIN order optimization error: {e}")
            return query
    
    def _add_index_hints(self, query: str) -> str:
        """Add index hints to query"""
        try:
            # Extract WHERE clauses for index hints
            where_matches = list(self.index_patterns['where_clause'].finditer(query))
            
            if not where_matches:
                return query
            
            # Create index hints
            index_hints = []
            for match in where_matches:
                column = match.group(1)
                index_hints.append(f"USE INDEX (idx_{column})")
            
            if index_hints:
                # Insert hints after SELECT
                select_pos = query.upper().find('SELECT')
                if select_pos != -1:
                    hints_str = ', '.join(index_hints)
                    query = query[:select_pos + 6] + hints_str + query[select_pos + 6:]
            
            return query
            
        except Exception as e:
            logger.error(f"Index hints error: {e}")
            return query
    
    async def _generate_execution_plan(self, query: str) -> QueryPlan:
        """Generate query execution plan"""
        try:
            start_time = time.time()
            
            # For PostgreSQL, use EXPLAIN ANALYZE
            if self.db_type == "postgresql" and 'postgresql' in self.connection_pools:
                pool = self.connection_pools['postgresql']
                
                try:
                    plan_result = await pool.fetch(f"EXPLAIN ANALYZE {query}")
                    
                    if plan_result:
                        plan_text = plan_result[0]['QUERY PLAN']
                        
                        # Parse plan (simplified)
                        cost = self._extract_plan_cost(plan_text)
                        rows = self._extract_plan_rows(plan_text)
                        indexes = self._extract_plan_indexes(plan_text)
                        tables = self._extract_plan_tables(plan_text)
                        
                        plan = QueryPlan(
                            query=query,
                            estimated_cost=cost,
                            estimated_rows=rows,
                            execution_time=time.time() - start_time,
                            indexes_used=indexes,
                            tables_scanned=tables,
                            optimization_level=self._determine_optimization_level(cost, rows),
                            recommendations=self._generate_recommendations(plan_text),
                            metadata={'plan_text': plan_text}
                        )
                        
                        return plan
                
                except Exception as e:
                    logger.error(f"EXPLAIN ANALYZE error: {e}")
            
            # Fallback to basic plan
            return QueryPlan(
                query=query,
                estimated_cost=0.0,
                estimated_rows=0,
                execution_time=time.time() - start_time,
                indexes_used=[],
                tables_scanned=[],
                optimization_level=OptimizationLevel.BASIC,
                recommendations=[],
                metadata={}
            )
            
        except Exception as e:
            logger.error(f"Execution plan generation error: {e}")
            return QueryPlan(
                query=query,
                estimated_cost=0.0,
                estimated_rows=0,
                execution_time=0.0,
                indexes_used=[],
                tables_scanned=[],
                optimization_level=OptimizationLevel.BASIC,
                recommendations=[],
                metadata={}
            )
    
    def _extract_plan_cost(self, plan_text: str) -> float:
        """Extract cost from execution plan"""
        try:
            cost_match = re.search(r'cost=([\d.]+)', plan_text)
            if cost_match:
                return float(cost_match.group(1))
        except:
            pass
        return 0.0
    
    def _extract_plan_rows(self, plan_text: str) -> int:
        """Extract row count from execution plan"""
        try:
            rows_match = re.search(r'rows=([\d]+)', plan_text)
            if rows_match:
                return int(rows_match.group(1))
        except:
            pass
        return 0
    
    def _extract_plan_indexes(self, plan_text: str) -> List[str]:
        """Extract indexes used from execution plan"""
        try:
            indexes = []
            index_matches = re.findall(r'Using\s+(\w+)', plan_text)
            indexes.extend(index_matches)
            
            # Also look for Index Scan
            index_scans = re.findall(r'Index\s+Scan\s+using\s+(\w+)', plan_text)
            indexes.extend(index_scans)
            
            return list(set(indexes))
        except:
            return []
    
    def _extract_plan_tables(self, plan_text: str) -> List[str]:
        """Extract tables scanned from execution plan"""
        try:
            tables = []
            table_matches = re.findall(r'Seq\s+Scan\s+on\s+(\w+)', plan_text)
            tables.extend(table_matches)
            
            # Also look for other scan types
            scan_matches = re.findall(r'(\w+)\s+Scan', plan_text)
            for match in scan_matches:
                if match[0] not in ['Index', 'Bitmap', 'Hash', 'Gin', 'GiST']:
                    tables.append(match[0])
            
            return list(set(tables))
        except:
            return []
    
    def _determine_optimization_level(self, cost: float, rows: int) -> OptimizationLevel:
        """Determine optimization level based on cost and rows"""
        if cost > self.high_cost_threshold or rows > 100000:
            return OptimizationLevel.EXPERT
        elif cost > self.expensive_query_threshold or rows > 10000:
            return OptimizationLevel.ADVANCED
        elif cost > self.slow_query_threshold or rows > 1000:
            return OptimizationLevel.INTERMEDIATE
        else:
            return OptimizationLevel.BASIC
    
    def _generate_recommendations(self, plan_text: str) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []
        
        try:
            # Check for sequential scans
            if 'Seq Scan' in plan_text:
                recommendations.append("Consider adding indexes for frequently accessed columns")
            
            # Check for missing indexes
            if 'Index Scan' not in plan_text and 'WHERE' in plan_text:
                recommendations.append("Add indexes for WHERE clause columns")
            
            # Check for expensive operations
            if 'Sort' in plan_text and 'index' not in plan_text.lower():
                recommendations.append("Add indexes for ORDER BY columns")
            
            # Check for nested loops
            if 'Nested Loop' in plan_text:
                recommendations.append("Consider restructuring query to avoid nested loops")
            
            # Check for full table scans
            if 'Seq Scan' in plan_text and 'rows=' in plan_text:
                rows_match = re.search(r'rows=([\d]+)', plan_text)
                if rows_match and int(rows_match.group(1)) > 10000:
                    recommendations.append("Full table scan on large table - consider adding WHERE clause or indexes")
            
        except Exception as e:
            logger.error(f"Recommendation generation error: {e}")
        
        return recommendations
    
    def _detect_query_type(self, query: str) -> QueryType:
        """Detect query type"""
        query_upper = query.upper().strip()
        
        if query_upper.startswith('SELECT'):
            return QueryType.SELECT
        elif query_upper.startswith('INSERT'):
            return QueryType.INSERT
        elif query_upper.startswith('UPDATE'):
            return QueryType.UPDATE
        elif query_upper.startswith('DELETE'):
            return QueryType.DELETE
        elif query_upper.startswith('CREATE'):
            return QueryType.CREATE
        elif query_upper.startswith('DROP'):
            return QueryType.DROP
        elif query_upper.startswith('ALTER'):
            return QueryType.ALTER
        else:
            return QueryType.SELECT
    
    def _generate_query_hash(self, query: str) -> str:
        """Generate hash for query"""
        return hashlib.md5(query.encode()).hexdigest()
    
    @asynccontextmanager
    async def execute_query(self, query: str, params: Optional[Tuple] = None):
        """Execute optimized query with performance monitoring"""
        query_hash = self._generate_query_hash(query)
        start_time = time.time()
        
        try:
            # Get or create metrics
            if query_hash not in self.query_metrics:
                self.query_metrics[query_hash] = QueryMetrics(query_hash=query_hash)
            
            metrics = self.query_metrics[query_hash]
            metrics.execution_count += 1
            metrics.last_executed = datetime.now()
            
            # Optimize query
            optimized_query = await self.optimize_query(query, params)
            
            # Execute query
            if self.db_type == "postgresql" and 'postgresql' in self.connection_pools:
                pool = self.connection_pools['postgresql']
                result = await pool.fetch(optimized_query, *params or ())
            elif self.db_type == "mysql" and 'mysql' in self.connection_pools:
                pool = self.connection_pools['mysql']
                result = await pool.execute(optimized_query, params or ())
            elif self.db_type == "mongodb" and 'mongodb' in self.connection_pools:
                # MongoDB query execution would be different
                raise NotImplementedError("MongoDB query execution not implemented")
            else:
                raise ValueError(f"Unsupported database type: {self.db_type}")
            
            # Update metrics
            execution_time = time.time() - start_time
            metrics.total_time += execution_time
            metrics.avg_time = metrics.total_time / metrics.execution_count
            metrics.min_time = min(metrics.min_time, execution_time)
            metrics.max_time = max(metrics.max_time, execution_time)
            metrics.success_count += 1
            
            # Check if query was slow
            if execution_time > self.slow_query_threshold:
                logger.warning(f"Slow query detected: {execution_time:.2f}s - {query[:100]}...")
            
            return result
            
        except Exception as e:
            # Update error metrics
            if query_hash in self.query_metrics:
                self.query_metrics[query_hash].error_count += 1
            
            logger.error(f"Query execution error: {e}")
            raise
    
    async def analyze_query_performance(self, query: str) -> Dict[str, Any]:
        """Analyze query performance"""
        try:
            query_hash = self._generate_query_hash(query)
            
            # Get or create metrics
            if query_hash not in self.query_metrics:
                self.query_metrics[query_hash] = QueryMetrics(query_hash=query_hash)
            
            metrics = self.query_metrics[query_hash]
            plan = await self._generate_execution_plan(query)
            
            return {
                'query': query,
                'query_hash': query_hash,
                'execution_count': metrics.execution_count,
                'avg_time': metrics.avg_time,
                'min_time': metrics.min_time,
                'max_time': metrics.max_time,
                'success_rate': metrics.success_count / max(metrics.execution_count, 1),
                'error_count': metrics.error_count,
                'plan': asdict(plan),
                'recommendations': plan.recommendations,
                'optimization_level': plan.optimization_level.value
            }
            
        except Exception as e:
            logger.error(f"Query performance analysis error: {e}")
            return {}
    
    async def get_index_recommendations(self) -> Dict[str, List[str]]:
        """Get index recommendations for all tables"""
        try:
            recommendations = {}
            
            # Analyze query patterns
            for pattern_name, pattern in self.query_patterns.items():
                if pattern_name in ['where_clause', 'join_clause', 'order_by', 'group_by']:
                    # Find all queries using this pattern
                    for query_hash, metrics in self.query_metrics.items():
                        if pattern.search(metrics.query):
                            table_name = self._extract_table_from_query(metrics.query)
                            if table_name:
                                if table_name not in recommendations:
                                    recommendations[table_name] = []
                                recommendations[table_name].append(f"Add index on column used in {pattern_name}")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Index recommendation error: {e}")
            return {}
    
    def _extract_table_name(self, query: str) -> Optional[str]:
        """Extract table name from query"""
        try:
            # Simple regex to extract table name
            if self.db_type == "postgresql":
                table_match = re.search(r'FROM\s+(\w+)', query, re.IGNORECASE)
            elif self.db_type == "mysql":
                table_match = re.search(r'FROM\s+(\w+)', query, re.IGNORECASE)
            elif self.db_type == "mongodb":
                table_match = re.search(r'collection\s*:\s*(\w+)', query, re.IGNORECASE)
            
            if table_match:
                return table_match.group(1)
            
        except:
            pass
        return None
    
    async def start_background_optimization(self):
        """Start background optimization tasks"""
        asyncio.create_task(self._background_optimization_loop())
        logger.info("Background optimization started")
    
    async def _background_optimization_loop(self):
        """Background optimization loop"""
        while True:
            try:
                # Analyze slow queries
                await self._analyze_slow_queries()
                
                # Update index recommendations
                if self.enable_auto_indexing:
                    await self._update_index_recommendations()
                
                # Optimize connection pools
                await self._optimize_connection_pools()
                
                await asyncio.sleep(300)  # Run every 5 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Background optimization error: {e}")
                await asyncio.sleep(300)
    
    async def _analyze_slow_queries(self):
        """Analyze slow queries and suggest optimizations"""
        try:
            slow_queries = []
            
            for query_hash, metrics in self.query_metrics.items():
                if metrics.avg_time > self.slow_query_threshold:
                    slow_queries.append((query_hash, metrics))
            
            if slow_queries:
                logger.info(f"Found {len(slow_queries)} slow queries for optimization")
                
                # Sort by average time (slowest first)
                slow_queries.sort(key=lambda x: x[1].avg_time, reverse=True)
                
                for query_hash, metrics in slow_queries[:10]:  # Top 10 slowest
                    plan = await self._generate_execution_plan(metrics.query)
                    logger.warning(f"Slow query analysis - Hash: {query_hash[:8]}, Time: {metrics.avg_time:.2f}s")
                    
                    for recommendation in plan.recommendations:
                        logger.warning(f"  Recommendation: {recommendation}")
            
        except Exception as e:
            logger.error(f"Slow query analysis error: {e}")
    
    async def _update_index_recommendations(self):
        """Update index recommendations"""
        try:
            recommendations = await self.get_index_recommendations()
            
            for table_name, table_recommendations in recommendations.items():
                if table_recommendations:
                    logger.info(f"Index recommendations for {table_name}:")
                    for rec in table_recommendations:
                        logger.info(f"  - {rec}")
            
        except Exception as e:
            logger.error(f"Index recommendation update error: {e}")
    
    async def _optimize_connection_pools(self):
        """Optimize connection pool sizes"""
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent
            
            # Adjust pool sizes based on system load
            for pool_name, pool in self.connection_pools.items():
                if pool_name == 'postgresql':
                    # PostgreSQL pool optimization
                    if cpu_percent > 80 or memory_percent > 80:
                        # High load, reduce pool size
                        new_max = max(5, pool._maxsize - 5)
                        if new_max != pool._maxsize:
                            logger.info(f"Reducing PostgreSQL pool size from {pool._maxsize} to {new_max_size}")
                            # Note: In practice, you'd need to recreate the pool
                    elif cpu_percent < 30 and memory_percent < 30:
                        # Low load, can increase pool size
                        new_max = min(50, pool._maxsize + 5)
                        if new_max != pool._maxsize:
                            logger.info(f"Increasing PostgreSQL pool size from {pool._maxsize} to {new_max_size}")
                            # Note: In practice, you'd need to recreate the pool
                
        except Exception as e:
            logger.error(f"Connection pool optimization error: {e}")
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get overall performance metrics"""
        try:
            total_queries = sum(m.execution_count for m in self.query_metrics.values())
            total_time = sum(m.total_time for m in self.query_metrics.values())
            avg_time = total_time / max(total_queries, 1)
            
            slow_queries = len([m for m in self.query_metrics.values() if m.avg_time > self.slow_query_threshold])
            
            return {
                'total_queries': total_queries,
                'total_time': total_time,
                'avg_time': avg_time,
                'slow_queries': slow_queries,
                'query_metrics_count': len(self.query_metrics),
                'connection_pools': {name: pool._maxsize for name, pool in self.connection_pools.items()},
                'optimization_enabled': {
                    'query_caching': self.enable_query_caching,
                    'auto_indexing': self.enable_auto_indexing,
                    'query_rewrite': self.enable_query_rewrite
                }
            }
            
        except Exception as e:
            logger.error(f"Performance metrics error: {e}")
            return {}
    
    async def shutdown(self):
        """Shutdown the database optimizer"""
        logger.info("Shutting down database optimizer...")
        
        # Close connection pools
        for pool in self.connection_pools.values():
            await pool.close()
        
        self.connection_pools.clear()
        
        logger.info("Database optimizer shutdown complete")

# Global database optimizer instance
db_optimizer = DatabaseOptimizer()
