#!/usr/bin/env python3
"""
Asmblr Public Setup Script
Simplified setup for public distribution with demo mode support
"""

import subprocess
import sys
import os
from pathlib import Path
import json


def print_banner():
    """Print welcome banner"""
    print("""
    🚀 Welcome to Asmblr - AI-Powered MVP Generator!
    
    Transform your ideas into launch-ready MVPs with AI automation.
    
    This setup will:
    ✓ Install Python dependencies
    ✓ Setup Ollama (if needed)
    ✓ Download AI models
    ✓ Configure environment
    ✓ Verify installation
    
    Let's get started! 🎯
    """)


def run_command(cmd, description="", check=True, capture_output=False):
    """Run a command with error handling"""
    print(f"\n🔧 {description}")
    print(f"🔧 Running: {cmd}")
    
    try:
        if capture_output:
            result = subprocess.run(cmd, shell=True, check=check, capture_output=True, text=True)
            if result.stdout:
                print(result.stdout)
            return result
        else:
            result = subprocess.run(cmd, shell=True, check=check)
            return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if hasattr(e, 'stderr') and e.stderr:
            print(f"❌ stderr: {e.stderr}")
        return False


def check_python_version():
    """Check Python version compatibility"""
    print("🐍 Checking Python version...")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print(f"❌ Python {version.major}.{version.minor} detected. Python 3.9+ is required.")
        print("Please upgrade Python and try again.")
        sys.exit(1)
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")


def install_dependencies():
    """Install Python dependencies"""
    print("\n📦 Installing Python dependencies...")
    
    # Upgrade pip
    if not run_command("python -m pip install --upgrade pip", "Upgrading pip"):
        return False
    
    # Install requirements
    if not run_command("python -m pip install -r requirements.txt", "Installing requirements"):
        return False
    
    print("✅ Dependencies installed successfully")
    return True


def check_ollama():
    """Check if Ollama is installed and running"""
    print("\n🤖 Checking Ollama...")
    
    # Check if Ollama is installed
    result = run_command("ollama --version", "Checking Ollama installation", 
                        check=False, capture_output=True)
    
    if not result or result.returncode != 0:
        print("❌ Ollama is not installed")
        return False, "not_installed"
    
    print(f"✅ {result.stdout.strip()}")
    
    # Check if Ollama is running
    try:
        import httpx
        with httpx.Client(timeout=5.0) as client:
            response = client.get("http://localhost:11434/api/tags")
            if response.status_code == 200:
                print("✅ Ollama is running")
                return True, "running"
    except Exception:
        pass
    
    print("⚠️  Ollama is installed but not running")
    return False, "not_running"


def install_ollama():
    """Install Ollama based on platform"""
    print("\n📥 Installing Ollama...")
    
    if sys.platform == "win32":
        print("🪟 Windows detected")
        print("Please download and install Ollama manually from: https://ollama.ai/download")
        print("After installation, restart your terminal and run this script again.")
        return False
    
    elif sys.platform == "darwin":
        print("🍎 macOS detected")
        return run_command(
            "curl -fsSL https://ollama.ai/install.sh | sh",
            "Installing Ollama on macOS"
        )
    
    elif sys.platform.startswith("linux"):
        print("🐧 Linux detected")
        return run_command(
            "curl -fsSL https://ollama.ai/install.sh | sh",
            "Installing Ollama on Linux"
        )
    
    else:
        print(f"❌ Unsupported platform: {sys.platform}")
        return False


def start_ollama():
    """Start Ollama service"""
    print("\n🚀 Starting Ollama...")
    
    if sys.platform == "win32":
        print("On Windows, Ollama should start automatically after installation.")
        print("If not running, check the Ollama application in your system tray.")
        return False
    else:
        return run_command(
            "ollama serve &",
            "Starting Ollama service",
            check=False
        )


def pull_models():
    """Download required AI models"""
    print("\n🧠 Downloading AI models...")
    
    models = [
        ("llama3.1:8b", "General purpose model"),
        ("qwen2.5-coder:7b", "Code generation model")
    ]
    
    for model, description in models:
        print(f"📥 Pulling {model} ({description})...")
        if not run_command(f"ollama pull {model}", f"Downloading {model}"):
            print(f"❌ Failed to pull {model}")
            return False
        print(f"✅ {model} downloaded successfully")
    
    return True


