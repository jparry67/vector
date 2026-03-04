import time
import schedule
from logger import get_logger
from vector import Vector

logger = get_logger(__name__)

KICKOFF_TIME = "8:30"
WRAPUP_TIME = "16:30"

def main():
    vector = Vector()
    schedule.every().day.at(KICKOFF_TIME).do(vector.kickoff_day)
    schedule.every().day.at(WRAPUP_TIME).do(vector.wrapup_day)
    try:
        while True:
            schedule.run_pending()
            time.sleep(10)
    except KeyboardInterrupt:
        logger.info("Shut down via keyboard interrupt.")
    except Exception as e:
        logger.exception(f"Shut down unexpectedly: {e}")
    finally:
        logger.info("Exiting.")
        schedule.clear()

if __name__ == "__main__":
    main()