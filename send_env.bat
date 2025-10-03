@echo off
setlocal

REM Check for virtual environment and set Python executable
set PYTHON_EXE=python

if exist "venv\Scripts\python.exe" (
    set PYTHON_EXE=venv\Scripts\python.exe
) else if exist ".venv\Scripts\python.exe" (
    set PYTHON_EXE=.venv\Scripts\python.exe
) else if exist "env\Scripts\python.exe" (
    set PYTHON_EXE=env\Scripts\python.exe
) else if exist ".env\Scripts\python.exe" (
    set PYTHON_EXE=.env\Scripts\python.exe
)

echo Using Python: %PYTHON_EXE%
echo.

set /p HOST="Enter iPhone IP address or hostname: "

if "%HOST%"=="" (
    echo ERROR: HOST cannot be empty
    pause
    exit /b 1
)

%PYTHON_EXE% iphone_env_sender.py %HOST%

pause

