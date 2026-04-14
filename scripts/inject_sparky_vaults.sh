#!/bin/bash
set -e

# SparkyFitness Variable Injection Utility
# This script handles both plain-text and Ansible Vault encrypted files.

VAULT_PASS_FILE="${1:-~/.vault_pass.txt}"

echo "--- 🥗 SparkyFitness Variable Injector ---"
echo "Please provide the following SHARED values for the new local services:"
read -p "Sparky DB User: " SPARKY_DB_USER
read -s -p "Sparky DB Password: " SPARKY_DB_PASS; echo
read -p "Sparky App DB User: " SPARKY_APP_DB_USER
read -s -p "Sparky App DB Password: " SPARKY_APP_DB_PASS; echo
read -s -p "Sparky JWT Secret: " SPARKY_JWT; echo
read -p "Sparky Admin Email: " SPARKY_ADMIN_EMAIL
read -p "Sparky Encryption Key (use the one from the garmin service if unsure): " SPARKY_KEY

# Default for the key if not provided
SPARKY_KEY=${SPARKY_KEY:-BEF138A804503DC4916153E7F5B399FE0A0A49F37CED7081150D1397E36618D3}

echo ""
echo "--- 🌍 Environment Specific URLs ---"
read -p "Test Server Tailscale URL [https://healthcoach-test]: " TEST_URL
read -p "Prod Server Tailscale URL [https://healthcoach-prod]: " PROD_URL

TEST_URL=${TEST_URL:-https://healthcoach-test}
PROD_URL=${PROD_URL:-https://healthcoach-prod}

# Function to inject variables into a file
inject_vars() {
    local FILE=$1
    local URL=$2
    
    if [ ! -f "$FILE" ]; then
        echo "⏭️ Skipping $FILE (not found)"
        return
    fi

    echo "Processing $FILE..."
    
    local VARS=$(cat <<EOF

# --- SparkyFitness Integrated Services ---
sparky_fitness_db_name: "sparkydb"
sparky_fitness_db_user: "$SPARKY_DB_USER"
sparky_fitness_db_password: "$SPARKY_DB_PASS"
sparky_fitness_app_db_user: "$SPARKY_APP_DB_USER"
sparky_fitness_app_db_password: "$SPARKY_APP_DB_PASS"
sparky_fitness_api_encryption_key: "$SPARKY_KEY"
sparky_jwt_secret: "$SPARKY_JWT"
sparky_fitness_frontend_url: "$URL"
sparky_fitness_admin_email: "$SPARKY_ADMIN_EMAIL"
sparky_fitness_email_host: "smtp.gmail.com"
sparky_fitness_email_port: 465
sparky_fitness_email_secure: "true"
sparky_fitness_email_user: "$SPARKY_ADMIN_EMAIL"
sparky_fitness_email_pass: "your-app-password"
sparky_fitness_email_from: "SparkyFitness <$SPARKY_ADMIN_EMAIL>"
EOF
)

    # Check if the file is an Ansible Vault file
    if grep -q "\$ANSIBLE_VAULT;" "$FILE"; then
        echo "   -> Detected Vault file. Decrypting..."
        if [ ! -f "$VAULT_PASS_FILE" ]; then
            echo "❌ Error: $FILE is vaulted but $VAULT_PASS_FILE was not found."
            exit 1
        fi
        
        TMP_FILE=$(mktemp)
        ansible-vault decrypt "$FILE" --vault-password-file "$VAULT_PASS_FILE" --output "$TMP_FILE"
        echo "$VARS" >> "$TMP_FILE"
        ansible-vault encrypt "$TMP_FILE" --vault-password-file "$VAULT_PASS_FILE" --output "$FILE"
        rm "$TMP_FILE"
        echo "✅ Vaulted file updated."
    else
        echo "   -> Detected plain-text file. Appending..."
        echo "$VARS" >> "$FILE"
        echo "✅ Plain-text file updated."
    fi
}

inject_vars "infra/ansible/inventory/group_vars/test.yml" "$TEST_URL"
inject_vars "infra/ansible/inventory/group_vars/prod.yml" "$PROD_URL"

echo "🎉 All configuration files updated."
