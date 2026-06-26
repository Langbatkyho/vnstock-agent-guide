@echo off
:: Bat che do ho tro Unicode UTF-8 de tranh UnicodeEncodeError tren Windows
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

title Bot Theo Doi Co Phieu (Chay Lien Tuc)
echo ==========================================================
echo       DANG KICH HOAT BOT THEO DOI CO PHIEU LIEN TUC
echo ==========================================================
echo.
cd /d "%~dp0"

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

echo Dang chay main.py (Vong lap vo han voi schedule)...
echo Nhan [Ctrl + C] de dung bot bat ky luc nao.
echo.
python main.py
echo.
echo ==========================================================
echo Bot da dung hoat dong.
echo ==========================================================
