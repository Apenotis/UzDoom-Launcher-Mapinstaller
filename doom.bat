@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM --- ANSI FARBEN INITIALISIEREN ---
reg add "HKCU\Console" /v VirtualTerminalLevel /t REG_DWORD /d 1 /f >nul 2>&1

set "ESC= "
for /f %%a in ('echo prompt $E ^| cmd') do set "ESC=%%a"

set "R=%ESC%[91m"
set "G=%ESC%[92m"
set "Y=%ESC%[93m"
set "B=%ESC%[94m"
set "CY=%ESC%[96m"
set "MAG=%ESC%[95m"
set "W=%ESC%[0m"
set "GRA=%ESC%[90m"

REM --- EINSTELLUNGEN ---
set "show_stats=1"
set "USE_MODS=1"

set "CSV_FILE=maps.csv"
set "IWAD_DIR=%~dp0iwad"
set "PWAD_DIR=%~dp0pwad"
set "UZ=%~dp0UzDoom\uzdoom.exe"
set "CUR_VERSION=4.14.3"
set "TIME_FILE=total_time.txt"

if not exist "%TIME_FILE%" (echo 0> "%TIME_FILE%")
set /p totalMinutes=<"%TIME_FILE%"
if "!totalMinutes!"=="" set "totalMinutes=0"

REM --- UPDATE CHECK (JEDER START) ---
set "updateAvailable=0"
for /f "delims=" %%v in ('powershell -command "$v = (Invoke-RestMethod -Uri 'https://api.github.com/repos/UZDoom/UZDoom/releases/latest').tag_name; echo $v" 2^>nul') do set "latest_version=%%v"
if defined latest_version (
    if not "!latest_version!"=="%CUR_VERSION%" set "updateAvailable=1"
)

:map_selection
title UZDoom Launcher
cls

set "currentError=!lastWrongID!"
set "lastWrongID="

REM Nur Formatierung, keine Berechnung hier!
for /f "tokens=1" %%a in ('powershell -command "$t=[int]!totalMinutes!; $h=[math]::Floor($t/3600); $m=[math]::Floor(($t%%3600)/60); $s=$t%%60; '{0:D2}:{1:D2}:{2:D2}' -f [int]$h,[int]$m,[int]$s"') do set "displayTime=%%a"

set "C_Cyan=%ESC%[36m"
set "C_Green=%ESC%[32m"
set "C_Yellow=%ESC%[33m"
set "C_Reset=%ESC%[0m"

set "lastID="
set "lastName="
if exist "last_played.txt" (
    set /p lastID=<"last_played.txt"
    for /f "usebackq skip=1 tokens=1,2,3 delims=," %%a in ("%CSV_FILE%") do (
        if /i "%%a"=="!lastID!" set "lastName=%%c"
    )
)

echo.
echo  %C_Cyan%============================================================================================================================================================================================================
echo      I W A D S                                   ^| P W A D S                                     ^| P W A D S                                     ^| H E R E T I C / H E X E N / W O L F
echo  ============================================================================================================================================================================================================%C_Reset%

for /L %%i in (1,1,400) do (
    set "col1[%%i]=" & set "col2[%%i]=" & set "col3[%%i]=" & set "col4[%%i]=" & set "tempPWAD[%%i]="
)

set "idx1=0" & set "idx2=0" & set "idx3=0" & set "idx4=0" & set "pCount=0"
set "countD1=0" & set "countD2=0" & set "countExtra=0" & set "modTotalCount=0"

for %%S in (doom heretic hexen wolfenstein) do (
    if exist "mods\%%S\" (
        for /d %%D in ("mods\%%S\*") do set /a modTotalCount+=1
    )
)

set "block=1"
for /f "usebackq tokens=1* delims=:" %%L in (`findstr /n "^" "%CSV_FILE%"`) do (
    set "line=%%M"
    if "!line!"=="" (
        set /a block+=1
        if !block! GTR 3 (
            set /a idx4+=1
            set "col4[!idx4!]=EMPTY"
            set "col4_block[!idx4!]=!block!"
        )
    ) else (
        if /i not "!line:~0,2!"=="ID" (
            for /f "tokens=1,2,3 delims=," %%a in ("!line!") do (
                set "entry=%%a - %%c"
                if !block! EQU 1 (
                    set /a idx1+=1 & set /a countD1+=1
                    set "col1[!idx1!]=!entry!"
                ) else if !block! EQU 2 (
                    set /a pCount+=1 & set /a countD2+=1
                    set "tempPWAD[!pCount!]=!entry!"
                ) else (
                    set /a idx4+=1 & set /a countExtra+=1
                    set "col4[!idx4!]=!entry!"
                    set "col4_block[!idx4!]=!block!"
                )
            )
        )
    )
)

