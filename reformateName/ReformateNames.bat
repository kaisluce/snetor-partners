@echo off
setlocal

set "BASE=\\snetor-docs\Users\MDM\006_PROJECT\003_ALL\Automation\code\partners\reformateName"
set "PYTHON_EXE=%BASE%\venv\Scripts\python.exe"
set "MAIN_PY=%BASE%\main.py"

"%PYTHON_EXE%" "%MAIN_PY%"
pause
