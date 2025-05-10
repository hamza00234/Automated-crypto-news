@echo off
cd /d "%~dp0"
py "%~dp0main.py" > "%~dp0output.log" 2>&1
echo Script execution completed. Check output.log for details.
pause 