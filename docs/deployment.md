# 🚢 Deployment & DevOps

The system uses a gated CI/CD pipeline to ensure that no broken code or configuration reaches the production environment.

## 🏁 The Gated Pipeline (`deploy.sh`)

To deploy changes, run the following from your Mac:
```bash
./deploy.sh
```

**Workflow:**
1.  **Stage 1: Test Deployment**: Ansible deploys the latest code and configuration to the `[test]` host defined in `inventory/hosts.ini`.
2.  **Stage 2: Verification**: The script SSHs into the test server and runs the full **Pytest** suite against the live test database.
3.  **Stage 3: Gate**: If tests fail, the script exits immediately. Production is not touched.
4.  **Stage 4: Production Deployment**: If tests pass, Ansible proceeds to deploy to the `[prod]` host.

## 🏗️ Infrastructure (Ansible)

*   **Roles**:
    *   `common`: Basic server hardening, timezones, and essential packages (`rsync`, `python3-venv`, `libpq-dev`).
    *   `docker`: Installs Docker Engine and the Compose plugin.
    *   `healthcoach`: Manages the application code, systemd services, timers, and rclone configuration.
*   **Systemd Services**:
    *   `healthcoach-bot.service`: Keeps the Telegram bot running 24/7.
    *   `health-sync.timer`: Triggers a database sync every hour.
    *   `healthcoach-export.timer`: Triggers the Google Drive CSV export daily at 8:00 PM.

## 🔐 Credentials Management

*   **Inventory Variables**: Located in `infra/ansible/inventory/group_vars/`.
    *   `test.yml` and `prod.yml` contain environment-specific settings.
*   **Best Practice**: Use **Ansible Vault** to encrypt these files. If using a vault, ensure your password is in `~/.vault_pass.txt` for the `deploy.sh` script to pick it up automatically.
