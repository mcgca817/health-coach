#!/bin/bash
set -e # Exit immediately if a command exits with a non-zero status

# Set Vault password parameter if it exists (for automated scripts or pass-through)
VAULT_ARG=""
if [ -f ~/.vault_pass.txt ]; then
    VAULT_ARG="--vault-password-file ~/.vault_pass.txt"
fi

echo "=========================================================="
echo "🚀 STEP 1: Deploying to TEST environment..."
echo "=========================================================="
cd infra/ansible
ansible-playbook -i inventory/hosts.ini playbooks/deploy.yml --limit test $VAULT_ARG || { echo "❌ Test deployment failed"; exit 1; }

echo ""
echo "=========================================================="
echo "🧪 STEP 2: Running Integration Tests on TEST server..."
echo "=========================================================="
# Get the IP of the test server from the inventory file
TEST_IP=$(awk '/^\[test\]/{flag=1; next} /^\[/{flag=0} flag {print $2}' inventory/hosts.ini | cut -d'=' -f2 | head -n 1)

# SSH into the test server and run pytest
ssh -o StrictHostKeyChecking=no cameron@$TEST_IP "cd /opt/healthcoach && venv/bin/python3 -m pytest tests/ -v" || { 
    echo "❌ Tests failed on the test server! Aborting production deployment."
    exit 1 
}

echo ""
echo "=========================================================="
echo "✅ STEP 3: Tests passed! Deploying to PRODUCTION environment..."
echo "=========================================================="
ansible-playbook -i inventory/hosts.ini playbooks/deploy.yml --limit prod $VAULT_ARG || { echo "❌ Production deployment failed"; exit 1; }

echo ""
echo "🎉 Full deployment to Production successful!"