set /a "totalMaps=countD1 + countD2 + countExtra"

if !pCount! GTR 0 (
    set /a "half=(pCount + 1) / 2"
    for /L %%i in (1,1,!half!) do (
        set "col2[%%i]=!tempPWAD[%%i]!"
        set /a "rIdx=%%i + half"
        if !rIdx! LEQ !pCount! (
            for %%v in (!rIdx!) do set "col3[%%i]=!tempPWAD[%%v]!"
        )
    )
    set "idx2=!half!" & set "idx3=!half!"
)

set "maxIdx=25"
if !idx1! GTR !maxIdx! set "maxIdx=!idx1!"
if !idx2! GTR !maxIdx! set "maxIdx=!idx2!"
if !idx3! GTR !maxIdx! set "maxIdx=!idx3!"
if !idx4! GTR !maxIdx! set "maxIdx=!idx4!"

for /L %%i in (1,1,!maxIdx!) do (
    set "c1_raw=!col1[%%i]!"
    set "c2_raw=!col2[%%i]!"
    set "c3_raw=!col3[%%i]!"
    set "c4_raw=!col4[%%i]!"
    set "b4=!col4_block[%%i]!"
    
    set "color4=%G%"
    if "!b4!"=="3" set "color4=%Y%"
    if "!b4!"=="4" set "color4=%CY%"
    if "!b4!"=="5" set "color4=%W%"
    
    set "id_color1=%R%" & set "id_color2=%G%" & set "id_color3=%G%" & set "id_color4=!color4!"

    set "spaces1=                                                  "
    set "c1_final=!c1_raw!!spaces1!"
    set "c1_final=!c1_final:~0,45!"
    if not "!c1_raw!"=="" for /f "tokens=1 delims= " %%A in ("!c1_raw!") do (
        if /i "%%A"=="!lastID!" (
            set "nameWithMarker=!c1_raw! [L]"
            set "c1_pad=!nameWithMarker!!spaces1!"
            set "temp=!c1_pad:~0,45!"
            set "c1_final=!temp:[L]=%ESC%[1;95m[L]%W%!"
        )
    )
    
    REM --- Spalte 2 & 3 (PWADS) ---
    set "spaces2=                                                  "
    set "c2_final=!c2_raw!!spaces2!"
    set "c2_final=!c2_final:~0,45!"
    if not "!c2_raw!"=="" for /f "tokens=1 delims= " %%A in ("!c2_raw!") do (
        if /i "%%A"=="!lastID!" (
            set "nameWithMarker=!c2_raw! [L]"
            set "c2_pad=!nameWithMarker!!spaces2!"
            set "temp=!c2_pad:~0,45!"
            set "c2_final=!temp:[L]=%MAG%[L]%W%!"
        )
    )

    set "c3_final=!c3_raw!!spaces2!"
    set "c3_final=!c3_final:~0,45!"
    if not "!c3_raw!"=="" for /f "tokens=1 delims= " %%A in ("!c3_raw!") do (
        if /i "%%A"=="!lastID!" (
            set "nameWithMarker=!c3_raw! [L]"
            set "c3_pad=!nameWithMarker!!spaces2!"
            set "temp=!c3_pad:~0,45!"
            set "c3_final=!temp:[L]=%MAG%[L]%W%!"
        )
    )
    
    REM --- Spalte 4 (EXTRA) ---
    set "display4="
    if not "!c4_raw!"=="" (
        if "!c4_raw!"=="EMPTY" (
            set "display4="
        ) else (
            set "c4_final=!c4_raw!!spaces2!"
            set "c4_final=!c4_final:~0,45!"
            for /f "tokens=1 delims= " %%A in ("!c4_raw!") do (
                if /i "%%A"=="!lastID!" (
                    set "nameWithMarker=!c4_raw! [L]"
                    set "c4_pad=!nameWithMarker!!spaces2!"
                    set "temp=!c4_pad:~0,45!"
                    set "c4_final=!temp:[L]=%MAG%[L]%W%!"
                )
            )
            set "display4=!id_color4!!c4_final!%W%"
        )
    )
    
    echo    !id_color1!!c1_final!%W% %GRA%^|%W% !id_color2!!c2_final!%W% %GRA%^|%W% !id_color3!!c3_final!%W% %GRA%^| !display4!
)

