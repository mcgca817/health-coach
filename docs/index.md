Health Coach — Documentation Index

This repository implements a personal AI-powered health coaching system. Use these docs as a quick reference for components, running the services, and where to find source code.

Overview
- Decision Engine: AI logic and report generation ([app/decision_engine](app/decision_engine))
- ETL: Data ingestion from external fitness services ([app/etl](app/etl) and `etl/`)
- Telegram Bot: User interface for daily reports and commands ([app/bot](app/bot))
- Sync: Data synchronization helpers ([app/sync](app/sync))
- Database utilities: Connection and run-history utilities ([app/db.py](app/db.py))

Quickstart (developer)
1. Create or provide an environment file at `/opt/healthcoach/.env` containing Telegram and Postgres credentials used by the services.
2. Install Python dependencies (the project uses a per-app requirements file at `app/requirements.txt`).

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r app/requirements.txt
```

3. Example: run the Telegram bot locally (reads `/opt/healthcoach/.env` by default):

```bash
python -m app.bot.main
```

4. To run Ansible deployment from the infra folder:

```bash
cd infra/ansible
ansible-playbook -i inventory/hosts.ini playbooks/deploy.yml --limit test --vault-password-file ~/.vault_pass.txt
```

Where to go next
- App internals: [app/](app/)
- Decision engine details: [docs/decision_engine.md](docs/decision_engine.md)
- ETL scripts: [docs/etl.md](docs/etl.md)
- Ansible infra: [docs/infra_ansible.md](docs/infra_ansible.md)
