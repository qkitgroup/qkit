.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH += ";$(Get-Location)"
jupyter lab --config=./jupyter_lab_config.py
