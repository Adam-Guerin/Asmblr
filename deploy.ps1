# Asmblr Production Deployment Script (PowerShell)
# Automated deployment with health checks and rollback

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("development", "staging", "production")]
    [string]$Environment = "production",
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipBackup,
    
    [Parameter(Mandatory=$false)]
    [switch]$Force
)

# Colors for output
$Colors = @{
    Red = "Red"
    Green = "Green"
    Yellow = "Yellow"
    Blue = "Blue"
    White = "White"
}

function Write-Status {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor $Colors.Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor $Colors.Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor $Colors.Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ️  $Message" -ForegroundColor $Colors.Blue
}

# Configuration
$BackupDir = "./backups/$(Get-Date -Format 'yyyyMMdd_HHmmss')"
$HealthCheckUrl = "http://localhost:8000/health"
$MaxRetries = 30
$RetryDelay = 10

Write-Host "🚀 Asmblr Production Deployment" -ForegroundColor $Colors.Blue
Write-Host "================================" -ForegroundColor $Colors.Blue
Write-Host "Environment: $Environment" -ForegroundColor $Colors.Yellow
Write-Host "Timestamp: $(Get-Date)"
Write-Host ""

# Pre-deployment checks
function Pre-Deployment-Checks {
    Write-Info "Running pre-deployment checks..."
    
    # Check required commands
    $requiredCommands = @("docker", "docker-compose", "curl", "git")
    foreach ($cmd in $requiredCommands) {
        try {
            Get-Command $cmd -ErrorAction Stop | Out-Null
        } catch {
            Write-Error "Required command not found: $cmd"
            exit 1
        }
    }
    
    # Check Docker daemon
    try {
        docker info | Out-Null
    } catch {
        Write-Error "Docker daemon is not running"
        exit 1
    }
    
    # Check environment file
    if (-not (Test-Path ".env.production")) {
        Write-Warning ".env.production not found, copying from .env.example"
        Copy-Item ".env.example" ".env.production"
        Write-Warning "Please update .env.production with production values"
        if (-not $Force) {
            exit 1
        }
    }
    
    # Check git status
    $gitStatus = git status --porcelain
    if ($gitStatus -and -not $Force) {
        Write-Warning "Uncommitted changes detected"
        $response = Read-Host "Continue anyway? (y/N)"
        if ($response -ne "y" -and $response -ne "Y") {
            Write-Info "Deployment cancelled"
            exit 0
        }
    }
    
    Write-Status "Pre-deployment checks passed"
}

# Create backup
function Create-Backup {
    if ($SkipBackup) {
        Write-Warning "Skipping backup"
        return
    }
    
    Write-Info "Creating backup..."
    
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
    
    # Backup database
    $postgresRunning = docker-compose -f docker-compose.production.yml ps -q postgres 2>$null
    if ($postgresRunning) {
        Write-Info "Backing up database..."
        docker-compose -f docker-compose.production.yml exec -T postgres pg_dump -U asmblr asmblr | Out-File "$BackupDir/database.sql" -Encoding UTF8
    }
    
    # Backup configuration
    Copy-Item ".env.production" "$BackupDir/"
    Copy-Item "docker-compose.production.yml" "$BackupDir/"
    
    # Backup runs directory
    if (Test-Path "runs") {
        Copy-Item "runs" "$BackupDir/" -Recurse
    }
    
    Write-Status "Backup created: $BackupDir"
}

# Build and deploy
function Deploy-Application {
    Write-Info "Building and deploying application..."
    
    # Set production environment
    $env:DEPLOYMENT_ENV = $Environment
    
    # Pull latest images
    Write-Info "Pulling latest images..."
    docker-compose -f docker-compose.production.yml pull
    
    # Build application
    Write-Info "Building application..."
    docker-compose -f docker-compose.production.yml build --no-cache
    
    # Stop existing services
    Write-Info "Stopping existing services..."
    docker-compose -f docker-compose.production.yml down
    
    # Start services
    Write-Info "Starting services..."
    docker-compose -f docker-compose.production.yml up -d
    
    Write-Status "Application deployed"
}

# Health check
function Health-Check {
    Write-Info "Performing health checks..."
    
    $retryCount = 0
    $healthy = $false
    
    while ($retryCount -lt $MaxRetries) {
        try {
            $response = Invoke-WebRequest -Uri $HealthCheckUrl -UseBasicParsing -TimeoutSec 10
            if ($response.StatusCode -eq 200) {
                $healthy = $true
                break
            }
        } catch {
            # Continue retrying
        }
        
        $retryCount++
        Write-Info "Health check attempt $retryCount/$MaxRetries..."
        Start-Sleep $RetryDelay
    }
    
    if ($healthy) {
        Write-Status "Health check passed"
    } else {
        Write-Error "Health check failed after $MaxRetries attempts"
        return $false
    }
    
    return $true
}

