@echo off
REM Script pour lancer Etoile D'ébène

REM Chemin vers l'environnement virtuel 
set VENV_PATH=C:\Users\Admin\Documents\GitHub\Simple-Bot-Discord\.venv\Scripts

REM Chemin vers le fichier Python à exécuter
set PYTHON_FILE=bot.py

REM Vérifie si l'environnement virtuel existe
if not exist "%VENV_PATH%\python.exe" (
    echo L'environnement virtuel spécifié n'existe pas ou le chemin est incorrect.
    pause
    exit /b
)

REM Active l'environnement virtuel et lance le script
echo Activation de l'environnement virtuel...
call "%VENV_PATH%\activate.bat"

REM Exécute le fichier Python
echo Lancement de %PYTHON_FILE%...
python %PYTHON_FILE%

REM Désactivation de l'environnement virtuel
deactivate

REM Pause pour garder la fenêtre ouverte
pause
