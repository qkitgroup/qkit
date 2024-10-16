@echo off
goto check_Permissions

:check_Permissions

    net session >nul 2>&1
    if %errorLevel% == 0 (
        goto admin
    ) else (
        goto not_admin
    )
	exit


:not_admin
	echo "Currently not an admin... Starting Prompt.."
	@powershell Start-Process %0 -Verb RunAs
	exit


:admin
	cd %~dp0
	cd ..
	FTYPE h5_file=
	ASSOC .h5=
	FTYPE h5_file="%cd%\launch_qviewkit.bat" "%%1"
	ASSOC .h5=h5_file
	pause