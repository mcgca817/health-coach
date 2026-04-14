#!/bin/bash
set -e # Exit immediately if a command exits with a non-zero status

# Set Vault password parameter if it exists
VAULT_ARG=""
if [ -f ~/.vault_pass.txt ]; then
    VAULT_ARG="--vault-password-file ~/.vault_pass.txt"
fi

echo "=========================================================="
echo "🛡️  HEALTH COACH GATED DEPLOYMENT PIPELINE"
echo "=========================================================="

echo ""
echo "🚀 PHASE 1: Deploying latest configuration to TEST..."
echo "----------------------------------------------------------"
cd infra/ansible
ansible-playbook -i inventory/hosts.ini playbooks/deploy.yml --limit test $VAULT_ARG || { echo "❌ ERROR: Test deployment failed"; exit 1; }

echo ""
echo "🧪 PHASE 2: Running Comprehensive Test Suite on TEST..."
echo "----------------------------------------------------------"
# Get the IP of the test server from the inventory file
TEST_IP=$(awk '/^\[test\]/{flag=1; next} /^\[/{flag=0} flag {print $2}' inventory/hosts.ini | cut -d'=' -f2 | head -n 1)

echo "📡 Connecting to: cameron@$TEST_IP"
echo "📂 Working directory: /opt/healthcoach"
echo ""

# SSH into the test server and run pytest inside the healthcoach-bot container
ssh -o StrictHostKeyChecking=no cameron@$TEST_IP "docker exec -t healthcoach-bot /app/entrypoint.sh test" || { 
    echo ""
    echo "❌ CRITICAL: Tests failed on the test server!"
    echo "🚨 DEPLOYMENT ABORTED: Production environment remains untouched."
    exit 1 
}

echo ""
echo "✅ SUCCESS: All tests passed on Test Server."
echo "----------------------------------------------------------"

echo ""
echo "🛡️  PHASE 2.5: Running Vulnerability Scan (Trivy)..."
echo "----------------------------------------------------------"
# Clean trivy cache to ensure space and fresh database
ssh -o StrictHostKeyChecking=no cameron@$TEST_IP "trivy clean --scan-cache"

# Scan the live container for OS and Python library vulnerabilities
if ssh -o StrictHostKeyChecking=no cameron@$TEST_IP "trivy image --severity HIGH,CRITICAL --no-progress healthcoach-healthcoach-bot"; then
    echo ""
    echo "✅ SECURITY: No High/Critical vulnerabilities detected."
    echo "=========================================================="
else
    echo ""
    echo "🚨 VULNERABILITY ALERT: High/Critical security issues found!"
    echo "🔍 ACTION REQUIRED: Patch dependencies before proceeding to production."
    exit 1
fi

echo ""
echo "🌍 PHASE 3: Deploying verified configuration to PRODUCTION..."
echo "----------------------------------------------------------"
ansible-playbook -i inventory/hosts.ini playbooks/deploy.yml --limit prod $VAULT_ARG || { echo "❌ ERROR: Production deployment failed"; exit 1; }

echo ""
echo "🎉 DEPLOYMENT COMPLETE: Production is now up to date and verified!"
echo "=========================================================="
