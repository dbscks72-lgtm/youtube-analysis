@echo off
title YouTube Channel Analysis
pushd "%~dp0"

if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] venv not found. Run these commands first:
    echo   python -m venv venv
    echo   venv\Scripts\activate
    echo   pip install -r requirements.txt
    pause
    popd
    exit /b 1
)

call venv\Scripts\activate.bat
streamlit run app.py --server.address 127.0.0.1
popd
pause
