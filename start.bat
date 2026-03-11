@echo off
cd /d %~dp0

for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8876" ^| findstr "LISTENING"') do (
  taskkill /F /PID %%p >nul 2>nul
)
timeout /t 1 >nul

set "PY310=C:\Users\86178\AppData\Local\Programs\Python\Python310\python.exe"
set "CONDA_PY=C:\Users\86178\miniconda3\python.exe"

if exist "%PY310%" (
  start "Paper Hub Server" "%PY310%" server.py
) else if exist "%CONDA_PY%" (
  start "Paper Hub Server" "%CONDA_PY%" server.py
) else (
  start "Paper Hub Server" python server.py
)

timeout /t 2 >nul
start "" http://127.0.0.1:8876/?v=20260311-8
