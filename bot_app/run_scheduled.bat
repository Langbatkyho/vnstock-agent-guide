@echo off
title Quet Toan Bo Watchlist (scheduled_run.py)
cd /d "%~dp0"

:: Bat che do ho tro Unicode UTF-8 de tranh UnicodeEncodeError tren Windows
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8


:: Tao thu muc logs neu chua co de ghi nhan log cua Batch
if not exist "logs" mkdir "logs"

:: Check xem co phai chay tu dong bang Task Scheduler hay khong
if "%1"=="--scheduled" (
    set IS_SCHEDULED=1
) else (
    set IS_SCHEDULED=0
)

:: Neu la chay tu dong, ghi log bat dau cua Batch file
if %IS_SCHEDULED%==1 (
    echo ========================================================== >> logs\run_scheduled_batch.log
    echo [BATCH LOG] BAT DAU CHUYEN QUET TU DONG luc %DATE% %TIME% >> logs\run_scheduled_batch.log
)

:: Kich hoat moi truong ao Python bang nhieu duong dan khac nhau de dam bao on dinh tren Task Scheduler
set VENV_PATH=""

if exist "%USERPROFILE%\.venv\Scripts\activate.bat" (
    set VENV_PATH="%USERPROFILE%\.venv\Scripts\activate.bat"
) else if exist "C:\Users\Langbatkyho\.venv\Scripts\activate.bat" (
    set VENV_PATH="C:\Users\Langbatkyho\.venv\Scripts\activate.bat"
) else if exist "%~dp0..\.venv\Scripts\activate.bat" (
    set VENV_PATH="%~dp0..\.venv\Scripts\activate.bat"
)

if not %VENV_PATH% == "" (
    if %IS_SCHEDULED%==1 (
        echo [BATCH LOG] Kich hoat moi truong ao tai %VENV_PATH% >> logs\run_scheduled_batch.log
    ) else (
        echo Kich hoat moi truong ao tai %VENV_PATH% thanh cong!
    )
    call %VENV_PATH%
) else (
    if %IS_SCHEDULED%==1 (
        echo [BATCH LOG] CANH BAO: Khong tim thay moi truong ao. Se dung Python mac dinh he thong. >> logs\run_scheduled_batch.log
    ) else (
        echo [CANH BAO] Khong tim thay moi truong ao. Se dung Python mac dinh he thong.
    )
)

:: Thuc thi Python dua tren che do chay
if %IS_SCHEDULED%==1 (
    echo [BATCH LOG] Dang chay scheduled_run.py... >> logs\run_scheduled_batch.log
    python scheduled_run.py >> logs\run_scheduled_batch.log 2>&1
    echo [BATCH LOG] Hoan thanh quet tu dong luc %DATE% %TIME% >> logs\run_scheduled_batch.log
    
    :: Tu dong thoat sau 3 giay neu chay tu dong
    timeout /t 3 >nul
) else (
    echo ==========================================================
    echo       DANG QUET WATCHLIST - BOT THEO DOI CO PHIEU
    echo ==========================================================
    echo.
    echo Dang chay scheduled_run.py...
    python scheduled_run.py
    echo.
    echo ==========================================================
    echo Hoan thanh. Nhan phim bat ky de thoat.
    echo ==========================================================
    pause
)
