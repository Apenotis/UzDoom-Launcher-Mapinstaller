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
set "W=%ESC%[0m"
set "GRA=%ESC%[90m"

REM --- Modabfrage an/aus 0/1 ---
set "USE_MODS=1"

REM --- PFADE ---
set "CSV_FILE=maps.csv"
set "IWAD_DIR=%~dp0iwad"
set "PWAD_DIR=%~dp0pwad"
set "UZ=UzDoom\uzdoom.exe"

set "lastCheckFile=last_update.txt"
set "doCheck=0"

for /f "tokens=1-3 delims=. " %%a in ('echo %DATE%') do set "today=%%c%%b%%a"

if not exist "%lastCheckFile%" (
    set "doCheck=1"
) else (
    set /p lastDate=<"%lastCheckFile%"

    for /f %%d in ('powershell -command "((Get-Date) - (Get-Date -Date ([datetime]::ParseExact('!lastDate!', 'yyyyMMdd', $null)))).Days"') do set "daysPassed=%%d"
    
    if !daysPassed! GEQ 7 set "doCheck=1"
)

if "!doCheck!"=="1" (
    echo %Y%   Prüfe auf UZDoom Updates Wöchentlicher Check...%W%
    for /f "delims=" %%v in ('powershell -command "$v = (Invoke-RestMethod -Uri 'https://api.github.com/repos/UZDoom/UZDoom/releases/latest').tag_name; echo $v" 2^>nul') do set "latest_version=%%v"
    
    if defined latest_version (
        echo !today!>"%lastCheckFile%"
        
        set "current_version=4.14.3"
        if not "!latest_version!"=="!current_version!" (
            echo.
            echo %R%   UPDATE VERFÜGBAR: %G%!latest_version!%W%
            echo    Download: https://github.com/UZDoom/UZDoom/releases/latest
            echo.
            pause
        )
    )
)

:map_selection
powershell -command "&{$W=(get-host).ui.rawui;$B=$W.buffersize;$B.width=205;$B.height=100;$W.buffersize=$B;$W.windowsize=@{width=205;height=66}}" 2>nul
cls
set "C_Cyan=%ESC%[36m"
set "C_Green=%ESC%[32m"
set "C_Yellow=%ESC%[33m"
set "C_Gray=%ESC%[90m"
set "C_Red=%ESC%[31m"
set "C_Reset=%ESC%[0m"

CLS
echo.
echo  %C_Cyan%===========================================================================================================================================================================================================
echo      I W A D S                                 ^| P W A D S                                           ^| P W A D S                                           ^| H E R E T I C / H E X E N / W O L F
echo  ===========================================================================================================================================================================================================%C_Reset%

REM Arrays und Zähler leeren
for /L %%i in (1,1,300) do (
    set "col1[%%i]="
    set "col2[%%i]="
    set "col3[%%i]="
    set "col4[%%i]="
    set "tempPWAD[%%i]="
)
set "idx1=0" & set "idx2=0" & set "idx3=0" & set "idx4=0" & set "tempPWAD_idx=0"
set "block=1"

REM CSV zeilenweise lesen
if not exist "%CSV_FILE%" (
    echo %R%FEHLER: %CSV_FILE% nicht gefunden!%W%
    pause
    exit
)

set "block=1"
set "pCount=0"
set "idx1=0" & set "idx4=0"

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
                    set /a idx1+=1
                    set "col1[!idx1!]=!entry!"
                ) else if !block! EQU 2 (
                    set /a pCount+=1
                    set "tempPWAD[!pCount!]=!entry!"
                ) else (
                    set /a idx4+=1
                    set "col4[!idx4!]=!entry!"
                    set "col4_block[!idx4!]=!block!"
                )
            )
        )
    )
)

if !pCount! GTR 0 (
    set /a "half=(pCount + 1) / 2"
    for /L %%i in (1,1,!half!) do (
        set "col2[%%i]=!tempPWAD[%%i]!"

        set /a "rIdx=%%i + half"
        if !rIdx! LEQ !pCount! (
            for %%v in (!rIdx!) do set "col3[%%i]=!tempPWAD[%%v]!"
        )
    )
    set "idx2=!half!"
    set "idx3=!half!"
)

set "maxIdx=25"
if !idx1! GTR !maxIdx! set "maxIdx=!idx1!"
if !idx2! GTR !maxIdx! set "maxIdx=!idx2!"
if !idx3! GTR !maxIdx! set "maxIdx=!idx3!"
if !idx4! GTR !maxIdx! set "maxIdx=!idx4!"

