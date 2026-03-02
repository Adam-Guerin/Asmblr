"""
Tests for Backup Service
Validates backup creation, restoration, and management
"""

import pytest
import asyncio
import json
import tempfile
from unittest.mock import AsyncMock, patch, MagicMock
from pathlib import Path

# Import backup service
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from backup_service import BackupService


class TestBackupService:
    """Test suite for BackupService"""
    
    @pytest.fixture
    def backup_service(self):
        """Create backup service for testing"""
        with patch('backup_service.get_settings') as mock_settings:
            mock_settings_instance = MagicMock()
            mock_settings_instance.backup_dir = "test_backups"
            mock_settings_instance.data_dir = "test_data"
            mock_settings_instance.runs_dir = "test_runs"
            mock_settings_instance.config_dir = "test_configs"
            mock_settings_instance.backup_retention_days = 7
            mock_settings_instance.redis_url = "redis://localhost:6379/0"
            mock_settings.return_value = mock_settings_instance
            
            service = BackupService()
            return service
    
    def test_backup_service_initialization(self, backup_service):
        """Test backup service initialization"""
        assert backup_service.backup_dir.name == "test_backups"
        assert backup_service.data_dir.name == "test_data"
        assert backup_service.runs_dir.name == "test_runs"
        assert backup_service.config_dir.name == "test_configs"
        assert backup_service.backup_retention_days == 7
    
    @pytest.mark.asyncio
    async def test_create_full_backup(self, backup_service):
        """Test full backup creation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set up test directories
            backup_service.backup_dir = Path(temp_dir) / "backups"
            backup_service.data_dir = Path(temp_dir) / "data"
            backup_service.runs_dir = Path(temp_dir) / "runs"
            backup_service.config_dir = Path(temp_dir) / "configs"
            
            # Create test data
            backup_service.backup_dir.mkdir(exist_ok=True)
            backup_service.data_dir.mkdir(exist_ok=True)
            backup_service.runs_dir.mkdir(exist_ok=True)
            backup_service.config_dir.mkdir(exist_ok=True)
            
            # Create test files
            (backup_service.data_dir / "app.db").touch()
            (backup_service.runs_dir / "run1").mkdir()
            (backup_service.config_dir / "config.yaml").touch()
            
            # Mock Redis operations
            with patch('backup_service.redis') as mock_redis:
                mock_redis.from_url.return_value = AsyncMock()
                
                manifest = await backup_service.create_backup("full")
                
                assert manifest["backup_type"] == "full"
                assert manifest["status"] == "completed"
                assert "files" in manifest
                assert "database" in manifest["files"]
                assert "runs" in manifest["files"]
                assert "configurations" in manifest["files"]
    
    @pytest.mark.asyncio
    async def test_create_database_backup(self, backup_service):
        """Test database backup creation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            backup_service.backup_dir = Path(temp_dir) / "backups"
            backup_service.data_dir = Path(temp_dir) / "data"
            
            # Create test database
            backup_service.backup_dir.mkdir(exist_ok=True)
            backup_service.data_dir.mkdir(exist_ok=True)
            db_file = backup_service.data_dir / "app.db"
            db_file.write_text("test database content")
            
            # Mock Redis operations
            with patch('backup_service.redis') as mock_redis:
                mock_redis.from_url.return_value = AsyncMock()
                
                manifest = await backup_service.create_backup("database")
                
                assert manifest["backup_type"] == "database"
                assert manifest["status"] == "completed"
                assert "database" in manifest["files"]
                
                # Check backup file exists
                backup_path = backup_service.backup_dir / manifest["backup_name"] / "database" / "app.db"
                assert backup_path.exists()
    
    @pytest.mark.asyncio
    async def test_backup_compression(self, backup_service):
        """Test backup compression"""
        with tempfile.TemporaryDirectory() as temp_dir:
            backup_service.backup_dir = Path(temp_dir) / "backups"
            backup_service.data_dir = Path(temp_dir) / "data"
            
            # Create test data
            backup_service.backup_dir.mkdir(exist_ok=True)
            backup_service.data_dir.mkdir(exist_ok=True)
            (backup_service.data_dir / "app.db").write_text("test content")
            
            # Mock Redis and subprocess
            with patch('backup_service.redis') as mock_redis, \
                 patch('backup_service.subprocess.run') as mock_subprocess:
                
                mock_redis.from_url.return_value = AsyncMock()
                mock_subprocess.return_value = MagicMock()
                
                manifest = await backup_service.create_backup("full")
                
                # Verify compression was called
                mock_subprocess.assert_called()
                call_args = mock_subprocess.call_args[0][0]
                assert "tar" in call_args
                assert "-czf" in call_args
    
    @pytest.mark.asyncio
    async def test_s3_upload(self, backup_service):
        """Test S3 upload functionality"""
        with tempfile.TemporaryDirectory() as temp_dir:
            backup_service.backup_dir = Path(temp_dir) / "backups"
            backup_service.s3_bucket = "test-bucket"
            backup_service.aws_access_key = "test-key"
            backup_service.aws_secret_key = "test-secret"
            
            # Create test backup
            backup_service.backup_dir.mkdir(exist_ok=True)
            backup_path = backup_service.backup_dir / "test_backup"
            backup_path.mkdir()
            (backup_path / "test.txt").write_text("test content")
            
            # Mock boto3
            with patch('backup_service.boto3') as mock_boto3:
                mock_s3 = MagicMock()
                mock_boto3.client.return_value = mock_s3
                
                await backup_service._upload_to_s3(backup_path)
                
                # Verify S3 client was created
                mock_boto3.client.assert_called_with(
                    's3',
                    aws_access_key_id="test-key",
                    aws_secret_access_key="test-secret"
                )
                
                # Verify upload was called
                mock_s3.upload_file.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_list_backups(self, backup_service):
        """Test listing available backups"""
        with tempfile.TemporaryDirectory() as temp_dir:
            backup_service.backup_dir = Path(temp_dir) / "backups"
            
            # Create test backups
            backup_service.backup_dir.mkdir(exist_ok=True)
            
            # Create uncompressed backup
            backup1 = backup_service.backup_dir / "asmblr_full_20240101_120000"
            backup1.mkdir()
            (backup1 / "backup_manifest.json").write_text(json.dumps({
                "backup_name": "asmblr_full_20240101_120000",
                "backup_type": "full",
                "timestamp": "2024-01-01T12:00:00"
            }))
            
            # Create compressed backup
            backup2 = backup_service.backup_dir / "asmblr_database_20240101_130000.tar.gz"
            backup2.write_text("compressed content")
            
            backups = await backup_service.list_backups()
            
            assert len(backups) == 2
            assert backups[0]["backup_name"] == "asmblr_full_20240101_120000"
            assert backups[1]["backup_name"] == "asmblr_database_20240101_130000"
    
    @pytest.mark.asyncio
    async def test_restore_backup(self, backup_service):
        """Test backup restoration"""
        with tempfile.TemporaryDirectory() as temp_dir:
            backup_service.backup_dir = Path(temp_dir) / "backups"
            backup_service.data_dir = Path(temp_dir) / "data"
            backup_service.runs_dir = Path(temp_dir) / "runs"
            backup_service.config_dir = Path(temp_dir) / "configs"
            
            # Create directories
            backup_service.backup_dir.mkdir(exist_ok=True)
            backup_service.data_dir.mkdir(exist_ok=True)
            backup_service.runs_dir.mkdir(exist_ok=True)
            backup_service.config_dir.mkdir(exist_ok=True)
            
            # Create test backup
            backup_name = "test_backup"
            backup_path = backup_service.backup_dir / backup_name
            backup_path.mkdir()
            
            # Create backup manifest
            manifest = {
                "backup_name": backup_name,
                "backup_type": "full",
                "timestamp": "2024-01-01T12:00:00",
                "files": {
                    "database": {"app_db": "database/app.db"},
                    "runs": {"backed_up_runs": ["run1", "run2"]},
                    "configurations": {"files": ["config.yaml"]}
                }
            }
            
            (backup_path / "backup_manifest.json").write_text(json.dumps(manifest))
            
            # Create backup files
            (backup_path / "database").mkdir()
            (backup_path / "database" / "app.db").write_text("database content")
            
            (backup_path / "runs").mkdir()
            (backup_path / "runs" / "run1").mkdir()
            (backup_path / "runs" / "run2").mkdir()
            
            (backup_path / "config").mkdir()
            (backup_path / "config" / "config.yaml").write_text("config content")
            
            # Restore backup
            success = await backup_service.restore_backup(backup_name)
            
            assert success is True
            
            # Verify files were restored
            assert (backup_service.data_dir / "app.db").exists()
            assert (backup_service.runs_dir / "run1").exists()
            assert (backup_service.config_dir / "config.yaml").exists()
    
    @pytest.mark.asyncio
    async def test_cleanup_old_backups(self, backup_service):
        """Test cleanup of old backups"""
        with tempfile.TemporaryDirectory() as temp_dir:
            backup_service.backup_dir = Path(temp_dir) / "backups"
            backup_service.backup_retention_days = 7
            
            # Create test backups with different timestamps
            backup_service.backup_dir.mkdir(exist_ok=True)
            
            # Recent backup (should not be deleted)
            recent_backup = backup_service.backup_dir / "asmblr_recent_20240108_120000"
            recent_backup.mkdir()
            (recent_backup / "backup_manifest.json").write_text(json.dumps({
                "backup_name": "asmblr_recent_20240108_120000",
                "timestamp": "2024-01-08T12:00:00"  # Recent
            }))
            
            # Old backup (should be deleted)
            old_backup = backup_service.backup_dir / "asmblr_old_20240101_120000"
            old_backup.mkdir()
            (old_backup / "backup_manifest.json").write_text(json.dumps({
                "backup_name": "asmblr_old_20240101_120000",
                "timestamp": "2024-01-01T12:00:00"  # Old
            }))
            
            deleted_count = await backup_service.cleanup_old_backups()
            
            assert deleted_count == 1
            assert recent_backup.exists()
            assert not old_backup.exists()


