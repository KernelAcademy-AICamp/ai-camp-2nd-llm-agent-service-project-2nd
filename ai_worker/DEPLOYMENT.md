# LEH AI Worker 배포 가이드

## 개요

LEH AI Worker는 S3에 업로드된 증거 파일(PDF, 이미지, 오디오, 비디오, 텍스트)을 처리하고
DynamoDB와 OpenSearch에 저장하는 AWS Lambda 기반 서비스입니다.

## 아키텍처

```
S3 (Evidence Upload)
        │
        ▼
   Lambda Function
        │
        ├──► DynamoDB (Metadata)
        │
        └──► OpenSearch (Vector Search)
```

## 사전 요구사항

### 1. AWS CLI 설치

**Windows:**
```powershell
msiexec.exe /i https://awscli.amazonaws.com/AWSCLIV2.msi
```

**macOS:**
```bash
brew install awscli
```

**Linux:**
```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

### 2. SAM CLI 설치

**Windows:**
```powershell
msiexec.exe /i https://github.com/aws/aws-sam-cli/releases/latest/download/AWS_SAM_CLI_64_PY3.msi
```

**macOS:**
```bash
brew install aws-sam-cli
```

**Linux:**
```bash
pip install aws-sam-cli
```

### 3. AWS 자격 증명 구성

```bash
aws configure
# AWS Access Key ID: [your-access-key]
# AWS Secret Access Key: [your-secret-key]
# Default region name: ap-northeast-2
# Default output format: json
```

### 4. 환경 변수 설정

```bash
# Linux/macOS
export OPENAI_API_KEY=sk-your-api-key

# Windows (PowerShell)
$env:OPENAI_API_KEY="sk-your-api-key"

# Windows (CMD)
set OPENAI_API_KEY=sk-your-api-key
```

## 배포 절차

### 빠른 배포 (스크립트 사용)

**Linux/macOS:**
```bash
cd ai_worker
chmod +x scripts/deploy.sh
./scripts/deploy.sh dev      # 개발 환경
./scripts/deploy.sh staging  # 스테이징 환경
./scripts/deploy.sh prod     # 운영 환경
```

**Windows:**
```cmd
cd ai_worker
scripts\deploy.bat dev      # 개발 환경
scripts\deploy.bat staging  # 스테이징 환경
scripts\deploy.bat prod     # 운영 환경
```

### 수동 배포

#### 1. 테스트 실행
```bash
pytest --cov=src --cov-fail-under=80
```

#### 2. SAM 템플릿 검증
```bash
sam validate --lint
```

#### 3. 빌드
```bash
sam build --use-container
```

#### 4. 배포
```bash
# 개발 환경
sam deploy --config-env dev --parameter-overrides "Environment=dev OpenAIApiKey=$OPENAI_API_KEY"

# 스테이징 환경
sam deploy --config-env staging --parameter-overrides "Environment=staging OpenAIApiKey=$OPENAI_API_KEY"

# 운영 환경 (confirm_changeset=true)
sam deploy --config-env prod --parameter-overrides "Environment=prod OpenAIApiKey=$OPENAI_API_KEY"
```

## 환경별 설정

| 환경 | 스택 이름 | S3 Bucket | DynamoDB Table |
|------|-----------|-----------|----------------|
| dev | leh-ai-worker-dev | leh-evidence-dev-{account} | leh-evidence-metadata-dev |
| staging | leh-ai-worker-staging | leh-evidence-staging-{account} | leh-evidence-metadata-staging |
| prod | leh-ai-worker-prod | leh-evidence-prod-{account} | leh-evidence-metadata-prod |

## 배포 후 확인

### 1. CloudFormation 스택 상태 확인
```bash
aws cloudformation describe-stacks --stack-name leh-ai-worker-dev --query "Stacks[0].StackStatus"
```

### 2. Lambda 함수 테스트
```bash
# S3 이벤트 시뮬레이션
aws lambda invoke \
  --function-name leh-ai-worker-dev \
  --payload '{"Records":[{"s3":{"bucket":{"name":"leh-evidence-dev-123456789012"},"object":{"key":"cases/test-case/evidence/test.txt"}}}]}' \
  --cli-binary-format raw-in-base64-out \
  response.json

cat response.json
```

### 3. CloudWatch 로그 확인
```bash
aws logs tail /aws/lambda/leh-ai-worker-dev --follow
```

## 리소스 정리 (삭제)

```bash
# 스택 삭제 (S3 버킷은 비어있어야 함)
aws cloudformation delete-stack --stack-name leh-ai-worker-dev

# S3 버킷 비우기 (필요시)
aws s3 rm s3://leh-evidence-dev-123456789012 --recursive
```

## 트러블슈팅

### 1. SAM 빌드 실패

**증상:** `sam build` 실패

**해결:**
```bash
# Docker 사용 빌드
sam build --use-container

# Python 가상환경 정리
rm -rf .aws-sam
sam build
```

### 2. 배포 권한 오류

**증상:** `AccessDenied` 또는 `UnauthorizedOperation`

**해결:**
IAM 사용자에게 다음 권한 필요:
- CloudFormation 전체 권한
- Lambda 전체 권한
- S3 전체 권한
- DynamoDB 전체 권한
- IAM 역할 생성 권한

### 3. Lambda 타임아웃

**증상:** `Task timed out after 300.00 seconds`

**해결:**
- `template.yaml`의 `Timeout` 값 증가 (최대 900초)
- 대용량 파일의 경우 Step Functions 사용 고려

### 4. OpenAI API 오류

**증상:** `openai.error.AuthenticationError`

**해결:**
- OPENAI_API_KEY 환경 변수 확인
- API 키 유효성 확인
- 잔액 확인

## 모니터링

### CloudWatch 대시보드 생성

```bash
aws cloudwatch put-dashboard --dashboard-name "LEH-AI-Worker" --dashboard-body '{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/Lambda", "Invocations", "FunctionName", "leh-ai-worker-dev"],
          [".", "Errors", ".", "."],
          [".", "Duration", ".", "."]
        ],
        "period": 300,
        "stat": "Sum",
        "region": "ap-northeast-2",
        "title": "Lambda Metrics"
      }
    }
  ]
}'
```

### 알람 설정

```bash
# 에러 알람
aws cloudwatch put-metric-alarm \
  --alarm-name "LEH-AI-Worker-Errors" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --dimensions Name=FunctionName,Value=leh-ai-worker-dev \
  --statistic Sum \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1
```

## 로컬 개발 (SAM 없이)

AWS CLI/SAM 없이 로컬에서 테스트:

```bash
cd ai_worker
python local_lambda_test.py
```

이 스크립트는 실제 파일을 사용하여 Lambda 핸들러를 로컬에서 실행합니다.

## 참고 자료

- [AWS SAM Documentation](https://docs.aws.amazon.com/serverless-application-model/)
- [Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
