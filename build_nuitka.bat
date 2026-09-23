@echo off
echo ======================================
echo  Building AutoClicker with Nuitka
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
    --onefile-tempdir-spec="{CACHE_DIR}/{COMPANY}/{PRODUCT}/{VERSION}" ^
    --assume-yes-for-downloads ^
    --windows-console-mode=disable ^
    --windows-icon-from-ico=assets/icon.ico ^
    --windows-company-name="AutoClicker" ^
    --windows-product-name="AutoClicker" ^
    --windows-file-version=1.0.0.0 ^
    --windows-product-version=1.0.0.0 ^
    --enable-plugin=tk-inter ^
    --include-package-data=customtkinter ^
    --include-data-dir=assets=assets ^
    --output-filename=AutoClicker.exe ^
    main.py

echo.
if %errorlevel% equ 0 (
    echo ======================================
    echo  Build successful!
    echo  File .exe duoc tao tai:
    echo  %~dp0AutoClicker.exe
    echo ======================================
) else (
    echo Build failed. Check errors above.
)

pause
