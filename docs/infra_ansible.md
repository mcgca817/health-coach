# Infrastructure (Ansible)

The `infra/ansible` folder contains playbooks, inventory, and roles to deploy and manage the Health Coach services.

Key items
- `playbooks/deploy.yml` — deploy role `healthcoach` to targeted inventory hosts.
- `playbooks/setup.yml` — initial setup tasks for servers.
- `inventory/hosts.ini` — test and prod inventory groups.
- `roles/healthcoach/` — service templates and tasks used to install and configure the app and timers.

Templates
- `templates/docker-compose.yml.j2` and `.env.j2` are used to generate deployment artifacts.

Example deploy command (from `infra/ansible`):

```bash
ansible-playbook -i inventory/hosts.ini playbooks/deploy.yml --limit test --vault-password-file ~/.vault_pass.txt
```

Notes
- Service templates include systemd unit files for bot and decision services (`healthcoach-bot.service.j2`, `healthcoach-decision.service.j2`).