set "updMarker="
if "!updateAvailable!"=="1" set "updMarker= %R%[U] Update verfügbar%W%"

echo.
echo  %C_Cyan%============================================================================================================================================================================================================%C_Reset%
echo    KARTEN: %G%Gesamt: !totalMaps!%W% ^| %R%IWAD: !countD1!%W% ^| %G%PWAD: !countD2!%W% ^| %CY%Heretic / Hexen: !countExtra!%W%  %GRA%│%W%  %Y%SPIELZEIT: !displayTime!%W%  %GRA%│%W%  MODS: %Y%!modTotalCount!%W%  %GRA%│%W%  %B%UZDoom !CUR_VERSION!!updMarker!%W%
echo  %C_Cyan%============================================================================================================================================================================================================%C_Reset%

set "lineText=   %C_Yellow%[0] Beenden    [R] Reset/Neu laden%C_Reset%"
if not "!lastID!"=="" set "lineText=!lineText!    %Y%Zuletzt gespielt: %CY%!lastID! - !lastName! %Y%[L]%C_Reset%"
echo !lineText!
echo.
if defined currentError (echo    %R%Fehler: ID '%Y%!currentError!%R%' ist ungültig.%C_Reset%) else (echo.)

set "M="
set /p "M=%C_Yellow%    Gib die ID ein ODER ENTER für letzte Karte - %MAG%!lastID!%C_Yellow%): %C_Reset%"

if "!M!"=="" (
    if not "!lastID!"=="" (
        set "M=!lastID!"
        echo %C_Green%    Starte letzte Karte: %MAG%!lastID!%C_Reset%
        timeout /t 1 >nul
    ) else (
        echo %R%    Keine letzte ID gespeichert!%C_Reset%
        pause
        goto :map_selection
    )
)

if "%M%"=="" goto map_selection
if /i "%M%"=="0" exit
if /i "%M%"=="r" (start "" "%~f0" & exit)
if /i "%M%"=="l" (if defined lastID (set "M=!lastID!" & goto start_from_last))

:start_from_last
set "found=0"
for /f "usebackq skip=1 tokens=1,* delims=," %%a in ("%CSV_FILE%") do (
    if /i "%%a"=="!M!" (
        set "mapData=%%b"
        set "found=1"
    )
)
if "!found!"=="0" (set "lastWrongID=!M!" & goto map_selection)

for /f "tokens=1,2,* delims=," %%x in ("!mapData!") do (
    set "core=%%x"
    set "mapname=%%y"
    set "remaining=%%z"
)
set "core=!core: =!"
set "displayCore=!core!"
set "subFolder=doom"
if /i "!core!"=="heretic.wad" set "subFolder=heretic"
if /i "!core!"=="hexen.wad"   set "subFolder=hexen"

