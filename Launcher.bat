@echo off
title Star Citizen Mining Analyzer - Launcher
color 0B

REM ===== Debug-Logging aktivieren =====
set DEBUG_LOG=launcher_debug.log
echo %DATE% %TIME% - Launcher gestartet > %DEBUG_LOG%

REM ===== Automatische Pfad-Erkennung =====
set BATCH_DIR=%~dp0
set PYTHON_FILE=%BATCH_DIR%mining_analyzer.py

echo.
echo ========================================================
echo  STAR CITIZEN MINING ANALYZER - WEBVIEW EDITION
echo ========================================================
echo  Moderne HTML/CSS Gaming-Overlay Technologie
echo ========================================================
echo.

echo [INFO] Automatische Pfad-Erkennung...
echo Batch-Ordner: %BATCH_DIR%
echo Python-Datei: %PYTHON_FILE%
echo.
echo %DATE% %TIME% - Pfad-Erkennung OK >> %DEBUG_LOG%

REM ===== Arbeitsverzeichnis setzen =====
cd /d "%BATCH_DIR%"
echo %DATE% %TIME% - Arbeitsverzeichnis gesetzt >> %DEBUG_LOG%

echo [INFO] Starte System-Checks fuer Webview-Edition...
echo.

REM ===== Python pruefen (verbesserte Methode) =====
echo [1/5] Pruefe Python Installation...
echo %DATE% %TIME% - Starte Python-Check >> %DEBUG_LOG%
set PYTHON_CMD=python
set PYTHON_FOUND=0

REM Teste python direkt ohne Umleitung (vermeidet "Zugriff verweigert")
python -c "import sys; print(sys.version)" >nul 2>nul
if %errorlevel% equ 0 (
    set PYTHON_CMD=python
    set PYTHON_FOUND=1
    echo [OK] Python gefunden
    echo %DATE% %TIME% - Python gefunden >> %DEBUG_LOG%
) else (
    REM Versuche py Launcher
    py -c "import sys; print(sys.version)" >nul 2>nul
    if %errorlevel% equ 0 (
        set PYTHON_CMD=py
        set PYTHON_FOUND=1
        echo [OK] Python Launcher gefunden
        echo %DATE% %TIME% - Python Launcher gefunden >> %DEBUG_LOG%
    ) else (
        echo [AUTO-INSTALL] Starte Python Installation...
        echo %DATE% %TIME% - Starte Python Auto-Install >> %DEBUG_LOG%
        call :install_python
        if errorlevel 1 (
            echo [ERROR] Python Installation fehlgeschlagen!
            echo %DATE% %TIME% - Python Installation fehlgeschlagen >> %DEBUG_LOG%
            pause
            exit /b 1
        )
        set PYTHON_CMD=python
        set PYTHON_FOUND=1
    )
)

if %PYTHON_FOUND% equ 0 (
    echo [ERROR] Python konnte nicht gefunden werden!
    echo %DATE% %TIME% - Python nicht gefunden >> %DEBUG_LOG%
    pause
    exit /b 1
)

REM ===== Python-Datei pruefen =====
echo [2/5] Pruefe mining_analyzer.py...
echo %DATE% %TIME% - Starte Datei-Check >> %DEBUG_LOG%
if not exist "%PYTHON_FILE%" (
    echo [ERROR] mining_analyzer.py nicht gefunden!
    echo.
    echo Gesucht in: %PYTHON_FILE%
    echo Batch-Verzeichnis: %BATCH_DIR%
    echo Aktuelles Verzeichnis: %CD%
    echo.
    echo Stelle sicher dass beide Dateien im gleichen Ordner sind:
    echo - %BATCH_DIR%Launcher.bat
    echo - %BATCH_DIR%mining_analyzer.py
    echo.
    echo %DATE% %TIME% - mining_analyzer.py nicht gefunden >> %DEBUG_LOG%
    pause
    exit /b 1
) else (
    echo [OK] mining_analyzer.py gefunden in: %BATCH_DIR%
    echo %DATE% %TIME% - mining_analyzer.py gefunden >> %DEBUG_LOG%
)

