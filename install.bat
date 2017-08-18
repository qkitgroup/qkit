@echo Addig the QKIT folder to your PYTHONPATH variable (for the local user)
@echo.

setx PYTHONPATH %PYTHONPATH%%~dp0;

@echo.
@echo.
@echo.
@echo The next thing is to install pyqtgraph module if not already installed.
@echo.
@pause
pip install pyqtgraph

@pause