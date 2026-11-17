@echo off
cd /d "%~dp0"
where py >nul 2>nul && (py -3 mediadownloadtool.py) || (python mediadownloadtool.py)
if errorlevel 1 pause
