@ECHO OFF

REM Build skript pro Sphinx dokumentaci na Windows

ECHO ========================================
ECHO TalosForge - Build dokumentace
ECHO ========================================

REM Instalace závislostí (pokud ještě nejsou nainstalované)
IF NOT EXIST "venv\Lib\site-packages\sphinx" (
    ECHO Instaluji závislosti pro dokumentaci...
    pip install -r requirements.txt
)

REM Vytvoření _build adresáře pokud neexistuje
IF NOT EXIST "_build" (
    mkdir _build
)

REM Spuštění sphinx build
ECHO Builduji HTML dokumentaci...
sphinx-build -M -b html . _build/html

IF ERRORLEVEL 1 (
    ECHO CHYBA PŘI BUILDU!
    EXIT /B 1
)

REM Otevření dokumentace v browseru
start _build\html\index.html

ECHO.
ECHO Dokumentace byla vygenerována do _build\html/
ECHO Dokumentace je otevřena ve vašem výchozím browseru.
ECHO.
PAUSE
