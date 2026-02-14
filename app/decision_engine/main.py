"""
Decision Engine Entry Point.
Currently in 'Maintenance Mode' to bypass AI logic errors.
The system relies on the Telegram /status command for data visibility.
"""
import sys
import os
import logging

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Placeholder function.
    This prevents systemd or cron jobs from failing while the 
    Decision Engine logic is being refactored.
    """
    logger.info("--- Decision Engine Bypass Active ---")
    logger.info("Logic execution is paused.")
    logger.info("Use the Telegram Bot (/status) for Athlete Dashboard.")
    
    # Return 0 to signal 'Success' to systemd/cron so it doesn't restart/alert
    return 0

if __name__ == "__main__":
    sys.exit(main())
