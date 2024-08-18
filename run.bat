@echo off
setlocal enableDelayedExpansion
title Start Marketplace GUI

:: Activate the virtual environment
call venv\Scripts\activate

:loop
echo.
set /p input="Type 'start' to run the app & gui or 'exit' to quit: "
set "input=%input:"=%"
if /i "%input%" == "exit" exit /b
if /i "%input%" == "start" goto run
goto loop

:run
echo Starting app.py in another window
start "Marketplace Scraper App" cmd /k "python app.py"
echo
echo Starting Streamlit GUI in a new window
start "Marketplace GUI" cmd /k "streamlit run gui.py"