class TestBackupServiceIntegration:
    """Integration tests for backup service"""
    
    @pytest.mark.asyncio
    async def test_backup_workflow_end_to_end(self):
        """Test complete backup workflow"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set up test environment
            backup_dir = Path(temp_dir) / "backups"
            data_dir = Path(temp_dir) / "data"
            runs_dir = Path(temp_dir) / "runs"
            config_dir = Path(temp_dir) / "configs"
            
            # Create directories
            for directory in [backup_dir, data_dir, runs_dir, config_dir]:
                directory.mkdir(exist_ok=True)
            
            # Create test data
            (data_dir / "app.db").write_text("test database")
            (runs_dir / "run1").mkdir()
            (runs_dir / "run1" / "result.json").write_text('{"status": "completed"}')
            (config_dir / "config.yaml").write_text("test: config")
            
            # Create backup service
            with patch('backup_service.get_settings') as mock_settings:
                mock_settings_instance = MagicMock()
                mock_settings_instance.backup_dir = backup_dir
                mock_settings_instance.data_dir = data_dir
                mock_settings_instance.runs_dir = runs_dir
                mock_settings_instance.config_dir = config_dir
                mock_settings_instance.backup_retention_days = 7
                mock_settings_instance.redis_url = "redis://localhost:6379/0"
                mock_settings.return_value = mock_settings_instance
                
                service = BackupService()
                
                # Mock Redis
                with patch('backup_service.redis') as mock_redis, \
                     patch('backup_service.subprocess.run') as mock_subprocess:
                    
                    mock_redis.from_url.return_value = AsyncMock()
                    mock_subprocess.return_value = MagicMock()
                    
                    # Create backup
                    manifest = await service.create_backup("full")
                    
                    # Verify backup was created
                    assert manifest["status"] == "completed"
                    assert manifest["backup_type"] == "full"
                    
                    # List backups
                    backups = await service.list_backups()
                    assert len(backups) == 1
                    assert backups[0]["backup_type"] == "full"
                    
                    # Restore backup
                    success = await service.restore_backup(backups[0]["backup_name"])
                    assert success is True
    
    @pytest.mark.asyncio
    async def test_backup_error_handling(self):
        """Test backup service error handling"""
        with tempfile.TemporaryDirectory() as temp_dir:
            backup_dir = Path(temp_dir) / "backups"
            backup_dir.mkdir(exist_ok=True)
            
            with patch('backup_service.get_settings') as mock_settings:
                mock_settings_instance = MagicMock()
                mock_settings_instance.backup_dir = backup_dir
                mock_settings_instance.data_dir = Path(temp_dir) / "data"
                mock_settings_instance.runs_dir = Path(temp_dir) / "runs"
                mock_settings_instance.config_dir = Path(temp_dir) / "configs"
                mock_settings_instance.backup_retention_days = 7
                mock_settings_instance.redis_url = "redis://localhost:6379/0"
                mock_settings.return_value = mock_settings_instance
                
                service = BackupService()
                
                # Test with missing directories
                with patch('backup_service.redis') as mock_redis:
                    mock_redis.from_url.return_value = AsyncMock()
                    
                    # Should handle missing directories gracefully
                    manifest = await service.create_backup("full")
                    
                    # Should still create backup manifest
                    assert manifest["backup_type"] == "full"
                    assert "files" in manifest
    
    @pytest.mark.asyncio
    async def test_backup_performance(self):
        """Test backup service performance"""
        with tempfile.TemporaryDirectory() as temp_dir:
            backup_dir = Path(temp_dir) / "backups"
            data_dir = Path(temp_dir) / "data"
            
            # Create directories
            backup_dir.mkdir(exist_ok=True)
            data_dir.mkdir(exist_ok=True)
            
            # Create test database
            (data_dir / "app.db").write_text("x" * 1000)  # 1KB test data
            
            with patch('backup_service.get_settings') as mock_settings:
                mock_settings_instance = MagicMock()
                mock_settings_instance.backup_dir = backup_dir
                mock_settings_instance.data_dir = data_dir
                mock_settings_instance.runs_dir = Path(temp_dir) / "runs"
                mock_settings_instance.config_dir = Path(temp_dir) / "configs"
                mock_settings_instance.backup_retention_days = 7
                mock_settings_instance.redis_url = "redis://localhost:6379/0"
                mock_settings.return_value = mock_settings_instance
                
                service = BackupService()
                
                with patch('backup_service.redis') as mock_redis:
                    mock_redis.from_url.return_value = AsyncMock()
                    
                    # Measure backup performance
                    start_time = asyncio.get_event_loop().time()
                    
                    manifest = await service.create_backup("database")
                    
                    end_time = asyncio.get_event_loop().time()
                    duration = end_time - start_time
                    
                    # Should complete quickly (under 5 seconds for small backup)
                    assert duration < 5.0
                    assert manifest["status"] == "completed"


@pytest.mark.asyncio
async def test_backup_service_main():
    """Test backup service main function"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock command line arguments
        test_args = ["backup", "--type", "database"]
        
        with patch('sys.argv', ["backup-service.py"] + test_args), \
             patch('backup_service.BackupService') as mock_backup_service, \
             patch('backup_service.asyncio.run') as mock_run:
            
            # Mock backup service instance
            mock_instance = AsyncMock()
            mock_backup_service.return_value = mock_instance
            mock_instance.create_backup.return_value = {"backup_name": "test_backup"}
            
            # Import and run main
            from backup_service import main
            
            # Should not raise exception
            try:
                await main()
            except SystemExit:
                pass  # Expected when script completes
            
            # Verify backup was created
            mock_instance.create_backup.assert_called_once_with("database")
