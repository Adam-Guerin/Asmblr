#!/usr/bin/env python3
"""
Asmblr Setup Script
Installs dependencies and sets up Ollama
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description="", check=True):
    """Run a command and handle errors."""
    print(f"\n{'='*50}")
    print(f"🔧 {description}")
    print(f"🔧 Running: {cmd}")
    print('='*50)
    
    try:
        result = subprocess.run(cmd, shell=True, check=check, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stderr:
            print(f"❌ stderr: {e.stderr}")
        return False

def check_ollama_installed():
    """Check if Ollama is installed."""
    try:
        result = subprocess.run(["ollama", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Ollama is installed: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    print("❌ Ollama is not installed")
    return False

def install_ollama():
    """Install Ollama based on the platform."""
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

def check_ollama_running():
    """Check if Ollama service is running."""
    try:
        import httpx
        with httpx.Client(timeout=5.0) as client:
            response = client.get("http://localhost:11434/api/tags")
            if response.status_code == 200:
                print("✅ Ollama service is running")
                return True
    except Exception as e:
        print(f"❌ Ollama service not running: {e}")
        return False

def start_ollama():
    """Start Ollama service."""
    print("\n🚀 Starting Ollama service...")
    
    if sys.platform == "win32":
        print("On Windows, Ollama should start automatically after installation.")
        print("If not running, check the Ollama application in your system tray.")
        return False
    else:
        # For Unix-like systems, try to start as background service
        return run_command(
            "ollama serve &",
            "Starting Ollama service",
            check=False
        )

def pull_models():
    """Download required models."""
    models = ["llama3.1:8b", "qwen2.5-coder:7b"]
    
    for model in models:
        print(f"\n📥 Pulling model: {model}")
        if not run_command(f"ollama pull {model}", f"Downloading {model}"):
            print(f"❌ Failed to pull {model}")
            return False
        print(f"✅ Successfully pulled {model}")
    
    return True

def install_python_deps():
    """Install Python dependencies."""
    print("\n🐍 Installing Python dependencies...")
    
    # Upgrade pip
    run_command("python -m pip install --upgrade pip", "Upgrading pip")
    
    # Install requirements
    if not run_command("python -m pip install -r requirements.txt", "Installing requirements"):
        return False
    
    return True

def create_directories():
    """Create necessary directories."""
    print("\n📁 Creating directories...")
    
    dirs = ["runs", "data", "configs", "knowledge"]
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)
        print(f"✅ Created directory: {dir_name}")

def main():
    """Main setup function."""
    print("🚀 Asmblr Setup Script")
    print("="*50)
    
    # Check if we're in the right directory
    if not Path("requirements.txt").exists():
        print("❌ requirements.txt not found. Please run this script from the Asmblr root directory.")
        sys.exit(1)
    
    # Step 1: Install Python dependencies
    if not install_python_deps():
        print("❌ Failed to install Python dependencies")
        sys.exit(1)
    
    # Step 2: Create directories
    create_directories()
    
    # Step 3: Check/Install Ollama
    if not check_ollama_installed():
        if not install_ollama():
            print("❌ Failed to install Ollama")
            print("\n📝 Manual installation required:")
            print("1. Download Ollama from https://ollama.ai/download")
            print("2. Install it following the instructions")
            print("3. Restart your terminal")
            print("4. Run this script again")
            sys.exit(1)
    
    # Step 4: Check if Ollama is running
    if not check_ollama_running():
        if not start_ollama():
            print("⚠️ Could not start Ollama automatically")
            print("Please start Ollama manually by running: ollama serve")
            
            # Wait a bit and check again
            import time
            time.sleep(5)
            if not check_ollama_running():
                print("❌ Ollama is still not running")
                sys.exit(1)
    
    # Step 5: Pull models
    if not pull_models():
        print("❌ Failed to pull required models")
        sys.exit(1)
    
    # Step 6: Final verification
    print("\n🔍 Final verification...")
    
    # Test Python imports
    try:
        from app.core.llm import LLMClient
        llm = LLMClient('http://localhost:11434', 'llama3.1:8b')
        if llm.available():
            result = llm.generate('Say "hello"')
            print(f"✅ LLM test successful: {result.strip()}")
        else:
            print("❌ LLM not available")
            sys.exit(1)
    except Exception as e:
        print(f"❌ LLM test failed: {e}")
        sys.exit(1)
    
    print("\n" + "="*50)
    print("🎉 Setup completed successfully!")
    print("="*50)
    print("\n📋 Next steps:")
    print("1. Start the UI: streamlit run ui.py")
    print("2. Open your browser to http://localhost:8501")
    print("3. Generate your first MVP!")
    print("\n💡 Tip: Make sure Ollama is running before starting the UI")

if __name__ == "__main__":
    main()
