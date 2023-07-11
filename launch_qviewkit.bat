@echo on
Pushd "%~dp0"
SET HDF5_USE_FILE_LOCKING=FALSE
CALL .venv/Scripts/activate.bat
qviewkit -f  %1

@echo off
if errorlevel 1 (
   echo.
   echo Qviewkit exited with an error. Please find a traceback above.
   echo Windows ErrorLevel: %errorlevel%
   pause

)

