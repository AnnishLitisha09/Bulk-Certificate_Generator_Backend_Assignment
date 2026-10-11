@echo off
echo ========================================================
echo Creating MySQL Database and Tables
echo ========================================================
".venv\Scripts\python.exe" init_db.py
if %ERRORLEVEL% EQU 0 (
    echo.
    echo [SUCCESS] Database and tables are ready in MySQL Workbench!
) else (
    echo.
    echo [ERROR] Table creation failed. Please check your credentials in .env.
)
