CALL .\.venv\Scripts\activate
SET PYTHONPATH=%cd%
jupyter lab --config=./jupyter_lab_config.py
