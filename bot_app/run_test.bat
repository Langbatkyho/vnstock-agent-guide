@echo off
:: Bat che do ho tro Unicode UTF-8 de tranh UnicodeEncodeError tren Windows
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

title Chay Thu Bot Theo Doi Co Phieu (test_run.py)
echo ==========================================================
echo       DANG KICH HOAT TEST RUN - BOT THEO DOI CO PHIEU
echo ==========================================================
echo.
cd /d "%~dp0"
echo Thu muc lam viec hien tai: %CD%
echo.

:: Kich hoat moi truong ao Python bang nhieu duong dan khac nhau de dam bao on dinh
set VENV_PATH=""

if exist "%USERPROFILE%\.venv\Scripts\activate.bat" (
    set VENV_PATH="%USERPROFILE%\.venv\Scripts\activate.bat"
) else if exist "C:\Users\Langbatkyho\.venv\Scripts\activate.bat" (
    set VENV_PATH="C:\Users\Langbatkyho\.venv\Scripts\activate.bat"
) else if exist "%~dp0..\.venv\Scripts\activate.bat" (
    set VENV_PATH="%~dp0..\.venv\Scripts\activate.bat"
)

if not %VENV_PATH% == "" (
    echo Kich hoat moi truong ao tai %VENV_PATH% thanh cong!
    call %VENV_PATH%
) else (
    echo [CANH BAO] Khong tim thay moi truong ao Python nao.
    echo Bot se chay bang Python mac dinh cua he thong.
)
echo.

echo Dang chay test_run.py...
python test_run.py
echo.
echo ==========================================================
echo Chuong trinh da chay xong. Nhan phim bat ky de thoat.
echo ==========================================================
pause
