@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

set "ESC= "
for /f %%a in ('echo prompt $E ^| cmd') do set "ESC=%%a"
set "G=%ESC%[92m" & set "Y=%ESC%[93m" & set "B=%ESC%[94m" & set "R=%ESC%[91m" & set "W=%ESC%[0m"
set "CY=%ESC%[96m" & set "GRA=%ESC%[90m"

set "INSTALL_DIR=Install"
set "PWAD_BASE=pwad"
set "CSV_FILE=maps.csv"

:main_menu
cls
echo %B%------------------------------------------------------%W%
echo                  %CY%DOOM MAP INSTALLER%W%
echo %B%------------------------------------------------------%W%
echo.
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

set "found_files=0"
for /f %%A in ('dir /b /a "%INSTALL_DIR%" 2^>nul') do set "found_files=1"

if "%found_files%"=="0" (
    echo   %Y%i STATUS: Keine neuen Dateien gefunden.%W%
    echo.
    echo   1 - Beenden
    echo   2 - CSV-Backup wiederherstellen
    echo.
    set /p "opt=  Auswahl: "
    if "!opt!"=="2" goto :restore_logic
    exit /b
)

echo %G%* Scanne %B%%INSTALL_DIR%%W% nach neuen Karten...%W%
if exist "%CSV_FILE%" copy /y "%CSV_FILE%" "%CSV_FILE%.bak" >nul 2>&1

REM --- Archive entpacken ---
set "zip_found=0"
for %%Z in ("%INSTALL_DIR%\*.zip" "%INSTALL_DIR%\*.7z" "%INSTALL_DIR%\*.rar") do set "zip_found=1"
if "%zip_found%"=="1" (
    echo %G%* Archive erkannt. Entpacke...%W%
    for %%Z in ("%INSTALL_DIR%\*.zip" "%INSTALL_DIR%\*.7z" "%INSTALL_DIR%\*.rar") do (
        echo     %GRA%-- Entpacke: %%~nxZ%W%
        set "targetZipDir=%INSTALL_DIR%\%%~nZ"
        if not exist "!targetZipDir!" mkdir "!targetZipDir!"
        tar -xf "%%Z" -C "!targetZipDir!" >nul 2>&1
        del "%%Z"
    )
)

REM --- Ordner verarbeiten ---
for /d %%D in ("%INSTALL_DIR%\*") do (
    set "m_name="
    set "m_iwad="
    set "m_fold=%%~nxD"
    set "m_fold=!m_fold: =!"
    set "currentFullDir=%%~fD"

    echo %Y%ÜBERPRÜFE STRUKTUR:%W% %CY%!m_fold!%W%

    pushd "!currentFullDir!"
    for /r %%F in (*.txt) do (
        if "!m_name!"=="" (
            for /f "usebackq tokens=*" %%A in (`powershell -command "$c = Get-Content '%%~fF'; $line = $c | Select-String 'Title\s*:' | Select-Object -First 1; if($line){ $val = $line.ToString().Split(':',2)[1].Trim(); (Get-Culture).TextInfo.ToTitleCase($val.ToLower()) }"`) do set "m_name=%%A"
        )
        if "!m_iwad!"=="" (
            for /f "usebackq tokens=*" %%G in (`powershell -command "$c = Get-Content '%%~fF'; $line = $c | Select-String 'Game\s*:' | Select-Object -First 1; if($line){ $v = $line.ToString().Split(':',2)[1].Trim().ToLower(); if($v -match 'heretic'){ 'heretic.wad' } elseif($v -match 'hexen'){ 'hexen.wad' } elseif($v -match 'doom2'){ 'doom2.wad' } elseif($v -match 'doom'){ 'doom.wad' } }"`) do set "m_iwad=%%G"
        )
    )
    popd

    if "!m_name!"=="" set "m_name=!m_fold!"
    set "targetPath=%PWAD_BASE%\!m_fold!"
    set "alreadyExists=0"

    findstr /C:",!m_name!," "%CSV_FILE%" >nul 2>&1
    if !errorlevel! EQU 0 set "alreadyExists=1"
    if exist "!targetPath!" set "alreadyExists=1"

    if "!alreadyExists!"=="1" (
        echo   %Y%-- Karte bereits vorhanden. Überspringe...%W%
    ) else (
        if "!m_iwad!"=="" call :manual_selector "!m_name!"
        if not exist "!targetPath!" mkdir "!targetPath!"
        
        echo     %GRA%-- Sammle Dateien aus Unterordnern...%W%
        pushd "!currentFullDir!"
        for /r %%f in (*.wad *.pk3 *.txt *.deh *.bex) do (
            move /y "%%f" "..\..\!targetPath!\" >nul 2>&1
        )
        popd
        
        call :update_db "!m_name!" "!m_iwad!" "!m_fold!"
        echo    %G%-- Erfolg: !id! - !m_name! installiert.%W%
    )
    rd /s /q "!currentFullDir!" 2>nul
)

