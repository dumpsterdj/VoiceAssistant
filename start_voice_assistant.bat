@echo off
REM === Activate conda/venv and run assistant ===

REM Path to your conda environment Python
set PYTHON_EXE=C:\Users\dhruv\.conda\envs\VoiceAssistant\python.exe

REM Path to your project main module
set PROJECT_MAIN=C:\Users\dhruv\PycharmProjects\VoiceAssistant\main.py

REM Run the assistant with options
start "" "%PYTHON_EXE%" "%PROJECT_MAIN%" --allow-download --allow-arbitrary

exit