for /L %%i in (1,1,!maxIdx!) do (
    set "c1=!col1[%%i]!                                          "
    set "c2=!col2[%%i]!                                                    "
    set "c3=!col3[%%i]!                                                    "
    set "c4_raw=!col4[%%i]!"
    set "b4=!col4_block[%%i]!"

    set "color4=%G%"
    if "!b4!"=="3" set "color4=%Y%"
    if "!b4!"=="4" set "color4=%CY%"
    if "!b4!"=="5" set "color4=%W%"

    set "display4="
    if not "!c4_raw!"=="" (
        if "!c4_raw!"=="EMPTY" (
            set "display4="
        ) else (
            set "display4=!color4!!c4_raw!%W%"
        )
    )

    echo    %R%!c1:~0,42! %GRA%^|%G% !c2:~0,50! %GRA%^|%G% !c3:~0,50! %GRA%^| !display4!
)

echo.
echo  %C_Cyan%===========================================================================================================================================================================================================%C_Reset%
echo    %C_Yellow%[0] Beenden    [R] Reset/Neu laden%C_Reset%
echo.
set "M="
set /p "M=%C_Yellow%    Gib die ID ein: %C_Reset%"

if "%M%"=="" goto map_selection
if /i "%M%"=="0" exit
if /i "%M%"=="r" goto map_selection

set "found=0"
for /f "usebackq skip=1 tokens=1,* delims=," %%a in ("%CSV_FILE%") do (
    if /i "%%a"=="%M%" (
        set "mapData=%%b"
        set "found=1"
    )
)

if "!found!"=="0" (
    echo %C_Red%Ungültige ID!%C_Reset%
    timeout /t 2 >nul
    goto map_selection
)

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

if /i "!core!"=="doom.wad"    set "displayCore=Doom I"
if /i "!core!"=="doom2.wad"   set "displayCore=Doom II"
if /i "!core!"=="heretic.wad" set "displayCore=Heretic"
if /i "!core!"=="hexen.wad"   set "displayCore=Hexen"

set "fileParams=" & set "extraParams=" & set "modFlag=0" & set "nextIsValue=0" & set "autoMod="

for %%p in (!remaining!) do (
    set "item=%%~p"
    set "firstChar=!item:~0,1!"
    
    if "!nextIsConfig!"=="1" (
        set "extraParams=!extraParams! "%~dp0!item!""
        set "nextIsConfig=0"
    ) else if "!nextIsValue!"=="1" (
        set "extraParams=!extraParams! !item!"
        set "nextIsValue=0"
    ) else if "!item!"=="1" (
        set "modFlag=1"
    ) else if "!item!"=="0" (
        set "modFlag=0"
    ) else if "!firstChar!"=="-" (
        if /i "!item!"=="-config" (
            set "extraParams=!extraParams! -config"
            set "nextIsConfig=1"
        ) else (
            set "extraParams=!extraParams! !item!"
            if /i "!item!"=="-warp" set "nextIsValue=1"
            if /i "!item!"=="-skill" set "nextIsValue=1"
        )
    ) else if "!firstChar!"=="+" (
        set "extraParams=!extraParams! !item!"
    ) else (
        set "targetPath="
        if exist "%PWAD_DIR%\!item!" (
            set "targetPath=%PWAD_DIR%\!item!"
        ) else if exist "%IWAD_DIR%\!item!" (
            set "targetPath=%IWAD_DIR%\!item!"
        ) else if exist "%PWAD_DIR%\!item!.wad" (
            set "targetPath=%PWAD_DIR%\!item!.wad"
        )
        
        if defined targetPath (
            if exist "!targetPath!\" (
                for %%f in ("!targetPath!\*.wad" "!targetPath!\*.pk3" "!targetPath!\*.pk7" "!targetPath!\*.zip" "!targetPath!\*.deh" "!targetPath!\*.bex" "!targetPath!\*.hhe" "!targetPath!\*.res" "!targetPath!\*.def" "!targetPath!\*.acs") do (
                    set "fileParams=!fileParams! -file "%%~f""
                )
            ) else (
                set "fileParams=!fileParams! -file "!targetPath!""
            )
        ) else (
            set "isSystem=0"
            if /i "!item!"=="doom" set "isSystem=1"
            if /i "!item!"=="heretic" set "isSystem=1"
            if /i "!item!"=="hexen" set "isSystem=1"
            
            if "!isSystem!"=="0" ( 
                if exist "mods\!subFolder!\!item!\" (
                    set "autoMod=!subFolder!\!item!"
                ) else if exist "mods\!item!\" (
                    set "autoMod=!item!"
                )
            )
        )
    )
)

if defined autoMod (
    set "modName=!autoMod! (Auto)"
    set "modParam="
    for %%F in ("mods\!autoMod!\*.pk3" "mods\!autoMod!\*.wad" "mods\!autoMod!\*.zip") do set "modParam=!modParam! -file "%%F""
    goto summary_section
)

