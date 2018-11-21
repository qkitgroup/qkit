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
@echo off
Setlocal EnableDelayedExpansion

@echo Do you want to install pyqtgraph, absolutely necessary for plots (y/n)?
SET /P install=
if !install!==y (
    pip install pyqtgraph
    )

@echo.
@echo.
@echo Do you want to install zerorpc, used for device communication (y/n)?
SET /P install=
if !install!==y (
    pip install zerorpc
    )
@echo.
@echo.
@echo Do you want to install jupyter lab (y/n)?
SET /P install=
if !install!==y (
    pip install jupyterlab==0.33.12
    )
@echo.
@echo.
@echo Do you want to install ipywidgets, used for nice feature in the notebooks (y/n)?
SET /P install=
if !install!==y (
    echo we need nodejs. If conda is not installed you must install it manually before you continue.
    echo Continue using conda [y/n]?
    SET /P conda=
    if !conda!==y (
        conda install -c conda-forge nodejs=8.9.3
    ) else (
        echo Please install it manually before continuing.
        pause
        )
    pip install ipywidgets
    jupyter nbextension enable --py widgetsnbextension
    jupyter labextension install @jupyter-widgets/jupyterlab-manager@0.36
    )
@echo.
@echo.
@echo Do you want to install qgrid, used for a nice overview of your measurement database (y/n)?
SET /P install=
if !install!==y (
    pip install qgrid
    jupyter nbextension enable --py --sys-prefix qgrid
    jupyter labextension install qgrid
    )
@echo.
@echo.
@echo Do you want to install dill, a pickle extension, that lets you save and load your virtual awg channels (y/n)?
SET /P install=
if !install!==y (
    pip install dill
    )
@echo.
@echo.
@echo Do you want to enable classic sorting in Windows Explorer to correctly sort measurements after UIDs (y/n)?
SET /P install=
if !install!==y (
	@powershell Start-Process -FilePath "reg" -ArgumentList "import","%~dp0Windows_UID_sorting.reg" -Verb RunAs 
    )
@echo.
@echo.
@echo That was it. Happy measuring! 
@echo.
@echo.
@pause