def setup_environment():
    """Setup environment configuration"""
    print("\n⚙️  Setting up environment...")
    
    # Check if .env exists
    env_file = Path(".env")
    env_example = Path(".env.example")
    env_public = Path(".env.public")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    # Copy appropriate template
    template_to_use = None
    if env_public.exists():
        template_to_use = env_public
        print("📋 Using public configuration template")
    elif env_example.exists():
        template_to_use = env_example
        print("📋 Using example configuration template")
    
    if template_to_use:
        with open(template_to_use, 'r') as src, open(env_file, 'w') as dst:
            dst.write(src.read())
        print(f"✅ Created .env from {template_to_use}")
    else:
        # Create minimal .env
        minimal_env = """# Asmblr Configuration
OLLAMA_BASE_URL=http://localhost:11434
GENERAL_MODEL=llama3.1:8b
CODE_MODEL=qwen2.5-coder:7b

# Demo Mode (recommended for first-time users)
DEMO_MODE=true
DEMO_TOPIC="AI-powered task management for remote teams"
DEMO_MAX_IDEAS=5
DEMO_FAST_MODE=true

# Basic Settings
DEFAULT_N_IDEAS=5
FAST_MODE=true
MAX_SOURCES=5
"""
        with open(env_file, 'w') as f:
            f.write(minimal_env)
        print("✅ Created minimal .env configuration")
    
    return True


def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    
    directories = ["runs", "data", "configs", "knowledge"]
    
    for dir_name in directories:
        dir_path = Path(dir_name)
        dir_path.mkdir(exist_ok=True)
        print(f"✅ Created directory: {dir_name}")
    
    return True


def verify_installation():
    """Verify the installation works"""
    print("\n🔍 Verifying installation...")
    
    try:
        # Test imports
        from app.core.config import get_settings
        from app.core.llm import LLMClient
        
        print("✅ Core modules imported successfully")
        
        # Test configuration
        settings = get_settings()
        print(f"✅ Configuration loaded: {len(vars(settings))} settings")
        
        # Test Ollama connection
        llm = LLMClient(settings.ollama_base_url, settings.general_model)
        if llm.available():
            print("✅ Ollama connection successful")
            
            # Test model generation (quick test)
            try:
                result = llm.generate('Say "hello"')
                print(f"✅ Model test successful: {result.strip()}")
            except Exception as e:
                print(f"⚠️  Model test failed: {e}")
                print("This might be normal if models are still loading")
        else:
            print("❌ Ollama connection failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False


def show_next_steps():
    """Show next steps to the user"""
    print("""
    🎉 Setup completed successfully!
    
    🚀 Next Steps:
    
    1. Start the Web Interface:
       streamlit run app/ui.py
    
    2. Open Your Browser:
       http://localhost:8501
    
    3. Generate Your First MVP:
       - Choose a topic or use the demo
       - Configure your preferences
       - Watch the AI agents work!
    
    💡 Tips:
    - Use Demo Mode for your first try (already configured)
    - Start with "Fast Mode" for quicker results
    - Check the runs/ directory for generated artifacts
    
    📚 Need Help?
    - README_PUBLIC.md for detailed documentation
    - CONTRIBUTING.md for development guidelines
    - GitHub Issues for support
    
    🌟 Enjoy building with AI!
    """)


def main():
    """Main setup function"""
    print_banner()
    
    # Check Python version
    check_python_version()
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Failed to install dependencies")
        sys.exit(1)
    
    # Setup environment
    if not setup_environment():
        print("❌ Failed to setup environment")
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Check and setup Ollama
    ollama_ok, ollama_status = check_ollama()
    
    if not ollama_ok:
        if ollama_status == "not_installed":
            if not install_ollama():
                print("❌ Failed to install Ollama")
                print("\n📖 Manual installation required:")
                print("1. Download Ollama from https://ollama.ai/download")
                print("2. Install it following the instructions")
                print("3. Restart your terminal")
                print("4. Run this script again")
                sys.exit(1)
        
        elif ollama_status == "not_running":
            if not start_ollama():
                print("⚠️  Could not start Ollama automatically")
                print("Please start Ollama manually: ollama serve")
                print("Then run this script again")
                sys.exit(1)
        
        # Re-check after installation/startup
        ollama_ok, ollama_status = check_ollama()
    
    # Pull models
    if ollama_ok:
        if not pull_models():
            print("⚠️  Failed to pull some models")
            print("You can pull them later with: ollama pull llama3.1:8b")
    
    # Verify installation
    if verify_installation():
        show_next_steps()
    else:
        print("\n⚠️  Setup completed with warnings")
        print("Some components may need manual configuration")
        print("Check the documentation for troubleshooting")
    
    print("\n✨ Setup complete! Happy building! 🚀")


if __name__ == "__main__":
    main()
