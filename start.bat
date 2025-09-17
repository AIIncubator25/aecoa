@echo off
echo 🏗️  AECOA - AI-Enhanced Compliance ^& Optimization Assistant
echo ==========================================================

echo 📁 Checking current directory...
if not exist "app.py" (
    echo ❌ app.py not found. Please run this from the AECOA directory.
    pause
    exit /b 1
)

echo ✅ AECOA directory confirmed

echo 🐍 Activating Python environment...
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    echo ✅ Virtual environment activated
) else if exist "py3106" (
    echo 📦 Using conda environment py3106...
    call conda activate py3106
) else (
    echo ⚠️  No virtual environment found, using system Python
)

echo 📦 Installing/updating dependencies...
pip install -r requirements.txt --quiet --upgrade

echo 🚀 Starting AECOA application...
echo 🌐 Opening web interface at: http://localhost:8501
echo ⏹️  Press Ctrl+C to stop the application
echo.

streamlit run app.py --server.address 0.0.0.0 --server.port 8501

pause