REM ===== Webview (Hauptkomponente) pruefen =====
echo [3/5] Pruefe Webview (HTML/CSS Engine)...
echo %DATE% %TIME% - Starte Webview-Check >> %DEBUG_LOG%
%PYTHON_CMD% -c "import webview; print('Webview Version:', webview.__version__)" >nul 2>nul
if errorlevel 1 (
    echo [WARNING] pywebview nicht installiert!
    echo [AUTO-INSTALL] Installiere moderne HTML/CSS Engine...
    echo.
    echo %DATE% %TIME% - pywebview nicht gefunden, starte Installation >> %DEBUG_LOG%

    %PYTHON_CMD% -m pip install pywebview
    if errorlevel 1 (
        echo [ERROR] pywebview Installation fehlgeschlagen!
        echo.
        echo MANUELLE INSTALLATION:
        echo 1. Oeffne Kommandozeile als Administrator
        echo 2. Fuehre aus: pip install pywebview
        echo 3. Starte Launcher erneut
        echo.
        echo %DATE% %TIME% - pywebview Installation fehlgeschlagen >> %DEBUG_LOG%
        pause
        exit /b 1
    ) else (
        echo [OK] pywebview erfolgreich installiert
        echo %DATE% %TIME% - pywebview installiert >> %DEBUG_LOG%
    )
) else (
    echo [OK] pywebview verfuegbar (moderne HTML/CSS UI)
    echo %DATE% %TIME% - pywebview bereits verfuegbar >> %DEBUG_LOG%
)

REM ===== Standard-Module pruefen =====
echo [4/5] Pruefe Standard-Module...
echo %DATE% %TIME% - Starte Standard-Module-Check >> %DEBUG_LOG%
%PYTHON_CMD% -c "import datetime, math, os, json, threading, time" >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Standard-Module fehlen!
    echo Python-Installation beschaedigt.
    echo %DATE% %TIME% - Standard-Module fehlen >> %DEBUG_LOG%
    pause
    exit /b 1
) else (
    echo [OK] Standard-Module verfuegbar
    echo %DATE% %TIME% - Standard-Module verfuegbar >> %DEBUG_LOG%
)

REM ===== Gaming-Features pruefen =====
echo [5/5] Pruefe Gaming-Features...
echo %DATE% %TIME% - Starte Gaming-Features-Check >> %DEBUG_LOG%

%PYTHON_CMD% -c "import pynput; print('PYNPUT_OK')" 2>nul
if errorlevel 1 (
    echo [AUTO-INSTALL] Installiere Gaming-Modus automatisch...
    echo %DATE% %TIME% - pynput nicht verfuegbar, starte automatische Installation >> %DEBUG_LOG%

    %PYTHON_CMD% -m pip install pynput
    if errorlevel 1 (
        echo [WARNING] Gaming-Modus Installation fehlgeschlagen
        echo [INFO] Clipboard-Modus bleibt verfuegbar
        echo %DATE% %TIME% - pynput Installation fehlgeschlagen >> %DEBUG_LOG%
    ) else (
        echo [OK] Gaming-Modus erfolgreich installiert
        echo %DATE% %TIME% - pynput Installation erfolgreich >> %DEBUG_LOG%
    )
) else (
    echo [OK] Gaming-Modus verfuegbar (globale Hotkeys)
    echo %DATE% %TIME% - pynput bereits verfuegbar >> %DEBUG_LOG%
)

echo %DATE% %TIME% - Gaming-Features-Check abgeschlossen >> %DEBUG_LOG%

echo.
echo ========================================================
echo  WEBVIEW-EDITION BEREIT!
echo ========================================================
echo.
echo %DATE% %TIME% - Alle Checks abgeschlossen >> %DEBUG_LOG%

echo NEUE FEATURES:
echo + Moderne HTML/CSS Benutzeroberflaeche
echo + Star Citizen-aehnliches Design
echo + Bessere Gaming-Overlay Technologie
echo + Responsive Layout fuer alle Bildschirmgroessen
echo + Professionelle Transparenz-Effekte
echo.

