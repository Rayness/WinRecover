@echo off
chcp 65001 >nul
echo ===================================================
echo  WinRecover — сборка через PyInstaller
echo ===================================================

:: Проверяем наличие PyInstaller
python -m pyinstaller --version >nul 2>&1
if errorlevel 1 (
    echo [!] PyInstaller не найден. Устанавливаю...
    pip install pyinstaller
)

:: Чистим предыдущую сборку
if exist dist\WinRecover rmdir /s /q dist\WinRecover
if exist build\WinRecover rmdir /s /q build\WinRecover

:: Сборка
echo.
echo [*] Запускаю сборку...
python -m pyinstaller winrecover.spec --noconfirm

if errorlevel 1 (
    echo.
    echo [!] Сборка завершилась с ошибкой.
    pause
    exit /b 1
)

echo.
echo [OK] Сборка успешна!
echo      Папка: dist\WinRecover\
echo      Запуск: dist\WinRecover\WinRecover.exe
echo.
pause
