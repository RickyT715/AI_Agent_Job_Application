@echo off
setlocal enabledelayedexpansion

echo ============================================================
echo   AI Job Application Agent - Installation
echo ============================================================
echo.

:: ------------------------------------------------------------------
:: Check prerequisites
:: ------------------------------------------------------------------
echo [1/6] Checking prerequisites...

where uv >nul 2>&1
if errorlevel 1 (
    echo ERROR: uv is not installed.
    echo Install it from: https://docs.astral.sh/uv/getting-started/installation/
    echo   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    exit /b 1
)
echo   [OK] uv found

where node >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed.
    echo Install it from: https://nodejs.org/ (v22+ recommended^)
    exit /b 1
)
echo   [OK] Node.js found

where docker >nul 2>&1
if errorlevel 1 (
    echo WARNING: Docker is not installed.
    echo Docker is required for run.bat. Install from: https://www.docker.com/products/docker-desktop/
    echo Continuing with local installation...
) else (
    echo   [OK] Docker found
)

echo.

:: ------------------------------------------------------------------
:: Backend dependencies
:: ------------------------------------------------------------------
echo [2/6] Installing backend dependencies...
cd /d "%~dp0backend"
uv sync --dev
if errorlevel 1 (
    echo ERROR: Backend dependency installation failed.
    exit /b 1
)
echo   [OK] Backend dependencies installed
echo.

:: ------------------------------------------------------------------
:: Frontend dependencies
:: ------------------------------------------------------------------
echo [3/6] Installing frontend dependencies...
cd /d "%~dp0frontend"
call npm ci
if errorlevel 1 (
    echo npm ci failed, trying npm install...
    call npm install
    if errorlevel 1 (
        echo ERROR: Frontend dependency installation failed.
        exit /b 1
    )
)
echo   [OK] Frontend dependencies installed
echo.

:: ------------------------------------------------------------------
:: Create .env from example if missing
:: ------------------------------------------------------------------
echo [4/6] Configuring environment...
cd /d "%~dp0"
if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo   Created .env from .env.example
    echo   IMPORTANT: Edit .env and add your API keys before running!
) else (
    echo   [OK] .env already exists
)
echo.

:: ------------------------------------------------------------------
:: Create data directory
:: ------------------------------------------------------------------
echo [5/6] Creating data directories...
cd /d "%~dp0backend"
if not exist "data" mkdir data
if not exist "data\chroma_db" mkdir data\chroma_db
echo   [OK] Data directories ready
echo.

:: ------------------------------------------------------------------
:: Run tests to verify installation
:: ------------------------------------------------------------------
echo [6/6] Running tests to verify installation...
echo.

echo --- Backend Tests ---
cd /d "%~dp0backend"
uv run pytest -m "not integration and not docker" -q --tb=line 2>&1
if errorlevel 1 (
    echo WARNING: Some backend tests failed. Check output above.
) else (
    echo   [OK] Backend tests passed
)
echo.

echo --- Frontend Tests ---
cd /d "%~dp0frontend"
call npx vitest run 2>&1
if errorlevel 1 (
    echo WARNING: Some frontend tests failed. Check output above.
) else (
    echo   [OK] Frontend tests passed
)
echo.

:: ------------------------------------------------------------------
:: Done
:: ------------------------------------------------------------------
cd /d "%~dp0"
echo ============================================================
echo   Installation complete!
echo ============================================================
echo.
echo   Next steps:
echo     1. Edit .env and add your API keys:
echo        - GOOGLE_API_KEY    (Gemini - free tier)
echo        - ANTHROPIC_API_KEY (Claude)
echo        - JSEARCH_API_KEY   (RapidAPI JSearch)
echo.
echo     2. Start the application:
echo        run.bat             (Docker - recommended)
echo        run.bat --local     (Local dev servers)
echo.

endlocal
