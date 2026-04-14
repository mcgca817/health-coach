#!/bin/bash
set -e

# Link the environment file if it exists (mounted from Ansible)
if [ -f "/opt/healthcoach/.env" ]; then
    ln -sf /opt/healthcoach/.env /app/.env
fi

case "$1" in
    bot)
        echo "Starting Telegram Bot..."
        python app/bot/main.py
        ;;
    sync)
        echo "Running Data Sync..."
        python app/sync/main.py
        ;;
    test)
        echo "Running Tests..."
        pytest tests/ -v -s
        ;;
    cron)
        echo "Starting Sync Cron..."
        # Loop to run sync every hour and export daily at 8 PM
        while true; do
            HOUR=$(date +%H)
            echo "--- Triggering Sync: $(date) ---"
            python app/sync/main.py || echo "Sync failed, retrying next hour..."
            
            if [ "$HOUR" -eq 20 ]; then
                echo "--- Triggering Daily Export: $(date) ---"
                python app/sync/daily_export.py || echo "Export failed"
            fi
            
            sleep 3600
        done
        ;;
    *)
        exec "$@"
        ;;
esac
