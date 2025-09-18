#!/usr/bin/env python3
"""
AECOA Startup Script
Ensures all dependencies are available and starts the application
"""

import sys
import subprocess
import os

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = [
        'streamlit',
        'pyyaml', 
        'pillow',
        'pandas',
        'numpy',
        'ezdxf',
        'openai',
        'requests',
        'toml'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            # Handle package name differences
            package_map = {
                'pillow': 'PIL',
                'pyyaml': 'yaml'
            }
            try:
                __import__(package_map.get(package, package))
            except ImportError:
                missing_packages.append(package)
    
    return missing_packages

def install_missing_packages(packages):
    """Install missing packages"""
    if not packages:
        return True
        
    print(f"Installing missing packages: {', '.join(packages)}")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "--upgrade", *packages
        ])
        return True
    except subprocess.CalledProcessError:
        return False

def check_environment():
    """Check if the environment is properly set up"""
    print("🔍 Checking AECOA environment...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    
    # Check dependencies
    missing = check_dependencies()
    if missing:
        print(f"⚠️  Missing packages: {', '.join(missing)}")
        print("📦 Installing missing packages...")
        if install_missing_packages(missing):
            print("✅ All packages installed")
        else:
            print("❌ Failed to install packages")
            return False
    else:
        print("✅ All dependencies available")
    
    # Check core files
    core_files = [
        'app.py',
        'agents/auth/auth.py',
        'agents/orchestrator.py',
        'agents/extractors/agent1_parameter_definition.py',
        'agents/providers.py',
        'agents/model_manager.py'
    ]
    
    for file in core_files:
        if not os.path.exists(file):
            print(f"❌ Missing core file: {file}")
            return False
    print("✅ All core files present")
    
    return True

def start_application():
    """Start the Streamlit application"""
    print("🚀 Starting AECOA application...")
    try:
        # Import streamlit to verify it's working
        import streamlit as st
        
        # Start the app
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.address", "0.0.0.0",
            "--server.port", "8501"
        ])
    except Exception as e:
        print(f"❌ Failed to start application: {e}")
        return False

def main():
    """Main startup function"""
    print("🏗️  AECOA - AI-Enhanced Compliance & Optimization Assistant")
    print("=" * 60)
    
    # Change to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    print(f"📁 Working directory: {script_dir}")
    
    # Check environment
    if not check_environment():
        print("❌ Environment check failed")
        sys.exit(1)
    
    print("✅ Environment ready!")
    print("🌐 Starting web interface...")
    print("   • URL: http://localhost:8501")
    print("   • Press Ctrl+C to stop")
    print("-" * 60)
    
    # Start application
    start_application()

if __name__ == "__main__":
    main()