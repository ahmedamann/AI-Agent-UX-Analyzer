#!/usr/bin/env python3
"""
AI Agent UX Analyzer - Startup Script

Simple script to launch the Streamlit web application.
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Launch the Streamlit application."""
    print("🚀 Starting AI Agent UX Analyzer...")
    print("📱 Opening web interface...")
    print("🌐 The app will open in your browser automatically")
    print("⏹️  Press Ctrl+C to stop the application")
    print("-" * 50)
    
    try:
        # Run streamlit app
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
            "--server.port", "8501",
            "--server.headless", "false"
        ])
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        print("💡 Make sure you have activated the conda environment: conda activate jobenv")

if __name__ == "__main__":
    main() 