@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

REM --- Farben definieren ---
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
    set "m_name=" & set "m_iwad="
    set "m_fold=%%~nxD"
    set "m_fold=!m_fold: =!"
    
    echo %Y%VERARBEITE ORDNER:%W% %CY%%%~nxD%W%
    
    REM Automatisches Auslesen des Titels und der IWAD aus .txt Dateien
    for %%F in ("%%~fD\*.txt") do (
        if "!m_name!"=="" (
            for /f "usebackq tokens=*" %%A in (`powershell -command "$c = Get-Content '%%~fF'; $line = $c | Select-String 'Title\s*:' | Select-Object -First 1; if($line){ $val = $line.ToString().Split(':',2)[1].Trim(); (Get-Culture).TextInfo.ToTitleCase($val.ToLower()) }"`) do set "m_name=%%A"
        )
        if "!m_iwad!"=="" (
            for /f "usebackq tokens=*" %%G in (`powershell -command "$c = Get-Content '%%~fF'; $line = $c | Select-String 'Game\s*:' | Select-Object -First 1; if($line){ $v = $line.ToString().Split(':',2)[1].Trim().ToLower(); if($v -eq 'doom'){ 'doom.wad' } elseif($v -match 'doom2'){ 'doom2.wad' } }"`) do set "m_iwad=%%G"
        )
    )

    if "!m_name!"=="" set "m_name=%%~nxD"
    set "targetPath=%PWAD_BASE%\!m_fold!"
    set "alreadyExists=0"

    findstr /C:",!m_name!," "%CSV_FILE%" >nul 2>&1
    if !errorlevel! EQU 0 set "alreadyExists=1"
    if exist "!targetPath!" set "alreadyExists=1"

    if "!alreadyExists!"=="1" (
        echo    %Y%-- Karte bereits vorhanden. Überspringe...%W%
    ) else (
        REM Nur wenn PowerShell nichts gefunden hat, manuell fragen
        if "!m_iwad!"=="" call :manual_selector "!m_name!"
        
        if not exist "!targetPath!" mkdir "!targetPath!"
        move /y "%%~fD\*.*" "!targetPath!\" >nul 2>&1
        
        call :update_db "!m_name!" "!m_iwad!" "!m_fold!"
        echo    %G%-- Trage Karteninformation in die csv ein: %W%[!id!, !m_iwad!, !m_name!, !m_fold!\]
    )
    rd /s /q "%%~fD"
)

REM --- Einzeldateien (.wad/.pk3) verarbeiten ---
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
echo   %R%-- IWAD-Wahl erforderlich für: %CY%%~1%W%
set "choice=2"
set /p "choice=      1:Doom1  2:Doom2  3:Plutonia  4:TNT (Standard: 2): "
if "!choice!"=="1" (set "m_iwad=doom.wad") else if "!choice!"=="3" (set "m_iwad=plutonia.wad") else if "!choice!"=="4" (set "m_iwad=tnt.wad") else (set "m_iwad=doom2.wad")
exit /b

:update_db
set "id=0"
for /f "tokens=1 delims=," %%I in ('type "%CSV_FILE%"') do (
    set /a "val=%%I" 2>nul
    if !val! GTR !id! set "id=!val!"
)
set /a id+=1

set "tmpCSV=%CSV_FILE%.tmp"
set "targetLine=0"

REM Sucht die letzte Leerzeile (Trennlinie zum 3. Block)
for /f "tokens=1 delims=:" %%A in ('findstr /n "^$" "%CSV_FILE%"') do set "targetLine=%%A"

if !targetLine! EQU 0 (
    echo !id!,%~2,%~1,0,%~3\ >> "%CSV_FILE%"
) else (
    (for /f "usebackq tokens=1* delims=:" %%A in (`findstr /n "^" "%CSV_FILE%"`) do (
        if %%A EQU !targetLine! echo !id!,%~2,%~1,0,%~3\
        echo(%%B
    )) > "%tmpCSV%"
    move /y "%tmpCSV%" "%CSV_FILE%" >nul
)
exit /b

:restore_logic
if exist "%CSV_FILE%.bak" (
    copy /y "%CSV_FILE%.bak" "%CSV_FILE%" >nul
    echo %G%Backup erfolgreich wiederhergestellt.%W%
) else (
    echo %R%Kein Backup gefunden.%W%
)
pause
goto :main_menu