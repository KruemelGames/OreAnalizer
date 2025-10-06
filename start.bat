\
    @echo off
    setlocal ENABLEDELAYEDEXPANSION
    REM ==== EasyPeasyScanny bootstrap ====
    REM Creates a venv, installs requirements, then runs main.py

    REM Resolve project root (folder of this .bat)
    set "PROJ_DIR=%~dp0"
    pushd "%PROJ_DIR%"

    echo [1/6] Checking Python...
    set "PYCMD="

    REM Prefer Python launcher (Windows Store / official)
    where py >NUL 2>&1
    if %ERRORLEVEL%==0 (
        set "PYCMD=py -3"
    ) else (
        REM Fallback to python.exe on PATH
        where python >NUL 2>&1
        if %ERRORLEVEL%==0 (
            set "PYCMD=python"
        ) else (
            echo ERROR: Python 3 not found. Please install from https://www.python.org/downloads/
            pause
            exit /b 1
        )
    )

    for /f "tokens=2 delims= " %%v in ('%PYCMD% -V 2^>^&1') do set "PYVER=%%v"
    echo Detected Python: %PYVER%

    REM 2) Create venv if missing
    if not exist ".venv" (
        echo [2/6] Creating virtual environment...
        %PYCMD% -m venv .venv
        if errorlevel 1 (
            echo ERROR: Failed to create virtual environment.
            pause
            exit /b 1
        )
    ) else (
        echo [2/6] Using existing virtual environment.
    )

    REM 3) Activate venv
    call ".venv\Scripts\activate.bat"
    if errorlevel 1 (
        echo ERROR: Failed to activate virtual environment.
        pause
        exit /b 1
    )

    REM 4) Ensure pip is up-to-date
    echo [3/6] Upgrading pip...
    python -m pip install --upgrade pip
    if errorlevel 1 (
        echo WARNING: Could not upgrade pip. Continuing...
    )

    REM 5) Install requirements (if file exists)
    if exist "requirements.txt" (
        echo [4/6] Installing requirements...
        python -m pip install -r requirements.txt
        if errorlevel 1 (
            echo.
            echo ERROR: Failed to install required packages.
            echo If you have no internet connection, try running again later.
            echo.
            pause
            exit /b 1
        )
    ) else (
        echo [4/6] No requirements.txt found. Skipping dependency installation.
    )

    REM 6) Run the app
    echo [5/6] Launching EasyPeasyScanny...
    python main.py
    set "EXITCODE=%ERRORLEVEL%"
    echo [6/6] Application exited with code %EXITCODE%

    REM Keep window open so users can read output
    echo.
    echo Press any key to close this window.
    pause >NUL
    popd
    exit /b %EXITCODE%
