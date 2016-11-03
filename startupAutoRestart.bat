@echo off
chcp 65001
echo.
pushd %~dp0

:loopstart

::Attempts to start py launcher without relying on PATH
%SYSTEMROOT%\py.exe --version > NUL 2>&1
IF %ERRORLEVEL% NEQ 0 GOTO attempt
%SYSTEMROOT%\py.exe -3.5 chronoxia.py
timeout 3
GOTO loopstart

::Attempts to start py launcher by relying on PATH
:attempt
python.exe --version > NUL 2>&1
IF %ERRORLEVEL% NEQ 0 GOTO lastattempt
py.exe -3.5 chronoxia.py
timeout 3
GOTO loopstart

::As a last resort, attempts to start whatever Python there is
:lastattempt
python.exe --version > NUL 2>&1
IF %ERRORLEVEL% NEQ 0 GOTO message
py.exe -3.5 chronoxia.py
timeout 3
GOTO loopstart

:message
echo Couldn't find a valid Python 3.5 installation. Python needs to be installed and available in the PATH environment
echo variable.
PAUSE

:end