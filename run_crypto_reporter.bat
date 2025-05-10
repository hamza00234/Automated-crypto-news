@echo off
setlocal enabledelayedexpansion

:: Set the full path to Python (adjust this path to match your Python installation)
set PYTHON_PATH=C:\Users\User\AppData\Local\Programs\Python\Python313\python.exe

:: Create a log file with timestamp
set LOGFILE=task_run_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%.log
set LOGFILE=%LOGFILE: =0%

:: Log the start of execution
echo ========================================== >> %LOGFILE%
echo Starting Crypto Reporter at %date% %time% >> %LOGFILE%
echo Current Directory: %CD% >> %LOGFILE%
echo Python Path: %PYTHON_PATH% >> %LOGFILE%

:: Check if Python executable exists
if not exist "%PYTHON_PATH%" (
    echo ERROR: Python not found at %PYTHON_PATH% >> %LOGFILE%
    echo Please update PYTHON_PATH in the batch file >> %LOGFILE%
    exit /b 1
)

:: Check if .env file exists
if not exist .env (
    echo ERROR: .env file not found in %CD% >> %LOGFILE%
    exit /b 1
)

:: Display environment variables (without sensitive data)
echo Environment Variables: >> %LOGFILE%
echo PATH: %PATH% >> %LOGFILE%
echo PYTHONPATH: %PYTHONPATH% >> %LOGFILE%

:: List directory contents
echo Directory Contents: >> %LOGFILE%
dir /b >> %LOGFILE%

:: Run the Python script and capture output
echo Running Python script... >> %LOGFILE%
"%PYTHON_PATH%" main.py >> %LOGFILE% 2>&1

:: Check if the script ran successfully
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Script failed with error code %ERRORLEVEL% >> %LOGFILE%
    exit /b 1
)

echo Script completed successfully at %date% %time% >> %LOGFILE%
echo ========================================== >> %LOGFILE%

endlocal 