echo BEDIENUNG (wie gewohnt):
echo   Numpad 0-9    = Signalwerte eingeben
echo   Enter         = Signal analysieren
echo   Backspace     = Letzte Ziffer loeschen
echo   ESC           = Eingabe zuruecksetzen
echo.

echo GAMING-MODI:
echo   Gaming-Modus    = Globale Hotkeys (funktioniert in Star Citizen)
echo.

echo BEISPIEL-SIGNALE:
echo   1800 = Atacamite (Kupferhalogenid)
echo   3600 = Atacamite 2x Multima
echo   2400 = Hadanite (Edelstein)
echo   7200 = Hadanite 3x Multima
echo.

echo Starte in 3 Sekunden...
echo %DATE% %TIME% - Starte Countdown >> %DEBUG_LOG%
timeout /t 3 >nul

cls
echo.
echo [STARTING] Star Citizen Mining Analyzer - Webview Edition
echo Loading HTML/CSS Interface...
echo Initializing Gaming-Overlay Technology...
echo Starte von: %BATCH_DIR%
echo.
echo %DATE% %TIME% - Starte Python-Programm >> %DEBUG_LOG%

REM Versuche pythonw (ohne Console-Fenster) zu verwenden
where pythonw >nul 2>nul
if %errorlevel% equ 0 (
    echo [INFO] Starte im Hintergrund-Modus ohne Console...
    start "Mining Analyzer" /B pythonw "%PYTHON_FILE%"
    echo %DATE% %TIME% - Programm im Hintergrund gestartet >> %DEBUG_LOG%
    timeout /t 2 >nul
    exit
)

REM Fallback: Normale Python-Ausführung mit Start
echo [INFO] Starte Programm und schliesse Console...
start "Mining Analyzer" /B %PYTHON_CMD% "%PYTHON_FILE%"
echo %DATE% %TIME% - Programm gestartet, Console wird geschlossen >> %DEBUG_LOG%
timeout /t 2 >nul
exit

REM ===== Python Installation Funktion =====
:install_python
echo.
echo [DOWNLOAD] Lade Python herunter...
echo.
echo %DATE% %TIME% - Starte Python-Download >> %DEBUG_LOG%

powershell -Command "try { Write-Host 'Download startet...'; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe' -OutFile 'python_setup.exe' -UseBasicParsing; Write-Host 'Download abgeschlossen' } catch { Write-Host 'Download fehlgeschlagen:', $_.Exception.Message; exit 1 }"

if errorlevel 1 (
    echo [ERROR] Download fehlgeschlagen!
    echo Bitte Python manuell von python.org installieren
    echo %DATE% %TIME% - Python-Download fehlgeschlagen >> %DEBUG_LOG%
    exit /b 1
)

if exist "python_setup.exe" (
    echo.
    echo [INSTALL] Installiere Python...
    echo Bitte warten, dies dauert 2-5 Minuten...
    echo.
    echo %DATE% %TIME% - Starte Python-Installation >> %DEBUG_LOG%

    start /wait python_setup.exe /quiet InstallAllUsers=0 PrependPath=1 Include_test=0 Include_doc=0 Include_tcltk=1 Include_launcher=1

    echo [CLEANUP] Raeume auf...
    del "python_setup.exe" >nul 2>&1

    echo [OK] Python Installation abgeschlossen
    timeout /t 3 >nul
    echo %DATE% %TIME% - Python-Installation abgeschlossen >> %DEBUG_LOG%

    python -c "import sys; print(sys.version)" >nul 2>nul
    if errorlevel 1 (
        echo [WARNING] Python installiert, aber noch nicht im PATH
        echo Bitte Launcher neu starten
        echo %DATE% %TIME% - Python installiert aber nicht im PATH >> %DEBUG_LOG%
        pause
        exit /b 0
    ) else (
        echo [SUCCESS] Python erfolgreich konfiguriert
        echo %DATE% %TIME% - Python erfolgreich konfiguriert >> %DEBUG_LOG%
        exit /b 0
    )
) else (
    echo [ERROR] Setup-Datei nicht gefunden
    echo %DATE% %TIME% - Python Setup-Datei nicht gefunden >> %DEBUG_LOG%
    exit /b 1
)

goto :eof