REM --- Einzeldateien verarbeiten ---
for %%W in ("%INSTALL_DIR%\*.wad" "%INSTALL_DIR%\*.pk3") do (
    set "m_name=%%~nW"
    set "m_fold=%%~nW"
    set "m_fold=!m_fold: =!"
    echo %Y%VERARBEITE DATEI:%W% %CY%%%~nxW%W%
    
    set "alreadyExists=0"
    findstr /C:",!m_name!," "%CSV_FILE%" >nul 2>&1
    if !errorlevel! EQU 0 set "alreadyExists=1"
    if exist "%PWAD_BASE%\!m_fold!" set "alreadyExists=1"

    if "!alreadyExists!"=="1" (
        echo   %Y%-- Bereits vorhanden. Lösche Quelldatei...%W%
        del /f /q "%%~fW"
    ) else (
        call :manual_selector "!m_name!"
        set "targetPath=%PWAD_BASE%\!m_fold!"
        if not exist "!targetPath!" mkdir "!targetPath!"
        move /y "%%~fW" "!targetPath!\" >nul 2>&1
        call :update_db "!m_name!" "!m_iwad!" "!m_fold!"
        echo   %G%-- ERFOLG: !id! - !m_name! installiert.%W%
    )
)

echo.
echo %G%Installation abgeschlossen.%W%
pause
exit /b

:manual_selector
echo   %R%-- IWAD-Wahl erforderlich für: %CY% %~1%W%
echo.
echo       1: Doom 1 (doom.wad)
echo       2: Doom 2 (doom2.wad)
echo       3: Heretic (heretic.wad)
echo       4: Hexen (hexen.wad)
echo       5: Plutonia (plutonia.wad)
echo       6: TNT (tnt.wad)
echo.
set "choice=2"
set /p "choice=      Auswahl (Standard: 2): "
if "!choice!"=="1" (set "m_iwad=doom.wad") else if "!choice!"=="3" (set "m_iwad=heretic.wad") else if "!choice!"=="4" (set "m_iwad=hexen.wad") else if "!choice!"=="5" (set "m_iwad=plutonia.wad") else if "!choice!"=="6" (set "m_iwad=tnt.wad") else (set "m_iwad=doom2.wad")
exit /b

:update_db
set "blockTarget=2"
set "prefix="
if /i "%~2"=="heretic.wad" (set "blockTarget=3" & set "prefix=h")
if /i "%~2"=="hexen.wad"   (set "blockTarget=4" & set "prefix=hx")

set "newNum=10"
if /i "%prefix%"=="h" (set "newNum=100")
if /i "%prefix%"=="hx" (set "newNum=200")

set "currentB=1"
for /f "usebackq tokens=1* delims=:" %%A in (`findstr /n "^" "%CSV_FILE%"`) do (
    set "ln=%%B"
    if "!ln!"=="" (
        set /a currentB+=1
    ) else (
        REM Wir prüfen den Block und extrahieren die ID
        for /f "tokens=1 delims=," %%I in ("!ln!") do (
            set "idStr=%%I"
            set "numOnly=!idStr!"
            if defined prefix (
                set "numOnly=!idStr:%prefix%=!"
            )
            
            REM Nur verarbeiten, wenn es eine Zahl ist
            set /a "checkNum=!numOnly!" 2>nul
            if !errorlevel! EQU 0 (
                if !checkNum! GTR !newNum! set "newNum=!checkNum!"
            )
        )
    )
)

set /a newNum+=1
set "id=!prefix!!newNum!"

set "foundBlock=0"
set "tmpCSV=%CSV_FILE%.tmp"
set "currentB=1"

(
    for /f "usebackq tokens=1* delims=:" %%A in (`findstr /n "^" "%CSV_FILE%"`) do (
        set "ln=%%B"
        if "!ln!"=="" (
            if !currentB! EQU !blockTarget! (
                echo !id!,%~2,%~1,0,%~3\
                set "foundBlock=1"
            )
            set /a currentB+=1
        )
        echo(!ln!
    )
    if "!foundBlock!"=="0" if !currentB! LSS !blockTarget! echo !id!,%~2,%~1,0,%~3\
) > "%tmpCSV%"
move /y "%tmpCSV%" "%CSV_FILE%" >nul
exit /b

:restore_logic
if exist "%CSV_FILE%.bak" (
    copy /y "%CSV_FILE%.bak" "%CSV_FILE%" >nul
    echo %G%Backup erfolgreich wiederhergestellt.%W%
) else (echo %R%Kein Backup gefunden.%W%)
pause
goto :main_menu