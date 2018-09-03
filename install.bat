@echo Addig the QKIT folder to your PYTHONPATH variable (for the local user)
@echo.

@set dir=%~dp0
@if %dir:~-1%==\ set dir=%dir:~0,-1%


@echo off
@echo %PYTHONPATH%|findstr %dir% >nul 2>&1
if not errorlevel 1 (
	@echo on
	@echo.qkit already installed
) else (
	@echo on
    if defined PYTHONPATH (
		if "%PYTHONPATH:~-1%"==";" (
			setx PYTHONPATH %PYTHONPATH%%dir%;
		) else (
			setx PYTHONPATH %PYTHONPATH%;%dir%;
		)
	) else (
		setx PYTHONPATH %PYTHONPATH%%dir%;
	)
)
@pause

@echo.
@echo.
@echo.
@echo The next thing is to install pyqtgraph module if not already installed.
@echo.
@pause
pip install pyqtgraph

@pause