set "fileParams=" & set "extraParams=" & set "modFlag=0" & set "nextIsValue=0" & set "autoMod="
for %%p in (!remaining!) do (
    set "item=%%~p"
    if "!nextIsConfig!"=="1" (
        set "extraParams=!extraParams! -config "%~dp0!item!" "
        set "nextIsConfig=0"
    ) else if "!nextIsValue!"=="1" (
        set "extraParams=!extraParams! !item! "
        set "nextIsValue=0"
    ) else if "!item!"=="1" (
        set "modFlag=1"
    ) else if "!item!"=="0" (
        set "modFlag=0"
    ) else if "!item:~0,1!"=="-" (
        set "extraParams=!extraParams! !item! "
        if /i "!item!"=="-config" set "nextIsConfig=1"
        if /i "!item!"=="-warp" set "nextIsValue=1"
        if /i "!item!"=="-skill" set "nextIsValue=1"
    ) else if "!item:~0,1!"=="+" (
        set "extraParams=!extraParams! !item! "
    ) else (
        set "targetPath="
        if exist "%PWAD_DIR%\!item!" (set "targetPath=%PWAD_DIR%\!item!") else if exist "%IWAD_DIR%\!item!" (set "targetPath=%IWAD_DIR%\!item!") else if exist "%PWAD_DIR%\!item!.wad" (set "targetPath=%PWAD_DIR%\!item!.wad")
        if defined targetPath (
            if exist "!targetPath!\" (for %%f in ("!targetPath!\*.wad" "!targetPath!\*.pk3" "!targetPath!\*.zip") do set "fileParams=!fileParams! -file "%%~f"") else (set "fileParams=!fileParams! -file "!targetPath!"")
        ) else (
            set "isSystem=0"
            if /i "!item!"=="doom" set "isSystem=1"
            if /i "!item!"=="heretic" set "isSystem=1"
            if /i "!item!"=="hexen" set "isSystem=1"
            if "!isSystem!"=="0" (if exist "mods\!subFolder!\!item!\" (set "autoMod=!subFolder!\!item!") else if exist "mods\!item!\" (set "autoMod=!item!"))
        )
    )
)

if defined autoMod (
    set "modName=!autoMod! (Auto)" & set "modParam="
    for %%F in ("mods\!autoMod!\*.pk3" "mods\!autoMod!\*.wad" "mods\!autoMod!\*.zip") do set "modParam=!modParam! -file "%%F""
    goto summary_section
)
if "!modFlag!"=="1" (set "modName=Vanilla (Deaktiviert)" & set "modParam=" & goto summary_section)
if "%USE_MODS%"=="0" (set "modName=Vanilla" & set "modParam=" & goto summary_section)

:mod_menu
set "modCount=0"
if exist "mods\!subFolder!\" (
    for /d %%D in ("mods\!subFolder!\*") do (
        set /a modCount+=1
        set "modFolder[!modCount!]=!subFolder!\%%~nxD"
        set "modTitle[!modCount!]=%%~nxD"
    )
)
if %modCount% EQU 0 goto summary_section

:mod_display
CLS
set "indent=          " & set "line=--------------------------------------------------------------------------------"
echo.
echo %indent%%CY%MOD-AUSWAHL: %G%!subFolder!%W%
echo %indent%%line%
echo %indent%  SPIEL : %G%%displayCore%%W%
echo %indent%  KARTE : %G%%mapname%%W%
echo %indent%%line%
echo.
for /L %%i in (1,1,%modCount%) do echo %indent%   %CY%%%i.%W% !modTitle[%%i]!
echo.
echo %indent%   %CY%0.%W% Keine Mod (Vanilla)
echo %indent%%line%
if defined modError (echo. & echo %indent%   %R%Fehler: ID '%Y%!modError!%R%' ungültig.%C_Reset% & set "modError=")
echo.
set "modChoice="
set /P "modChoice=%indent%  %Y%DEINE WAHL: %W%"

if "%modChoice%"=="" (set "modName=Vanilla" & set "modParam=" & goto summary_section)
if "%modChoice%"=="0" (set "modName=Vanilla" & set "modParam=" & goto summary_section)
set "isValidMod=0"
for /L %%i in (1,1,%modCount%) do if "%modChoice%"=="%%i" set "isValidMod=1"
if "!isValidMod!"=="0" (set "modError=!modChoice!" & goto mod_display)

set "selectedPath=!modFolder[%modChoice%]!"
set "modName=!modTitle[%modChoice%]!"
set "modParam="
for %%F in ("mods\!selectedPath!\*.pk3" "mods\!selectedPath!\*.wad" "mods\!selectedPath!\*.zip") do set "modParam=!modParam! -file "%%F""

:summary_section
set "indent=          "
CLS
echo.
echo %indent%%G%S T A R T E   E N G I N E%W%
echo %indent%--------------------------------------------------------------------------------
echo %indent%  KARTE : %CY%%mapname%%W%
echo %indent%  IWAD  : %CY%%displayCore%%W%
echo %indent%  MOD   : %CY%%modName%%W%
echo %indent%--------------------------------------------------------------------------------
echo.
echo %indent%%Y%Spiel läuft... Bitte warten.%W%

echo !M!>"last_played.txt"

REM --- Zeitstempel beim Start ---
set "startTime=%time: =0%"
set "startTime=!startTime:,=.!"

set "lastLine=0"
if exist "logfile.txt" for /f %%A in ('find /c /v "" ^< "logfile.txt"') do set "lastLine=%%A"

REM --- Spielstart ---
start /wait "" "%UZ%" +logfile "logfile.txt" -iwad "%IWAD_DIR%\!core!" !fileParams! !modParam! !extraParams!

REM --- Zeitstempel beim Ende ---
set "endTime=%time: =0%"
set "endTime=!endTime:,=.!"
for /f %%t in ('powershell -command "$s=[datetime]::Parse('!startTime!'); $e=[datetime]::Parse('!endTime!'); if($e -lt $s){$e=$e.AddDays(1)}; [int][math]::Floor(($e-$s).TotalSeconds)"') do set "sessionSeconds=%%t"