# Post-deployment verification
function Post-Deployment-Verification {
    Write-Info "Running post-deployment verification..."
    
    # Check all services are running
    $services = @("asmblr", "postgres", "redis", "ollama", "nginx")
    foreach ($service in $services) {
        $running = docker-compose -f docker-compose.production.yml ps -q $service 2>$null
        if ($running) {
            Write-Status "Service $service is running"
        } else {
            Write-Error "Service $service is not running"
            return $false
        }
    }
    
    # Check application endpoints
    $endpoints = @(
        "http://localhost:8000/health",
        "http://localhost:8000/api/status",
        "http://localhost:8501"  # Streamlit
    )
    
    foreach ($endpoint in $endpoints) {
        try {
            $response = Invoke-WebRequest -Uri $endpoint -UseBasicParsing -TimeoutSec 10
            if ($response.StatusCode -eq 200) {
                Write-Status "Endpoint $endpoint is accessible"
            } else {
                Write-Warning "Endpoint $endpoint returned status $($response.StatusCode)"
            }
        } catch {
            Write-Warning "Endpoint $endpoint is not accessible"
        }
    }
    
    Write-Status "Post-deployment verification completed"
    return $true
}

# Rollback function
function Rollback {
    Write-Error "Deployment failed, initiating rollback..."
    
    # Stop current deployment
    docker-compose -f docker-compose.production.yml down
    
    # Restore from backup if available
    if (Test-Path $BackupDir) {
        Write-Info "Restoring from backup..."
        
        # Restore database
        if (Test-Path "$BackupDir/database.sql") {
            docker-compose -f docker-compose.production.yml up -d postgres
            Start-Sleep 10
            docker-compose -f docker-compose.production.yml exec -T postgres psql -U asmblr -c "DROP DATABASE IF EXISTS asmblr;" 2>$null
            docker-compose -f docker-compose.production.yml exec -T postgres psql -U asmblr -c "CREATE DATABASE asmblr;" 2>$null
            Get-Content "$BackupDir/database.sql" | docker-compose -f docker-compose.production.yml exec -T postgres psql -U asmblr asmblr
        }
        
        # Restore configuration
        Copy-Item "$BackupDir/.env.production" ".env.production"
        
        # Restart services
        docker-compose -f docker-compose.production.yml up -d
        
        Write-Status "Rollback completed"
    } else {
        Write-Error "No backup available for rollback"
    }
}

# Cleanup old backups
function Cleanup-Backups {
    Write-Info "Cleaning up old backups..."
    
    # Keep only last 7 days of backups
    Get-ChildItem "./backups" -Directory | Where-Object {
        $_.CreationTime -lt (Get-Date).AddDays(-7)
    } | Remove-Item -Recurse -Force
    
    Write-Status "Backup cleanup completed"
}

# Main deployment flow
try {
    Write-Info "Starting deployment process..."
    
    # Pre-deployment checks
    Pre-Deployment-Checks
    
    # Create backup
    Create-Backup
    
    # Deploy application
    if (-not (Deploy-Application)) {
        Rollback
        exit 1
    }
    
    # Health check
    if (-not (Health-Check)) {
        Rollback
        exit 1
    }
    
    # Post-deployment verification
    if (-not (Post-Deployment-Verification)) {
        Rollback
        exit 1
    }
    
    # Cleanup
    Cleanup-Backups
    
    Write-Host ""
    Write-Host "🎉 Deployment completed successfully!" -ForegroundColor $Colors.Green
    Write-Host "📊 Application is running at: http://localhost:8000" -ForegroundColor $Colors.Green
    Write-Host "🌐 UI available at: http://localhost:8501" -ForegroundColor $Colors.Green
    Write-Host "📈 Monitoring at: http://localhost:3001" -ForegroundColor $Colors.Green
    Write-Host ""
    Write-Host "Backup location: $BackupDir" -ForegroundColor $Colors.Blue
    Write-Host "To rollback: .\rollback.ps1 '$BackupDir'" -ForegroundColor $Colors.Blue
    
} catch {
    Write-Error "Deployment failed: $($_.Exception.Message)"
    Rollback
    exit 1
}
