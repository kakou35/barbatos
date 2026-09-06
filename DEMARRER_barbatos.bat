@echo off
chcp 65001 >nul 2>&1
setlocal

TITLE BARBATOS - Local Autonomous AI Operating System
COLOR 0B

cd /d "%~dp0"

echo.
echo ======================================================
echo              BARBATOS - DEMARRAGE
echo       Local Autonomous AI Operating System
echo ======================================================
echo.
echo [INFO] Dossier : %CD%
echo.

REM ======================================================
REM VERIFICATION DE PYTHON
REM ======================================================

echo [1/4] Verification de Python...

where python >nul 2>&1

if errorlevel 1 goto error_no_python

for /f "tokens=*" %%A in ('python --version 2^>^&1') do set PYTHON_VERSION=%%A

echo       %PYTHON_VERSION%
echo.


REM ======================================================
REM VERIFICATION DE BARBATOS
REM ======================================================

echo [2/4] Verification de BARBATOS...

if not exist "barbatos_cli.py" goto error_no_barbatos

echo       barbatos_cli.py OK
echo.


REM ======================================================
REM VERIFICATION D'OLLAMA
REM ======================================================

echo [3/4] Verification d'Ollama...

where ollama >nul 2>&1

if errorlevel 1 goto error_no_ollama

echo       Ollama OK
echo.


REM ======================================================
REM VERIFICATION DU MODELE
REM ======================================================

echo [4/4] Verification du modele LLM...

ollama list | findstr /i "llama3.1:latest" >nul 2>&1

if errorlevel 1 goto error_no_model

echo       llama3.1:latest OK
echo.


REM ======================================================
REM LANCEMENT
REM ======================================================

echo ======================================================
echo              BARBATOS EST PRET
echo ======================================================
echo.
echo [INFO] Lancement de BARBATOS...
echo.

python barbatos_cli.py

if errorlevel 1 goto error_runtime

echo.
echo ======================================================
echo              BARBATOS ARRETE
echo ======================================================
echo.

exit /b 0


REM ======================================================
REM ERREURS
REM ======================================================

:error_no_python

echo.
echo ======================================================
echo [ERREUR] PYTHON INTROUVABLE
echo ======================================================
echo.
echo Python n'est pas accessible depuis le PATH Windows.
echo.
echo Verifiez que Python 3.11 est installe.
echo.
pause
exit /b 1


:error_no_barbatos

echo.
echo ======================================================
echo [ERREUR] BARBATOS INTROUVABLE
echo ======================================================
echo.
echo Le fichier barbatos_cli.py est absent.
echo.
echo Dossier actuel :
echo %CD%
echo.
echo Verifiez que le lanceur se trouve bien
echo a la racine du dossier BARBATOS.
echo.
pause
exit /b 1


:error_no_ollama

echo.
echo ======================================================
echo [ERREUR] OLLAMA INTROUVABLE
echo ======================================================
echo.
echo Ollama n'est pas installe ou n'est pas accessible
echo depuis le PATH Windows.
echo.
echo Installez Ollama puis relancez BARBATOS.
echo.
pause
exit /b 1


:error_no_model

echo.
echo ======================================================
echo [ERREUR] MODELE LLM INTROUVABLE
echo ======================================================
echo.
echo Le modele llama3.1:latest n'est pas disponible.
echo.
echo Modeles Ollama disponibles :
echo.
ollama list
echo.
echo Pour installer le modele :
echo.
echo     ollama pull llama3.1:latest
echo.
pause
exit /b 1


:error_runtime

echo.
echo ======================================================
echo [ERREUR] BARBATOS S'EST ARRETE
echo ======================================================
echo.
echo BARBATOS a retourne une erreur pendant son execution.
echo.
echo Consultez les messages affiches ci-dessus.
echo.
pause
exit /b 1
```
