@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title AI Job Application Agent

:: ------------------------------------------------------------------
:: Parse arguments
:: ------------------------------------------------------------------
set MODE=docker
set ACTION=start

:parse_args
if "%~1"=="" goto done_args
if /i "%~1"=="--local" set MODE=local& shift & goto parse_args
if /i "%~1"=="--stop" set ACTION=stop& shift & goto parse_args
if /i "%~1"=="--build" set ACTION=build& shift & goto parse_args
if /i "%~1"=="--logs" set ACTION=logs& shift & goto parse_args
if /i "%~1"=="--help" goto show_help
if /i "%~1"=="-h" goto show_help
shift
goto parse_args
:done_args

:: ------------------------------------------------------------------
:: Help
:: ------------------------------------------------------------------
if "%ACTION%"=="help" goto show_help
goto check_env

:show_help
echo.
echo   AI Job Application Agent - Runner
echo.
echo   Usage:  run.bat [options]
echo.
echo   Options:
echo     (default)     Start with Docker Compose (recommended)
echo     --local       Start local dev servers (no Docker)
echo     --stop        Stop all Docker Compose services
echo     --build       Force rebuild Docker images and start
echo     --logs        Tail Docker Compose logs
echo     -h, --help    Show this help
echo.
echo   Examples:
echo     run.bat               Start all services via Docker
echo     run.bat --build       Rebuild images then start
echo     run.bat --local       Start backend + frontend locally
echo     run.bat --stop        Stop Docker services
echo.
goto end_ok

:: ------------------------------------------------------------------
:: Check .env exists
:: ------------------------------------------------------------------
:check_env
if not exist ".env" (
    echo.
    echo   ERROR: .env file not found.
    echo   Run install.bat first, or copy .env.example to .env and add your API keys.
    echo.
    goto end_error
)

:: ------------------------------------------------------------------
:: Docker: stop
:: ------------------------------------------------------------------
if "%ACTION%"=="stop" (
    echo Stopping Docker Compose services...
    docker compose down
    if errorlevel 1 (
        echo.
        echo   ERROR: Failed to stop services. Is Docker running?
        goto end_error
    )
    echo   Done.
    goto end_ok
)

:: ------------------------------------------------------------------
:: Docker: logs
:: ------------------------------------------------------------------
if "%ACTION%"=="logs" (
    docker compose logs -f
    goto end_ok
)

:: ------------------------------------------------------------------
:: Local mode
:: ------------------------------------------------------------------
if "%MODE%"=="local" goto run_local

:: ------------------------------------------------------------------
:: Docker mode
:: ------------------------------------------------------------------
:run_docker
echo.
echo ============================================================
echo   AI Job Application Agent - Docker Mode
echo ============================================================
echo.

:: Check Docker daemon is running
echo   Checking Docker...
docker info >nul 2>&1
if errorlevel 1 (
    echo.
    echo   ERROR: Docker is not running.
    echo   Please start Docker Desktop and wait for it to fully load,
    echo   then run this script again.
    echo.
    goto end_error
)
echo   [OK] Docker is running
echo.

:: Check if images exist; auto-build on first run
set NEED_BUILD=0
if "%ACTION%"=="build" set NEED_BUILD=1

:: Check if backend image exists
docker images --format "{{.Repository}}" 2>nul | findstr /i "ai_agent_job_application-backend" >nul 2>&1
if errorlevel 1 set NEED_BUILD=1

:: Check if frontend image exists
docker images --format "{{.Repository}}" 2>nul | findstr /i "ai_agent_job_application-frontend" >nul 2>&1
if errorlevel 1 set NEED_BUILD=1

if !NEED_BUILD!==1 (
    echo   Building Docker images (this may take a few minutes on first run)...
    echo.
    docker compose build
    if errorlevel 1 (
        echo.
        echo   ERROR: Docker build failed. Check the output above for details.
        echo.
        goto end_error
    )
    echo.
    echo   [OK] Images built successfully
    echo.
)

echo   Starting services...
docker compose up -d
if errorlevel 1 (
    echo.
    echo   ERROR: Docker Compose failed to start.
    echo   Check logs with: run.bat --logs
    echo.
    goto end_error
)

echo.
echo   Waiting for services to become healthy...

:: Wait and check health in a loop (up to 60 seconds)
set TRIES=0
:health_loop
if !TRIES! GEQ 12 goto health_done
timeout /t 5 /nobreak >nul
set /a TRIES+=1

:: Check if all services are up
docker compose ps --format "{{.Service}}: {{.Status}}" 2>nul | findstr /i "unhealthy" >nul
if errorlevel 1 goto health_done
echo     ...still waiting (!TRIES!/12)
goto health_loop

:health_done
echo.

:: Show service status
echo   Service Status:
docker compose ps --format "    {{.Service}}: {{.Status}}" 2>nul
echo.

echo ============================================================
echo   Services started!
echo ============================================================
echo.
echo   Frontend:    http://localhost:3000
echo   Backend API: http://localhost:8000
echo   API Docs:    http://localhost:8000/docs
echo   PostgreSQL:  localhost:5432
echo   Redis:       localhost:6379
echo.
echo   Commands:
echo     run.bat --logs      View logs
echo     run.bat --stop      Stop all services
echo     run.bat --build     Rebuild and restart
echo.
echo   Showing live logs below (press Ctrl+C to detach,
echo   services will keep running in background)...
echo.
echo ============================================================
echo.

docker compose logs -f
goto end_ok

:: ------------------------------------------------------------------
:: Local dev mode (no Docker)
:: ------------------------------------------------------------------
:run_local
echo.
echo ============================================================
echo   AI Job Application Agent - Local Dev Mode
echo ============================================================
echo.
echo   Starting backend and frontend dev servers locally.
echo   (No PostgreSQL/Redis needed - uses SQLite + in-memory queue)
echo.

:: Check uv is available
where uv >nul 2>&1
if errorlevel 1 (
    echo   ERROR: uv not found. Run install.bat first.
    goto end_error
)

:: Check node is available
where node >nul 2>&1
if errorlevel 1 (
    echo   ERROR: Node.js not found. Run install.bat first.
    goto end_error
)

:: Start backend in a new window
echo   Starting backend server...
set "BACKEND_DIR=%~dp0backend"
start "Backend - FastAPI" cmd /k "cd /d ""%BACKEND_DIR%"" && uv run uvicorn app.main:app --reload --port 8000"

:: Small delay so backend starts first
timeout /t 3 /nobreak >nul

:: Start frontend in a new window
echo   Starting frontend dev server...
set "FRONTEND_DIR=%~dp0frontend"
start "Frontend - Vite" cmd /k "cd /d ""%FRONTEND_DIR%"" && npm run dev"

echo.
echo ============================================================
echo   Local dev servers starting!
echo ============================================================
echo.
echo   Frontend:    http://localhost:5173
echo   Backend API: http://localhost:8000
echo   API Docs:    http://localhost:8000/docs
echo.
echo   Two new windows opened - one for backend, one for frontend.
echo   Close those windows to stop the servers.
echo.
goto end_ok

:: ------------------------------------------------------------------
:: Exit handlers - keep window open so user can see output
:: ------------------------------------------------------------------
:end_error
echo.
echo   Press any key to exit...
pause >nul
endlocal
exit /b 1

:end_ok
endlocal
exit /b 0
