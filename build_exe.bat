@echo off
chcp 65001 >nul
echo Установка зависимостей...
pip install -r requirements.txt
if errorlevel 1 (
    echo Ошибка установки зависимостей
    pause
    exit /b 1
)

echo.
echo Сборка PhotoInWord.exe...
python -m PyInstaller -F -n PhotoInWord --clean main.py
if errorlevel 1 (
    echo Ошибка сборки
    pause
    exit /b 1
)

echo.
echo Готово! Исполняемый файл: dist\PhotoInWord.exe
pause
