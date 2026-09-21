@echo off
echo ======================================
echo  Building AutoClicker Pro with Nuitka
echo ======================================
echo.

REM Check if Nuitka is installed
python -m nuitka --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Nuitka not found. Installing...
    pip install nuitka
)

echo Building standalone executable...
echo.

python -m nuitka ^
    --standalone ^
    --onefile ^
    --windows-disable-console ^
    --windows-icon-from-ico=assets/icon.ico ^
    --windows-company-name="AutoClicker" ^
    --windows-product-name="AutoClicker Pro" ^
    --windows-file-version=1.0.0.0 ^
    --windows-product-version=1.0.0.0 ^
    --enable-plugin=tk-inter ^
    --include-data-dir=i18n=i18n ^
    --output-filename=AutoClickerPro.exe ^
    main.py

echo.
if %errorlevel% equ 0 (
    echo ======================================
    echo  Build successful!
    echo  Output: main.dist\AutoClickerPro.exe
    echo ======================================
) else (
    echo Build failed. Check errors above.
)

pause
