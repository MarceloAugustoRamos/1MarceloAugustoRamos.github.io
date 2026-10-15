@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 goto fallback
py -3 launcher.py install
goto finished

:fallback
where python >nul 2>nul
if errorlevel 1 goto no_python
python launcher.py install
goto finished

:no_python
echo Python nao foi encontrado. Instale Python e marque Add Python to PATH.
pause
exit /b 1

:finished
if errorlevel 1 goto failure
pause
exit /b 0

:failure
echo.
echo A instalacao falhou. Leia a mensagem acima.
pause
exit /b 1
