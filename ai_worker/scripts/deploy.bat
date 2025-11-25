@echo off
REM LEH AI Worker Deployment Script (Windows)
REM Usage: deploy.bat [dev|staging|prod]

setlocal enabledelayedexpansion

set ENVIRONMENT=%1
if "%ENVIRONMENT%"=="" set ENVIRONMENT=dev

echo ========================================
echo   LEH AI Worker Deployment
echo   Environment: %ENVIRONMENT%
echo ========================================

REM Validate environment
if not "%ENVIRONMENT%"=="dev" if not "%ENVIRONMENT%"=="staging" if not "%ENVIRONMENT%"=="prod" (
    echo Error: Invalid environment. Use: dev, staging, or prod
    exit /b 1
)

REM Check prerequisites
echo.
echo [1/6] Checking prerequisites...

where aws >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: AWS CLI not installed
    echo Install: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
    exit /b 1
)

where sam >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: SAM CLI not installed
    echo Install: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html
    exit /b 1
)

REM Verify AWS credentials
aws sts get-caller-identity >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: AWS credentials not configured
    echo Run: aws configure
    exit /b 1
)

for /f "tokens=*" %%i in ('aws sts get-caller-identity --query Account --output text') do set AWS_ACCOUNT=%%i
echo AWS Account: %AWS_ACCOUNT%

REM Check OpenAI API Key
echo.
echo [2/6] Checking environment variables...

if "%OPENAI_API_KEY%"=="" (
    echo Error: OPENAI_API_KEY environment variable not set
    echo Set it with: set OPENAI_API_KEY=your-api-key
    exit /b 1
)
echo OPENAI_API_KEY is set

REM Run tests
echo.
echo [3/6] Running tests...

pytest --cov=src --cov-fail-under=80 -q
if %errorlevel% neq 0 (
    echo Error: Tests failed or coverage below 80%%
    exit /b 1
)
echo Tests passed

REM Validate SAM template
echo.
echo [4/6] Validating SAM template...

sam validate --lint
if %errorlevel% neq 0 (
    echo Error: SAM template validation failed
    exit /b 1
)
echo SAM template is valid

REM Build the application
echo.
echo [5/6] Building application...

sam build --use-container
if %errorlevel% neq 0 (
    echo Error: Build failed
    exit /b 1
)
echo Build successful

REM Deploy
echo.
echo [6/6] Deploying to %ENVIRONMENT%...

if "%ENVIRONMENT%"=="prod" (
    echo WARNING: Deploying to PRODUCTION!
    set /p confirm="Are you sure? (yes/no): "
    if not "!confirm!"=="yes" (
        echo Deployment cancelled
        exit /b 0
    )
)

sam deploy --config-env %ENVIRONMENT% --parameter-overrides "Environment=%ENVIRONMENT% OpenAIApiKey=%OPENAI_API_KEY%"
if %errorlevel% neq 0 (
    echo Error: Deployment failed
    exit /b 1
)

echo.
echo ========================================
echo   Deployment Complete!
echo ========================================

REM Get stack outputs
echo.
echo Stack Outputs:
aws cloudformation describe-stacks --stack-name "leh-ai-worker-%ENVIRONMENT%" --query "Stacks[0].Outputs[*].[OutputKey,OutputValue]" --output table

echo.
echo Done!
