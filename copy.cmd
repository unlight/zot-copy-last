@echo off
rem zot spawns extensions via CreateProcess, which cannot run a .py shebang.
rem Pick whichever Python launcher exists and hand over to copy.py.
where python >nul 2>nul
if errorlevel 1 goto trypy
python "%~dp0copy.py" %*
exit /b %errorlevel%
:trypy
where py >nul 2>nul
if errorlevel 1 goto nopython
py -3 "%~dp0copy.py" %*
exit /b %errorlevel%
:nopython
echo [copy] no Python launcher found on PATH (python, py) 1>&2
exit /b 127
