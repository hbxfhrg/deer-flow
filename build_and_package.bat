@echo off
chcp 65001 >nul
cls

echo ================================================
echo          DeerFlow Build and Package
echo ================================================
echo Ports:
echo   - deeragent: 3000 (managed by other service)
echo   - backend: 8001
echo   - frontend: 4000
echo ================================================
echo Note: This script does NOT include MySQL image
echo Please use external MySQL database
echo ================================================
echo.

set "IMAGE_NAME_BACKEND=deerflow-backend"
set "IMAGE_NAME_FRONTEND=deerflow-frontend"
set "TAG=latest"
set "OUTPUT_DIR=./docker-images"

echo [1/3] Creating output directory...
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

echo.
echo [2/3] Preparing configuration files...
if exist "config.yaml" (
    copy config.yaml backend\config.yaml >nul
    echo   - Copied root config.yaml to backend\config.yaml
) else if exist "config.example.yaml" (
    copy config.example.yaml backend\config.yaml >nul
    echo   - Copied config.example.yaml to backend\config.yaml
) else (
    echo WARNING: No config.yaml found, using existing backend\config.yaml if available
)

echo.
echo [3/3] Building backend image...
cd backend
docker build -t %IMAGE_NAME_BACKEND%:%TAG% .
if %errorlevel% neq 0 (
    echo ERROR: Failed to build backend image
    pause
    exit /b 1
)
cd ..

echo.
echo [4/3] Building frontend image...
cd practice
docker build -t %IMAGE_NAME_FRONTEND%:%TAG% .
if %errorlevel% neq 0 (
    echo ERROR: Failed to build frontend image
    pause
    exit /b 1
)
cd ..

echo.
echo [5/3] Saving images to tar files...
docker save %IMAGE_NAME_BACKEND%:%TAG% -o "%OUTPUT_DIR%/%IMAGE_NAME_BACKEND%.tar"
docker save %IMAGE_NAME_FRONTEND%:%TAG% -o "%OUTPUT_DIR%/%IMAGE_NAME_FRONTEND%.tar"

echo.
echo [6/3] Generating deployment script...

echo @echo off > "%OUTPUT_DIR%/deploy.bat"
echo echo [1/4] Loading backend image... >> "%OUTPUT_DIR%/deploy.bat"
echo docker load -i deerflow-backend.tar >> "%OUTPUT_DIR%/deploy.bat"
echo echo [2/4] Loading frontend image... >> "%OUTPUT_DIR%/deploy.bat"
echo docker load -i deerflow-frontend.tar >> "%OUTPUT_DIR%/deploy.bat"
echo echo [3/4] Starting services... >> "%OUTPUT_DIR%/deploy.bat"
echo docker-compose -f docker-compose.prod.yml up -d >> "%OUTPUT_DIR%/deploy.bat"
echo echo Deployment completed! >> "%OUTPUT_DIR%/deploy.bat"
echo echo Backend: http://localhost:8001 >> "%OUTPUT_DIR%/deploy.bat"
echo echo Frontend: http://localhost:4000 >> "%OUTPUT_DIR%/deploy.bat"
echo pause >> "%OUTPUT_DIR%/deploy.bat"

copy docker-compose.prod.yml "%OUTPUT_DIR%/" /Y
copy .env "%OUTPUT_DIR%/" /Y
copy backend\config.yaml "%OUTPUT_DIR%/" /Y

echo.
echo ================================================
echo          Package Completed!
echo ================================================
echo Output Directory: %OUTPUT_DIR%
echo Files:
echo   - deerflow-backend.tar
echo   - deerflow-frontend.tar
echo   - docker-compose.prod.yml
echo   - .env
echo   - config.yaml
echo   - deploy.bat
echo.
echo ================================================
echo          Pre-deployment Checklist
echo ================================================
echo 1. Install MySQL 8.0+ on target server
echo 2. Create database: CREATE DATABASE deer_flow DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
echo 3. Create user: GRANT ALL ON deer_flow.* TO 'deerflow'@'%' IDENTIFIED BY 'deerflow@2024';
echo 4. Update .env with correct database connection
echo 5. Update config.yaml with your LLM API key and other settings
echo 6. Run deploy.bat to start services
echo ================================================
echo.
pause