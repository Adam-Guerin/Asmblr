#!/usr/bin/env python3
"""
Automated Backup Service for Asmblr
Performs scheduled backups of databases, configurations, and user data
"""

import sys
import asyncio
import json
import shutil
import time
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
import argparse

import redis.asyncio as redis
from loguru import logger

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.config import get_settings


class BackupService:
    """Automated backup service for Asmblr"""
    
    def __init__(self):
        settings = get_settings()
        self.settings = settings
        self.backup_dir = Path(settings.backup_dir) if hasattr(settings, 'backup_dir') else Path("backups")
        self.data_dir = Path(settings.data_dir)
        self.runs_dir = Path(settings.runs_dir)
        self.config_dir = Path(settings.config_dir)
        
        # Backup configuration
        self.backup_retention_days = getattr(settings, 'backup_retention_days', 30)
        self.compression_enabled = True
        self.s3_bucket = getattr(settings, 's3_bucket', None)
        self.aws_access_key = getattr(settings, 'aws_access_key_id', None)
        self.aws_secret_key = getattr(settings, 'aws_secret_access_key', None)
        
        # Ensure backup directory exists
        self.backup_dir.mkdir(exist_ok=True)
        
        logger.info(f"Backup service initialized. Backup dir: {self.backup_dir}")
    
    async def create_backup(self, backup_type: str = "full") -> dict[str, Any]:
        """Create a backup of specified type"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"asmblr_{backup_type}_{timestamp}"
        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(exist_ok=True)
        
        logger.info(f"Starting {backup_type} backup: {backup_name}")
        
        backup_manifest = {
            "backup_name": backup_name,
            "backup_type": backup_type,
            "timestamp": datetime.now().isoformat(),
            "files": {},
            "status": "in_progress"
        }
        
        try:
            if backup_type == "full":
                await self._backup_database(backup_path, backup_manifest)
                await self._backup_runs(backup_path, backup_manifest)
                await self._backup_configurations(backup_path, backup_manifest)
                await self._backup_logs(backup_path, backup_manifest)
                
            elif backup_type == "database":
                await self._backup_database(backup_path, backup_manifest)
                
            elif backup_type == "runs":
                await self._backup_runs(backup_path, backup_manifest)
                
            elif backup_type == "config":
                await self._backup_configurations(backup_path, backup_manifest)
            
            # Create manifest file
            manifest_path = backup_path / "backup_manifest.json"
            with open(manifest_path, 'w') as f:
                backup_manifest["status"] = "completed"
                json.dump(backup_manifest, f, indent=2)
            
            # Compress backup if enabled
            if self.compression_enabled:
                await self._compress_backup(backup_path)
            
            # Upload to S3 if configured
            if self.s3_bucket:
                await self._upload_to_s3(backup_path)
            
            backup_manifest["status"] = "completed"
            logger.info(f"Backup completed successfully: {backup_name}")
            
            return backup_manifest
            
        except Exception as e:
            backup_manifest["status"] = "failed"
            backup_manifest["error"] = str(e)
            logger.error(f"Backup failed: {e}")
            
            # Save error manifest
            manifest_path = backup_path / "backup_manifest.json"
            with open(manifest_path, 'w') as f:
                json.dump(backup_manifest, f, indent=2)
            
            raise
    
    async def _backup_database(self, backup_path: Path, manifest: dict[str, Any]) -> None:
        """Backup database files"""
        logger.info("Backing up database...")
        
        db_backup_dir = backup_path / "database"
        db_backup_dir.mkdir(exist_ok=True)
        
        # Backup SQLite database
        sqlite_db = self.data_dir / "app.db"
        if sqlite_db.exists():
            # Create a consistent backup using SQLite backup command
            backup_db = db_backup_dir / "app.db"
            try:
                # Use SQLite backup command for consistency
                subprocess.run([
                    "sqlite3", str(sqlite_db), f".backup {backup_db}"
                ], check=True, capture_output=True)
                
                manifest["files"]["database"] = {
                    "app_db": str(backup_db.relative_to(backup_path)),
                    "size": backup_db.stat().st_size,
                    "type": "sqlite"
                }
                
                logger.info(f"Database backed up: {backup_db}")
                
            except subprocess.CalledProcessError as e:
                # Fallback to file copy
                shutil.copy2(sqlite_db, backup_db)
                manifest["files"]["database"] = {
                    "app_db": str(backup_db.relative_to(backup_path)),
                    "size": backup_db.stat().st_size,
                    "type": "sqlite_copy"
                }
                logger.warning(f"Database backup used copy method: {e}")
        
        # Backup Redis data if available
        try:
            redis_client = redis.from_url(self.settings.redis_url)
            
            # Create Redis backup
            redis_backup = db_backup_dir / "redis_dump.rdb"
            
            # Trigger Redis save
            await redis_client.save()
            
            # Copy Redis RDB file
            redis_rdb_path = Path("/var/lib/redis/dump.rdb")  # Default Redis path
            if redis_rdb_path.exists():
                shutil.copy2(redis_rdb_path, redis_backup)
                manifest["files"]["database"]["redis"] = {
                    "path": str(redis_backup.relative_to(backup_path)),
                    "size": redis_backup.stat().st_size
                }
                logger.info(f"Redis data backed up: {redis_backup}")
            
        except Exception as e:
            logger.warning(f"Redis backup failed: {e}")
    
    async def _backup_runs(self, backup_path: Path, manifest: dict[str, Any]) -> None:
        """Backup runs directory"""
        logger.info("Backing up runs...")
        
        runs_backup_dir = backup_path / "runs"
        runs_backup_dir.mkdir(exist_ok=True)
        
        if not self.runs_dir.exists():
            logger.warning("Runs directory not found")
            return
        
        # Backup recent runs (last 7 days)
        cutoff_time = datetime.now() - timedelta(days=7)
        backed_up_runs = []
        
        for run_dir in self.runs_dir.iterdir():
            if not run_dir.is_dir():
                continue
            
            try:
                # Parse run timestamp from directory name
                run_name = run_dir.name
                if "_" in run_name:
                    date_part = run_name.split("_")[0]
                    run_time = datetime.strptime(date_part, "%Y%m%d")
                    
                    if run_time > cutoff_time:
                        # Copy run directory
                        run_backup = runs_backup_dir / run_name
                        shutil.copytree(run_dir, run_backup)
                        backed_up_runs.append(run_name)
                        
            except Exception as e:
                logger.warning(f"Failed to backup run {run_dir.name}: {e}")
        
        manifest["files"]["runs"] = {
            "backed_up_runs": backed_up_runs,
            "count": len(backed_up_runs),
            "cutoff_days": 7
        }
        
        logger.info(f"Backed up {len(backed_up_runs)} runs")
    
    async def _backup_configurations(self, backup_path: Path, manifest: dict[str, Any]) -> None:
        """Backup configuration files"""
        logger.info("Backing up configurations...")
        
        config_backup_dir = backup_path / "config"
        config_backup_dir.mkdir(exist_ok=True)
        
        backed_up_configs = []
        
        # Backup environment files
        env_files = [".env", ".env.example", ".env.minimal", ".env.production"]
        for env_file in env_files:
            env_path = project_root / env_file
            if env_path.exists():
                backup_path = config_backup_dir / env_file
                shutil.copy2(env_path, backup_path)
                backed_up_configs.append(env_file)
        
        # Backup configuration directory
        if self.config_dir.exists():
            config_dest = config_backup_dir / "configs"
            shutil.copytree(self.config_dir, config_dest)
            backed_up_configs.append("configs/")
        
        # Backup Docker compose files
        docker_files = [
            "docker-compose.yml",
            "docker-compose.production.yml",
            "docker-compose.monitoring.yml"
        ]
        for docker_file in docker_files:
            docker_path = project_root / docker_file
            if docker_path.exists():
                backup_path = config_backup_dir / docker_file
                shutil.copy2(docker_path, backup_path)
                backed_up_configs.append(docker_file)
        
        manifest["files"]["configurations"] = {
            "files": backed_up_configs,
            "count": len(backed_up_configs)
        }
        
        logger.info(f"Backed up {len(backed_up_configs)} configuration files")
    
    async def _backup_logs(self, backup_path: Path, manifest: dict[str, Any]) -> None:
        """Backup log files"""
        logger.info("Backing up logs...")
        
        logs_backup_dir = backup_path / "logs"
        logs_backup_dir.mkdir(exist_ok=True)
        
        # Backup recent logs (last 3 days)
        log_dirs = [
            project_root / "logs",
            Path("/var/log/asmblr")
        ]
        
        backed_up_logs = []
        
        for log_dir in log_dirs:
            if not log_dir.exists():
                continue
            
            for log_file in log_dir.glob("*.log*"):
                try:
                    # Check if log file is recent
                    mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                    if datetime.now() - mtime < timedelta(days=3):
                        backup_file = logs_backup_dir / log_file.name
                        shutil.copy2(log_file, backup_file)
                        backed_up_logs.append(log_file.name)
                        
                except Exception as e:
                    logger.warning(f"Failed to backup log {log_file.name}: {e}")
        
        manifest["files"]["logs"] = {
            "files": backed_up_logs,
            "count": len(backed_up_logs)
        }
        
        logger.info(f"Backed up {len(backed_up_logs)} log files")
    
    async def _compress_backup(self, backup_path: Path) -> None:
        """Compress backup directory"""
        logger.info("Compressing backup...")
        
        compressed_path = backup_path.with_suffix(".tar.gz")
        
        try:
            # Create tar.gz archive
            subprocess.run([
                "tar", "-czf", str(compressed_path),
                "-C", str(backup_path.parent),
                backup_path.name
            ], check=True)
            
            # Remove uncompressed directory
            shutil.rmtree(backup_path)
            
            logger.info(f"Backup compressed: {compressed_path}")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Compression failed: {e}")
            raise
    
    async def _upload_to_s3(self, backup_path: Path) -> None:
        """Upload backup to S3"""
        if not self.s3_bucket or not self.aws_access_key or not self.aws_secret_key:
            logger.warning("S3 configuration not complete, skipping upload")
            return
        
        logger.info("Uploading backup to S3...")
        
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            # Initialize S3 client
            s3_client = boto3.client(
                's3',
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key
            )
            
            # Determine file to upload
            if self.compression_enabled:
                upload_file = backup_path.with_suffix(".tar.gz")
            else:
                upload_file = backup_path
            
            if not upload_file.exists():
                logger.warning(f"Backup file not found: {upload_file}")
                return
            
            # Upload to S3
            s3_key = f"backups/{upload_file.name}"
            
            s3_client.upload_file(
                str(upload_file),
                self.s3_bucket,
                s3_key
            )
            
            logger.info(f"Backup uploaded to S3: s3://{self.s3_bucket}/{s3_key}")
            
        except ImportError:
            logger.warning("boto3 not installed, skipping S3 upload")
        except Exception as e:
            logger.error(f"S3 upload failed: {e}")
            raise
    
    async def cleanup_old_backups(self) -> None:
        """Clean up old backups based on retention policy"""
        logger.info("Cleaning up old backups...")
        
        cutoff_date = datetime.now() - timedelta(days=self.backup_retention_days)
        deleted_count = 0
        
        try:
            for backup_item in self.backup_dir.iterdir():
                if backup_item.is_dir():
                    # Parse backup timestamp from directory name
                    try:
                        backup_name = backup_item.name
                        if "asmblr_" in backup_name:
                            timestamp_str = backup_name.split("_")[2]
                            backup_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                            
                            if backup_date < cutoff_date:
                                shutil.rmtree(backup_item)
                                deleted_count += 1
                                logger.info(f"Deleted old backup: {backup_name}")
                    
                    except (ValueError, IndexError):
                        continue
                
                elif backup_item.is_file() and backup_item.suffix == ".gz":
                    # Handle compressed backups
                    try:
                        backup_name = backup_item.stem
                        if "asmblr_" in backup_name:
                            timestamp_str = backup_name.split("_")[2]
                            backup_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                            
                            if backup_date < cutoff_date:
                                backup_item.unlink()
                                deleted_count += 1
                                logger.info(f"Deleted old backup: {backup_item.name}")
                    
                    except (ValueError, IndexError):
                        continue
            
            logger.info(f"Cleanup completed. Deleted {deleted_count} old backups.")
            
        except Exception as e:
            logger.error(f"Backup cleanup failed: {e}")
    
    async def list_backups(self) -> list[dict[str, Any]]:
        """List all available backups"""
        backups = []
        
        try:
            for backup_item in self.backup_dir.iterdir():
                backup_info = {}
                
                if backup_item.is_dir():
                    # Uncompressed backup
                    manifest_path = backup_item / "backup_manifest.json"
                    if manifest_path.exists():
                        with open(manifest_path) as f:
                            backup_info = json.load(f)
                            backup_info["path"] = str(backup_item)
                            backup_info["compressed"] = False
                
                elif backup_item.is_file() and backup_item.suffix == ".gz":
                    # Compressed backup
                    backup_name = backup_item.stem
                    if "asmblr_" in backup_name:
                        backup_info = {
                            "backup_name": backup_name,
                            "path": str(backup_item),
                            "compressed": True,
                            "size": backup_item.stat().st_size
                        }
                        
                        # Try to extract timestamp
                        try:
                            timestamp_str = backup_name.split("_")[2]
                            backup_info["timestamp"] = datetime.strptime(
                                timestamp_str, "%Y%m%d_%H%M%S"
                            ).isoformat()
                        except (ValueError, IndexError):
                            pass
                
                if backup_info:
                    backups.append(backup_info)
            
            # Sort by timestamp (newest first)
            backups.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
        except Exception as e:
            logger.error(f"Failed to list backups: {e}")
        
        return backups
    
    async def restore_backup(self, backup_name: str) -> bool:
        """Restore from a backup"""
        logger.info(f"Starting restore from backup: {backup_name}")
        
        try:
            # Find backup
            backup_path = None
            for backup_item in self.backup_dir.iterdir():
                if backup_item.name == backup_name or backup_item.stem == backup_name:
                    backup_path = backup_item
                    break
            
            if not backup_path:
                logger.error(f"Backup not found: {backup_name}")
                return False
            
            # Extract if compressed
            if backup_path.suffix == ".gz":
                extract_path = backup_path.parent / backup_path.stem
                subprocess.run([
                    "tar", "-xzf", str(backup_path),
                    "-C", str(backup_path.parent)
                ], check=True)
                backup_path = extract_path
            
            # Read manifest
            manifest_path = backup_path / "backup_manifest.json"
            if not manifest_path.exists():
                logger.error("Backup manifest not found")
                return False
            
            with open(manifest_path) as f:
                manifest = json.load(f)
            
            # Restore components
            if "database" in manifest.get("files", {}):
                await self._restore_database(backup_path, manifest)
            
            if "runs" in manifest.get("files", {}):
                await self._restore_runs(backup_path, manifest)
            
            if "configurations" in manifest.get("files", {}):
                await self._restore_configurations(backup_path, manifest)
            
            logger.info(f"Restore completed from backup: {backup_name}")
            return True
            
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False
    
    async def _restore_database(self, backup_path: Path, manifest: dict[str, Any]) -> None:
        """Restore database from backup"""
        logger.info("Restoring database...")
        
        db_backup_dir = backup_path / "database"
        if not db_backup_dir.exists():
            return
        
        # Restore SQLite database
        sqlite_backup = db_backup_dir / "app.db"
        if sqlite_backup.exists():
            sqlite_db = self.data_dir / "app.db"
            
            # Create backup of current database
            if sqlite_db.exists():
                backup_current = sqlite_db.with_suffix(f".db.backup.{int(time.time())}")
                shutil.copy2(sqlite_db, backup_current)
                logger.info(f"Current database backed up to: {backup_current}")
            
            # Restore from backup
            shutil.copy2(sqlite_backup, sqlite_db)
            logger.info("SQLite database restored")
    
    async def _restore_runs(self, backup_path: Path, manifest: dict[str, Any]) -> None:
        """Restore runs from backup"""
        logger.info("Restoring runs...")
        
        runs_backup_dir = backup_path / "runs"
        if not runs_backup_dir.exists():
            return
        
        # Merge runs (don't overwrite existing)
        for run_backup in runs_backup_dir.iterdir():
            if not run_backup.is_dir():
                continue
            
            run_dest = self.runs_dir / run_backup.name
            if not run_dest.exists():
                shutil.copytree(run_backup, run_dest)
                logger.info(f"Restored run: {run_backup.name}")
    
    async def _restore_configurations(self, backup_path: Path, manifest: dict[str, Any]) -> None:
        """Restore configurations from backup"""
        logger.info("Restoring configurations...")
        
        config_backup_dir = backup_path / "config"
        if not config_backup_dir.exists():
            return
        
        # Restore configuration files (with .bak extension to avoid overwrites)
        for config_file in config_backup_dir.iterdir():
            if config_file.is_file():
                dest_path = project_root / config_file.name
                if dest_path.exists():
                    backup_path = dest_path.with_suffix(f".{int(time.time())}.bak")
                    shutil.copy2(dest_path, backup_path)
                
                shutil.copy2(config_file, dest_path)
                logger.info(f"Restored configuration: {config_file.name}")


async def main():
    """Main backup service function"""
    parser = argparse.ArgumentParser(description="Asmblr Backup Service")
    parser.add_argument("action", choices=["backup", "restore", "list", "cleanup"],
                       help="Action to perform")
    parser.add_argument("--type", choices=["full", "database", "runs", "config"],
                       default="full", help="Backup type")
    parser.add_argument("--name", help="Backup name for restore")
    parser.add_argument("--schedule", action="store_true",
                       help="Run in scheduled mode")
    
    args = parser.parse_args()
    
    backup_service = BackupService()
    
    if args.action == "backup":
        manifest = await backup_service.create_backup(args.type)
        print(f"Backup completed: {manifest.get('backup_name')}")
    
    elif args.action == "restore":
        if not args.name:
            print("Error: --name required for restore")
            sys.exit(1)
        
        success = await backup_service.restore_backup(args.name)
        if success:
            print(f"Restore completed from: {args.name}")
        else:
            print(f"Restore failed: {args.name}")
            sys.exit(1)
    
    elif args.action == "list":
        backups = await backup_service.list_backups()
        print("Available backups:")
        for backup in backups:
            print(f"  {backup.get('backup_name', 'Unknown')} - {backup.get('timestamp', 'Unknown')}")
    
    elif args.action == "cleanup":
        await backup_service.cleanup_old_backups()
        print("Backup cleanup completed")
    
    elif args.action == "schedule":
        # Run scheduled backups every 6 hours
        logger.info("Starting scheduled backup service...")
        
        while True:
            try:
                await backup_service.create_backup("full")
                await backup_service.cleanup_old_backups()
                
                # Wait 6 hours
                await asyncio.sleep(6 * 3600)
                
            except KeyboardInterrupt:
                logger.info("Scheduled backup service stopped")
                break
            except Exception as e:
                logger.error(f"Scheduled backup failed: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retry


if __name__ == "__main__":
    asyncio.run(main())
