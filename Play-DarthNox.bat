@echo off
REM ============================================================
REM  Play DarthNox  -  launcher for OpenLF2 + the DarthNox mod
REM
REM  Put this file in the SAME FOLDER as OpenLF2.exe, with the
REM  mod at:  mods\darthnox\
REM  Then just double-click it.
REM ============================================================
setlocal enabledelayedexpansion
cd /d "%~dp0"

REM --- find the OpenLF2 executable -----------------------------
set "EXE="
for %%F in (OpenLF2.exe openlf2.exe) do if exist "%%F" set "EXE=%%F"
if not defined EXE (
    echo [X] OpenLF2.exe was not found in this folder.
    echo     Put Play-DarthNox.bat next to OpenLF2.exe and run it again.
    echo.
    pause
    exit /b 1
)

REM --- check the mod is in place -------------------------------
if not exist "mods\darthnox\package.manifest" (
    echo [X] The mod was not found at  mods\darthnox\
    echo.
    echo     You should have:
    echo       %CD%\mods\darthnox\package.manifest
    echo       %CD%\mods\darthnox\catalog.lua
    echo       %CD%\mods\darthnox\assets\
    echo.
    pause
    exit /b 1
)

REM --- first run needs the original LF2 installer --------------
REM OpenLF2 remembers it, so this only happens once.
if exist ".darthnox-installed" goto :launch

set "LF2="
for %%N in (LF2_v2.0a.exe lf2_v20a_Setup.exe) do (
    for %%D in ("%CD%" "%USERPROFILE%\Downloads" "%USERPROFILE%\Desktop" "%USERPROFILE%\Documents") do (
        if not defined LF2 if exist "%%~D\%%N" set "LF2=%%~D\%%N"
    )
)

if not defined LF2 (
    echo The original Little Fighter 2 installer is needed once, to load
    echo the base game data. I looked in this folder, Downloads, Desktop
    echo and Documents but did not find it.
    echo.
    echo Drag LF2_v2.0a.exe onto this window and press Enter,
    echo or paste its full path:
    set /p "LF2=> "
    set "LF2=!LF2:"=!"
)

if not exist "!LF2!" (
    echo.
    echo [X] Not found: !LF2!
    echo.
    pause
    exit /b 1
)

echo Using installer: !LF2!
echo.
"%EXE%" --installer "!LF2!" --mod "mods\darthnox"
if errorlevel 1 goto :failed
echo done> ".darthnox-installed"
goto :done

:launch
echo Launching OpenLF2 with the DarthNox mod...
echo.
"%EXE%" --mod "mods\darthnox"
if errorlevel 1 goto :failed

:done
echo.
echo DarthNox is record ID 61 in the Versus character picker.
echo Press "Previous" from Random to jump straight to the high IDs.
echo.
pause
exit /b 0

:failed
echo.
echo ============================================================
echo  OpenLF2 exited with an error. Copy everything above this
echo  line and send it over - that output says what went wrong.
echo ============================================================
echo.
pause
exit /b 1