if "!modFlag!"=="1" (
    set "modName=Vanilla (Deaktiviert per CSV)"
    set "modParam="
    goto summary_section
)

if "%USE_MODS%"=="0" (
    set "modName=Vanilla"
    set "modParam="
    goto summary_section
)

:mod_menu
CLS
powershell -command "&{$W=(get-host).ui.rawui;$B=$W.buffersize;$B.width=100;$B.height=25;$W.buffersize=$B;$W.windowsize=@{width=100;height=25}}" 2>nul
set "indent=          "
set "line=--------------------------------------------------------------------------------"
set "modCount=0"

set "subFolder=doom"
if /i "!core!"=="heretic.wad" set "subFolder=heretic"
if /i "!core!"=="hexen.wad"   set "subFolder=hexen"

if exist "mods\!subFolder!\" (
    for /d %%D in ("mods\!subFolder!\*") do (
        set "folder=%%~nxD"
        set /a modCount+=1
        set "modFolder[!modCount!]=!subFolder!\!folder!"
        set "modTitle[!modCount!]=!folder!"
    )
)

CLS
echo.
echo %indent%%CY%MOD-AUSWAHL: %G%!subFolder!%W%
echo %indent%%line%
echo %indent%  SPIEL : %G%%displayCore%%W%
echo %indent%  KARTE : %G%%mapname%%W%
echo %indent%%line%
echo.
if %modCount% EQU 0 (
    echo %indent%  %Y%Keine Mods in "mods\!subFolder!\" gefunden.%W%
    timeout /t 2 >nul
    goto summary_section
)

for /L %%i in (1,1,%modCount%) do echo %indent%   %CY%%%i.%W% !modTitle[%%i]!
echo.
echo %indent%   %CY%0.%W% Keine Mod (Vanilla)
echo %indent%%line%
set "modChoice="
set /P "modChoice=%indent%  %Y%DEINE WAHL: %W%"

if "%modChoice%"=="0" (set "modName=Vanilla" & set "modParam=" & goto summary_section)
if "%modChoice%"=="" (set "modName=Vanilla" & set "modParam=" & goto summary_section)

set "selectedPath=!modFolder[%modChoice%]!"
set "modName=!modTitle[%modChoice%]!"
set "modParam="
for %%F in ("mods\!selectedPath!\*.pk3" "mods\!selectedPath!\*.wad" "mods\!selectedPath!\*.zip") do (
    set "modParam=!modParam! -file "%%F""
)

:summary_section
set "indent=          "
set "line=--------------------------------------------------------------------------------"
CLS
echo.
echo %indent%%G%S T A R T E   E N G I N E%W%
echo %indent%%line%
echo %indent%  KARTE : %CY%%mapname%%W%
echo %indent%  IWAD  : %CY%%displayCore%%W%
echo %indent%  MOD   : %CY%%modName%%W%
echo %indent%%line%
echo.
echo %indent%%Y%Spiel wird geladen...%W%



REM --- DEBUGGER START ---
rem CLS
rem echo %Y%================================================================================%W%
rem echo %G%                  D E B U G G E R   /   L A D E - K O N T R O L L E%W%
rem echo %Y%================================================================================%W%
rem echo.
rem echo  %CY%IWAD / CORE:%W%      %IWAD_DIR%\%core%
rem echo  %CY%KARTEN-PFAD:%W%      !targetPath!
rem echo.
rem echo  %CY%GELADENE DATEIEN (-file):%W%
rem if "!fileParams!"=="" (echo     keine) else (echo   !fileParams!)
rem echo.
rem echo  %CY%MOD-PARAMETER:%W%
rem if "!modParam!"=="" (echo     keine) else (echo   !modParam!)
rem echo.
rem echo  %CY%ZUSATZ-PARAMETER (-config / -warp / etc):%W%
rem if "!extraParams!"=="" (echo     keine) else (echo   !extraParams!)
rem echo.
rem echo %Y%--------------------------------------------------------------------------------%W%
rem echo %R%   PRÜFEN:%W% Steht oben hinter "-config" der richtige Pfad zur .cfg?
rem echo %Y%--------------------------------------------------------------------------------%W%
rem echo.
rem pause
REM --- DEBUGGER ENDE ---



start "" "%UZ%" +logfile "logfile.txt" -iwad "%IWAD_DIR%\%core%" !extraParams! !fileParams! !modParam!

echo %indent%%G%Spiel gestartet!%W%
echo.
echo %indent%%line%
echo %indent%%Y%Drücke eine Taste für das Hauptmenü...%W%
pause >nul

for %%v in (mapname core displayCore modName modParam fileParams extraParams mapData remaining found modChoice targetPath item firstChar block line M folder skip isSpecial) do set "%%v="
goto map_selection