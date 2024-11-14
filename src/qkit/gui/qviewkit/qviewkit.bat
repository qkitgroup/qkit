@echo on
Pushd "%~dp0"
python main.py -f %1

@echo off
if errorlevel 1 (
   echo.
   echo Qviewkit exited with an error. Please find a traceback above.
   echo Windows ErrorLevel: %errorlevel%
   pause

)
