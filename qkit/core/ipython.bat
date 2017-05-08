:: ipython.bat
:: Runs IPython like in qtlab.bat, without actually starting QTLab.
::
:: Useful for testing and debugging.

:: Add Console2 to PATH
SET PATH=%CD%\3rd_party\Console2\;%PATH%

:: Check for version of python
IF EXIST c:\python27\python.exe (
    SET PYTHON_PATH=c:\python27
    GOTO mark1
)
IF EXIST c:\python26\python.exe (
    SET PYTHON_PATH=c:\python26
    GOTO mark1
)
:mark1

:: Run Ipython
:: check if version < 0.11
IF EXIST "%PYTHON_PATH%\scripts\ipython.py" (
    start Console -w "IPython" -r "/k %PYTHON_PATH%\python.exe %PYTHON_PATH%\scripts\ipython.py -p sh"
    GOTO EOF
)
:: check if version >= 0.11
IF EXIST "%PYTHON_PATH%\scripts\ipython-script.py" (
    start Console -w "Ipython" -r "/k %PYTHON_PATH%\python.exe %PYTHON_PATH%\scripts\ipython-script.py"
    GOTO EOF
)

echo Failed to run ipython.bat
pause
:EOF
