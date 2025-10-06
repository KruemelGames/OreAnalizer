@echo off
title EasyPeasyScanny - Launcher
color 0B
setlocal ENABLEDELAYEDEXPANSION
set LOG=Launcher_debug.log
echo %DATE% %TIME%  Launcher gestartet > "%LOG%"
set "ROOT=%~dp0"
cd /d "%ROOT%"
set "MAIN_PY=%ROOT%main.py"
set "PYEXE="
where py >NUL 2>&1 && (py -3.13 -c "print(1)" >NUL 2>&1) && set "PYEXE=py -3.13"
if not defined PYEXE ( where py >NUL 2>&1 && set "PYEXE=py -3" )
if not defined PYEXE ( where python >NUL 2>&1 && set "PYEXE=python" )
if not defined PYEXE (
  echo [ERROR] Python nicht gefunden. Bitte installiere Python 3.13.
  start "" "https://www.python.org/downloads/"
  pause & exit /b 1
)
for /f "tokens=2 delims= " %%v in ('%PYEXE% -V 2^>^&1') do set "PYVER=%%v"
if not exist ".venv" ( %PYEXE% -m venv .venv ) || (echo [ERROR] venv fehlgeschlagen >> "%LOG%" & pause & exit /b 1)
call ".venv\Scripts\activate.bat" || (echo [ERROR] venv-Aktivierung fehlgeschlagen >> "%LOG%" & pause & exit /b 1)
python -m pip install --upgrade pip >NUL 2>>"%LOG%"
if exist "requirements.txt" ( python -m pip install -r requirements.txt ) else ( python -m pip install pywebview keyboard pynput >NUL 2>>"%LOG%" )
where pythonw >NUL 2>&1
if %ERRORLEVEL%==0 (
  start "EasyPeasyScanny" /B pythonw "%MAIN_PY%"
  timeout /t 2 >NUL
  exit /b 0
) else (
  %PYEXE% "%MAIN_PY%"
  set "EXITCODE=%ERRORLEVEL%"
  echo Beendet (Code %EXITCODE%). Taste druecken zum Schliessen.
  pause >NUL
  exit /b %EXITCODE%
)
