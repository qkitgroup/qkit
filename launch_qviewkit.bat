@echo on
Pushd "%~dp0"
CALL .venv/Scripts/activate.bat
qviewkit -f  %1

@echo off
if errorlevel 1 (
   echo.
   echo Qviewkit exited with an error. Please find a traceback above.
   echo Windows ErrorLevel: %errorlevel%
   pause

)

