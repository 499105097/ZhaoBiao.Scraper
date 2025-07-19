import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
import time
import os
import atexit
import configparser
import signal
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class ScheduledScraper:
    def __init__(self, config_file='config.ini'):
        from scraper import BidCandidateScraper, BidAnnouncementScraper
        
        # Read configuration file
        self.config = configparser.ConfigParser()
        self.config.read(config_file, encoding='utf-8')
        
        # Read scheduled task settings from config file
        try:
            self.schedule_hour = self.config.getint('Schedule', 'SCHEDULE_HOUR')
            self.schedule_minute = self.config.getint('Schedule', 'SCHEDULE_MINUTE')
            logging.info(f"Loaded schedule settings from config file: {self.schedule_hour:02d}:{self.schedule_minute:02d}")
        except (configparser.NoSectionError, configparser.NoOptionError) as e:
            logging.warning(f"Error reading configuration file: {e}, using default time settings")
            self.schedule_hour = 8
            self.schedule_minute = 0
        
        self.candidate_scraper = BidCandidateScraper()
        self.announcement_scraper = BidAnnouncementScraper()
        self.scheduler = BlockingScheduler()
        
        # Set up scheduled task
        self.scheduler.add_job(
            func=self.run_scraping_task,
            trigger="cron",
            hour=self.schedule_hour,
            minute=self.schedule_minute,
            id='daily_scraping'
        )
        
        # Register cleanup function on exit
        atexit.register(self.shutdown)
        
        # Register signal handlers for proper termination
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle termination signals"""
        logging.info(f"Received signal {signum}, shutting down...")
        self.shutdown()
        sys.exit(0)
    
    def run_scraping_task(self):
        """Execute scraping task"""
        try:
            logging.info("=" * 60)
            logging.info("Scheduled task started")
            logging.info("=" * 60)
            
            # Execute bid candidate scraping
            logging.info("Starting bid candidate information scraping...")
            self.candidate_scraper.scrape_candidates()
            
            # Wait a while
            logging.info("Candidate scraping completed, waiting 5 seconds before starting bid announcement scraping...")
            time.sleep(5)
            
            # Execute bid announcement scraping
            logging.info("Starting bid announcement information scraping...")
            self.announcement_scraper.scrape_announcements()
            
            logging.info("=" * 60)
            logging.info("Scheduled task completed")
            logging.info("=" * 60)
            
        except Exception as e:
            logging.error(f"Scheduled task execution failed: {e}")
    
    def start(self):
        """Start the scheduler"""
        try:
            logging.info("Starting scheduled task scheduler...")
            logging.info(f"Task will run daily at {self.schedule_hour:02d}:{self.schedule_minute:02d}")
            logging.info("Press Ctrl+C to stop")
            
            # Print special message for Windows users about termination
            if os.name == 'nt':  # Windows
                logging.info("On Windows: If Ctrl+C doesn't work, press Ctrl+Break or close the terminal window")
                
            self.scheduler.start()
            
        except KeyboardInterrupt:
            logging.info("Received stop signal (KeyboardInterrupt), shutting down...")
            self.shutdown()
            sys.exit(0)
        except Exception as e:
            logging.error(f"Scheduler startup failed: {e}")
            sys.exit(1)
    
    def shutdown(self):
        """Shut down the scheduler"""
        try:
            if hasattr(self, 'scheduler') and self.scheduler.running:
                self.scheduler.shutdown(wait=False)  # Don't wait for jobs to complete
                logging.info("Scheduler shut down")
        except Exception as e:
            logging.error(f"Error during shutdown: {e}")

def main():
    """Main function"""
    scheduled_scraper = ScheduledScraper()
    scheduled_scraper.start()

if __name__ == "__main__":
    main()