if not defined sessionSeconds set "sessionSeconds=0"
set /a totalMinutes=!totalMinutes! + !sessionSeconds!
echo !totalMinutes!>"%TIME_FILE%"

cls

REM --- SESSION STATISTIK ---
if "!show_stats!"=="1" (
    echo %G%    Spiel beendet. Analysiere Sitzung... %W%
    set /a health_count=0, armor_count=0, ammo_count=0, key_count=0, powerup_count=0
    set "weapon_list= "

    if exist "logfile.txt" (
        REM Aktuelle Sitzung isolieren
        more +!lastLine! "logfile.txt" > "session_raw.tmp"
        
        REM Vorfiltern auf Items/Waffen (Sichert Performance und Stabilität)
        findstr /I "genommen erhalten picked got Slot Mega Sphäre Super charge keycard Schlüssel Karte Skull Radiation Visor Suit Shielding Invulnerability Unverwundbarkeit Invisibility Unsichtbarkeit" "session_raw.tmp" > "filtered_log.tmp"
        
        for /f "usebackq delims=" %%L in ("filtered_log.tmp") do (
            set "raw_line=%%L"
            
            if defined raw_line (
                REM Heilung & Rüstung
                echo "!raw_line!" | findstr /I "Heilung Health Bonus Stimpack Medikit Mega Supercharge Berserk" >nul && set /a health_count+=1
                echo "!raw_line!" | findstr /I "Panzer Armor Mega" >nul && set /a armor_count+=1
                
                REM Munition
                echo "!raw_line!" | findstr /I "Patronen Magazin Rakete Zelle Kiste Clip Shell Rocket Cell Ammo Box Rucksack Backpack" >nul && set /a ammo_count+=1
                
                REM Schlüssel
                echo "!raw_line!" | findstr /I "Schlüssel Karte Keycard Key Skull" >nul && set /a key_count+=1
                
                REM Power-Ups
                echo "!raw_line!" | findstr /I "Suit Visor Shielding Invulnerability Unverwundbarkeit Invisibility Unsichtbarkeit Computer Strahlenschutz Infrarot" >nul && set /a powerup_count+=1

                REM Waffen-Check
                for %%W in (Pistole Pistol Schrotflinte Shotgun Gewehr Chaingun Maschinengewehr Kettensäge Saw Raketenwerfer Launcher Plasma BFG MG-42 Railgun) do (
                    echo "!raw_line!" | findstr /I "%%W" >nul && (
                        echo "!weapon_list!" | findstr /I "%%W" >nul || (
                            if "!weapon_list!"==" " (
                                set "weapon_list=%%W"
                            ) else (
                                set "weapon_list=!weapon_list!, %%W"
                            )
                        )
                    )
                )
            )
        )
    )

    cls
    echo %MAG%========================================================%W%
    echo    S E S S I O N   Z U S A M M E N F A S S U N G
    echo %MAG%========================================================%W%
    echo.
    echo    Projekt: !M! - %Y%!mapname!%W%
    
    set /a "sM=sessionSeconds / 60"
    set /a "sS=sessionSeconds %% 60"
    echo    Dauer:   %Y%!sM! Min. !sS! Sek.%W%
    echo.
    echo    Gegenstände:
    echo    - Heilung:  %G%!health_count!%W% ^| Rüstung: %CY%!armor_count!%W%
    echo    - Munition: %Y%!ammo_count!%W% ^| Schlüssel: %B%!key_count!%W%
    echo    - Spezial:  %MAG%!powerup_count!%W%
    
    if not "!weapon_list!"==" " (
        echo.
        echo    Waffen:     %MAG%!weapon_list!%W%
    )
    echo.
    echo %MAG%========================================================%W%
    
    if exist "session_raw.tmp" del "session_raw.tmp"
    if exist "filtered_log.tmp" del "filtered_log.tmp"
    pause
)

REM --- VARIABLEN LEEREN UND ZURÜCK ZUR AUSWAHL ---
for %%v in (mapname core displayCore modName modParam fileParams extraParams mapData remaining found modChoice targetPath item firstChar block line folder nextIsValue autoMod isSystem sessionMinutes startTime endTime displayTime health_count armor_count ammo_count key_count powerup_count weapon_list raw_line lastLine) do set "%%v="
goto map_selection