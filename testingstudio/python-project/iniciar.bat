@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 goto fallback
py -3 launcher.py start
goto finished

:fallback
where python >nul 2>nul
if errorlevel 1 goto no_python
python launcher.py start
goto finished

:no_python
echo Python nao foi encontrado. Instale Python e marque Add Python to PATH.
pause
exit /b 1

:finished
if errorlevel 1 goto failure
exit /b 0

:failure
echo.
echo Nao foi possivel abrir o app. Leia a mensagem acima.
pause
exit /b 1
