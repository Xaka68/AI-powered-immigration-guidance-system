#!/usr/bin/env bash
# deploy.sh — Deploy Integreat Compass to AWS App Runner from GitHub source.
#
# Prerequisites:
#   1. AWS CLI v2 installed and configured (aws configure)
#   2. GitHub connection created in App Runner console (one-time setup)
#   3. Secrets stored in SSM Parameter Store
#
# Usage:
#   export GITHUB_CONNECTION_ARN="arn:aws:apprunner:eu-central-1:123456789:connection/github/..."
#   export LLM_API_KEY_ARN="arn:aws:ssm:eu-central-1:123456789:parameter/compass/llm-api-key"
#   bash infra/deploy.sh

set -euo pipefail

REGION="${AWS_REGION:-eu-central-1}"
REPO_URL="${GITHUB_REPO_URL:-https://github.com/<YOUR_ORG>/AI-powered-immigration-guidance-system}"
BRANCH="${DEPLOY_BRANCH:-main}"

echo "=== Deploying Integreat Compass to AWS App Runner ==="
echo "Region: $REGION"
echo "Repo:   $REPO_URL"
echo "Branch: $BRANCH"
echo ""

# ─── 1. Create backend service ─────────────────────────────────────────────────
echo ">>> Creating backend service..."

aws apprunner create-service \
  --region "$REGION" \
  --service-name compass-backend \
  --source-configuration '{
    "AuthenticationConfiguration": {
      "ConnectionArn": "'"${GITHUB_CONNECTION_ARN}"'"
    },
    "AutoDeploymentsEnabled": true,
    "CodeRepository": {
      "RepositoryUrl": "'"${REPO_URL}"'",
      "SourceCodeVersion": {
        "Type": "BRANCH",
        "Value": "'"${BRANCH}"'"
      },
      "CodeConfiguration": {
        "ConfigurationSource": "API",
        "CodeConfigurationValues": {
          "Runtime": "PYTHON_312",
          "BuildCommand": "pip install -e backend/",
          "StartCommand": "uvicorn api.main:app --host 0.0.0.0 --port 8000 --app-dir backend/src",
          "Port": "8000",
          "RuntimeEnvironmentVariables": {
            "LLM_BASE_URL": "https://api.openai.com/v1",
            "LLM_MODEL": "gpt-4o-mini",
            "EMBED_MODEL": "intfloat/multilingual-e5-large",
            "INTEGREAT_REGION": "testumgebung-frag-integreat",
            "APP_ROOT": "/app"
          }
        }
      }
    }
  }' \
  --instance-configuration '{
    "Cpu": "1 vCPU",
    "Memory": "2 GB"
  }' \
  --health-check-configuration '{
    "Protocol": "HTTP",
    "Path": "/health",
    "Interval": 10,
    "Timeout": 5,
    "HealthyThreshold": 1,
    "UnhealthyThreshold": 5
  }'

echo ""
echo ">>> Backend service created. It will take 2-5 minutes to build and deploy."
echo "    Check status: aws apprunner list-services --region $REGION"
echo ""

# ─── 2. Wait for backend URL ───────────────────────────────────────────────────
echo ">>> Waiting for backend URL..."
sleep 10

BACKEND_URL=$(aws apprunner list-services --region "$REGION" \
  --query "ServiceSummaryList[?ServiceName=='compass-backend'].ServiceUrl" \
  --output text)

if [ -z "$BACKEND_URL" ]; then
  echo "Backend URL not yet available. Deploy frontend manually after backend is RUNNING."
  echo "  aws apprunner list-services --region $REGION"
  exit 0
fi

echo "Backend URL: https://$BACKEND_URL"
echo ""

# ─── 3. Create frontend service ────────────────────────────────────────────────
echo ">>> Creating frontend service..."

aws apprunner create-service \
  --region "$REGION" \
  --service-name compass-frontend \
  --source-configuration '{
    "AuthenticationConfiguration": {
      "ConnectionArn": "'"${GITHUB_CONNECTION_ARN}"'"
    },
    "AutoDeploymentsEnabled": true,
    "CodeRepository": {
      "RepositoryUrl": "'"${REPO_URL}"'",
      "SourceCodeVersion": {
        "Type": "BRANCH",
        "Value": "'"${BRANCH}"'"
      },
      "CodeConfiguration": {
        "ConfigurationSource": "API",
        "CodeConfigurationValues": {
          "Runtime": "NODEJS_18",
          "BuildCommand": "cd frontend && npm ci && npm run build",
          "StartCommand": "cd frontend && node .output/server/index.mjs",
          "Port": "3000",
          "RuntimeEnvironmentVariables": {
            "VITE_API_URL": "https://'"${BACKEND_URL}"'",
            "VITE_USE_MOCK": "false"
          }
        }
      }
    }
  }' \
  --instance-configuration '{
    "Cpu": "0.25 vCPU",
    "Memory": "0.5 GB"
  }' \
  --health-check-configuration '{
    "Protocol": "HTTP",
    "Path": "/",
    "Interval": 10,
    "Timeout": 5,
    "HealthyThreshold": 1,
    "UnhealthyThreshold": 5
  }'

echo ""
echo "=== Done ==="
echo "Frontend and backend deploying. Both will get HTTPS URLs automatically."
echo "Check: aws apprunner list-services --region $REGION"
