import requests
from bs4 import BeautifulSoup
import csv
import logging
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
import time
import os
import atexit

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class ScheduledScraper:
    def __init__(self):
        from scraper import BidCandidateScraper
        self.scraper = BidCandidateScraper()
        self.scheduler = BlockingScheduler()
        
        # 设置每天早上8点执行任务
        self.scheduler.add_job(
            func=self.run_scraping_task,
            trigger="cron",
            hour=8,
            minute=0,
            id='daily_scraping'
        )
        
        # 注册关闭时的清理函数
        atexit.register(self.shutdown)
    
    def run_scraping_task(self):
        """执行抓取任务"""
        try:
            logging.info("=" * 50)
            logging.info("定时任务开始执行")
            logging.info("=" * 50)
            
            self.scraper.scrape_candidates()
            
            logging.info("=" * 50)
            logging.info("定时任务执行完成")
            logging.info("=" * 50)
            
        except Exception as e:
            logging.error(f"定时任务执行失败: {e}")
    
    def start(self):
        """启动调度器"""
        try:
            logging.info("启动定时任务调度器...")
            logging.info("任务将在每天早上8:00执行")
            logging.info("按 Ctrl+C 停止程序")
            
            # 显示下次执行时间
            jobs = self.scheduler.get_jobs()
            if jobs:
                next_run = jobs[0].next_run_time
                logging.info(f"下次执行时间: {next_run}")
            
            self.scheduler.start()
            
        except KeyboardInterrupt:
            logging.info("接收到停止信号，正在关闭...")
            self.shutdown()
        except Exception as e:
            logging.error(f"调度器启动失败: {e}")
    
    def shutdown(self):
        """关闭调度器"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logging.info("调度器已关闭")

def main():
    """主函数"""
    scheduled_scraper = ScheduledScraper()
    scheduled_scraper.start()

if __name__ == "__main__":
    main()
