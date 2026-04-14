# 🛡️ McPatty Performance Coach

An automated, personal AI coaching system that orchestrates health data from multiple providers into a unified dashboard and automated exports.

## 🚀 System Overview

This project provides an end-to-end pipeline for an athlete's performance data:
1.  **Ingestion**: Pulls wellness, training, and nutrition data from **Intervals.icu**, **SparkyFitness**, and **Google Sheets**.
2.  **Storage**: Centralizes all metrics in a local **PostgreSQL** database.
3.  **Visualization**: Exposes a real-time athlete dashboard via a **Telegram Bot**.
4.  **Archival**: Automatically converts workout files (.FIT to .CSV) and maintains a growing master metrics log on **Google Drive**.

## 📖 Sophisticated Documentation

Follow these guides to understand and manage your coaching system:

*   **[Core Architecture](docs/architecture.md)**: Deep dive into the data flow, database schema, and component interactions.
*   **[API Integrations](docs/integrations.md)**: Technical details on how we connect to Intervals.icu, SparkyFitness, and Google Cloud.
*   **[Deployment & DevOps](docs/deployment.md)**: Guide to using the gated CI/CD pipeline (`deploy.sh`) and Ansible infrastructure.
*   **[Testing Suite](docs/testing.md)**: Details on the unit and integration test models.

## ⚡ Quick Start: Deployment

To update your production or test servers with the latest code and verified configurations:

```bash
# Ensure your vault password file exists if using encrypted secrets
./deploy.sh
```

This script will:
1.  Deploy to your **Test Server**.
2.  Run the **Full Test Suite** on the test environment.
3.  Only proceed to **Production** if all tests pass.

## 🌐 Tailscale Access

The system uses **Tailscale Serve** to securely expose internal services over HTTPS to your private tailnet.

### Access URLs:
*   **SparkyFitness (Test):** [https://healthcoach-test.tail996c5.ts.net](https://healthcoach-test.tail996c5.ts.net)
*   **SparkyFitness (Prod):** [https://healthcoach-prod.tail996c5.ts.net](https://healthcoach-prod.tail996c5.ts.net)
*   **Grafana Dashboards:** Internal port 3000 (accessible via Tailscale IP).

## 🤖 Bot Commands

The Telegram bot (`@YourBotName`) supports the following:
*   `/status`: Verbose 30-day performance dashboard.
*   `/today`: High-resolution snapshot of today's nutrition and training.
*   `/sync`: Force a manual data refresh and Google Drive export.
*   `/historicsync`: Backfill 2 years of data into your master CSV.
*   `/journal <text>`: Log your subjective feel directly into the database.

---
*Maintained by the McPatty Performance Engine.*
