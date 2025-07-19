import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.blocking import BlockingScheduler
import time
import os
import sys
import re
import pymysql
import configparser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class DatabaseManager:
    """Database Manager Class"""
    
    def __init__(self, config_file='config.ini'):
        """Initialize database connection"""
        self.config = configparser.ConfigParser()
        self.config.read(config_file, encoding='utf-8')
        
        # Read database connection information from config file
        try:
            self.db_config = {
                'host': self.config.get('Database', 'DB_HOST'),
                'database': self.config.get('Database', 'DB_DATABASE'),
                'user': self.config.get('Database', 'DB_USER'),
                'password': self.config.get('Database', 'DB_PASSWORD'),
                'charset': self.config.get('Database', 'DB_CHARSET'),
                'autocommit': self.config.getboolean('Database', 'DB_AUTOCOMMIT'),
                'port': self.config.getint('Database', 'DB_PORT')
            }
            
            # Read table name configuration
            self.candidate_table = self.config.get('Tables', 'CANDIDATE_TABLE')
            self.crawler_table = self.config.get('Tables', 'CRAWLER_TABLE')
            
            logging.info(f"Database configuration loaded: {self.db_config['host']}:{self.db_config['port']}")
        except (configparser.NoSectionError, configparser.NoOptionError) as e:
            logging.error(f"Config file read error: {e}")
            # Use default configuration as backup
            self.db_config = {
                'host': '8.156.76.75',
                'database': 'bczy',
                'user': 'bczzy',
                'password': 'FG7yAZ6zZRZeKD3S',
                'charset': 'utf8mb4',
                'autocommit': True,
                'port': 3306
            }
            self.candidate_table = 'fa_candidate'
            self.crawler_table = 'fa_crawler'
            logging.warning("Using default database configuration")
        
        self.connection = None
    
    def connect(self):
        """Establish database connection"""
        try:
            self.connection = pymysql.connect(**self.db_config)
            logging.info("Database connection successful")
            return True
        except Exception as e:
            logging.error(f"Database connection failed: {e}")
            return False
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logging.info("Database connection closed")
    
    def insert_candidate(self, title, time_str, content, candidate):
        """Insert bid candidate data to the configured candidate table"""
        try:
            if not self.connection or not self.connection.open:
                self.connect()
            
            cursor = self.connection.cursor()
            
            # Current timestamp
            createtime = int(datetime.now().timestamp())
            
            # Use configured table name
            sql = f"""
            INSERT INTO `{self.candidate_table}` (`title`, `time`, `content`, `candidate`, `createtime`) 
            VALUES (%s, %s, %s, %s, %s)
            """
            
            cursor.execute(sql, (title, time_str, content, candidate, createtime))
            self.connection.commit()
            
            logging.info(f"Successfully inserted candidate data to {self.candidate_table}: {title[:50]}...")
            return True
            
        except Exception as e:
            logging.error(f"Failed to insert candidate data: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
    
    def insert_announcement(self, title, time_str, condition, content, tenderer, address, contacts, mobile, email):
        """Insert bid announcement data to the configured announcement table"""
        try:
            if not self.connection or not self.connection.open:
                self.connect()
            
            cursor = self.connection.cursor()
            
            # Current timestamp
            createtime = int(datetime.now().timestamp())
            
            # Use configured table name
            sql = f"""
            INSERT INTO `{self.crawler_table}` (`title`, `time`, `condition`, `content`, `tenderer`, `address`, `contacts`, `mobile`, `email`, `createtime`) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(sql, (title, time_str, condition, content, tenderer, address, contacts, mobile, email, createtime))
            self.connection.commit()
            
            logging.info(f"Successfully inserted announcement data to {self.crawler_table}: {title[:50]}...")
            return True
            
        except Exception as e:
            logging.error(f"Failed to insert announcement data: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
    
    def check_duplicate(self, table_type, title, time_str):
        """Check if a record with the same title and time already exists"""
        try:
            if not self.connection or not self.connection.open:
                self.connect()
            
            cursor = self.connection.cursor()
            
            # Select table name based on table type
            if table_type == 'candidate':
                table_name = self.candidate_table
            elif table_type == 'crawler':
                table_name = self.crawler_table
            else:
                table_name = table_type  # Compatible with old direct table name passing
            
            sql = f"SELECT COUNT(*) FROM `{table_name}` WHERE `title` = %s AND `time` = %s"
            cursor.execute(sql, (title, time_str))
            count = cursor.fetchone()[0]
            
            return count > 0
            
        except Exception as e:
            logging.error(f"Failed to check for duplicate record: {e}")
            return False
        finally:
            if cursor:
                cursor.close()

class BidCandidateScraper:
    def __init__(self, target_date=None):
        self.base_url = "https://zb.shudaojt.com"
        self.list_url = "https://zb.shudaojt.com/hxrgs/people.html"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Set target date, if not specified use yesterday
        if target_date:
            self.target_date = target_date
        else:
            yesterday = datetime.now() - timedelta(days=1)
            self.target_date = yesterday.strftime('%Y-%m-%d')
        
        # Initialize database manager
        self.db = DatabaseManager()
        
        logging.info(f"Target scraping date: {self.target_date}")
        
    def get_page_content(self, url, max_retries=3):
        """Get webpage content with retry mechanism"""
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                response.encoding = 'utf-8'
                return response.text
            except requests.RequestException as e:
                logging.warning(f"Attempt {attempt + 1} to get {url} failed: {e}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(2)
    
    def get_page_url(self, page_num):
        """Generate URL based on page number"""
        if page_num == 1:
            return self.list_url
        else:
            return f"https://zb.shudaojt.com/hxrgs/{page_num}.html"
    
    def is_target_date(self, date_str):
        """Check if date matches target date"""
        if not date_str:
            return False
        try:
            # Standardize date format, handle possible format variations
            if date_str.startswith('2025-') and len(date_str) >= 10:
                # Only compare date part, ignore possible time part
                date_part = date_str[:10]
                return date_part == self.target_date
            return False
        except Exception as e:
            logging.warning(f"Date format parsing error: {date_str}, error: {e}")
            return False
    
    def extract_candidate_links(self, html_content):
        """Extract candidate detail links from list page"""
        soup = BeautifulSoup(html_content, 'html.parser')
        links = []
        
        # Find main content area
        main_section = soup.find('div', {'class': 'zhongbiaoPeople', 'id': 'main'})
        if not main_section:
            logging.error("Main content area not found")
            return links, False
        
        # Extract all candidate links
        candidate_items = main_section.find_all('div', class_='list-details-right-single')
        
        target_date_found = False
        should_stop = False  # Whether to stop pagination
        
        for item in candidate_items:
            link_element = item.find('a')
            if link_element and link_element.get('href'):
                href = link_element.get('href')
                title = link_element.get('title', '').strip()
                
                # Extract time information
                time_element = item.find('div', class_='single-time')
                date_str = time_element.text.strip() if time_element else ''
                
                logging.debug(f"Checking project: {title[:50]}..., date: {date_str}")
                
                # Check date
                if self.is_target_date(date_str):
                    target_date_found = True
                    links.append({
                        'href': href,
                        'title': title,
                        'date': date_str
                    })
                    logging.debug(f"✓ Found target date data: {title[:50]}...")
                elif date_str < self.target_date and date_str.startswith('2025-'):
                    # If we encounter an earlier date, we should stop pagination
                    should_stop = True
                    logging.debug(f"Encountered earlier date: {date_str}, should stop pagination")
                    break
        
        # Continue to next page condition: haven't encountered earlier dates
        should_continue = not should_stop
        
        logging.info(f"Extracted {len(links)} candidate links with target date from current page")
        if should_stop:
            logging.info("Encountered data earlier than target date, will stop pagination")
        
        return links, should_continue
    
    def extract_candidate_details(self, html_content, original_title, original_date):
        """Extract candidate information from detail page"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract title
        title_element = soup.find('h3', class_='detail-tt')
        title = title_element.text.strip() if title_element else original_title
        
        # Extract publish time
        info_time = original_date
        time_elements = soup.find_all('span')
        for span in time_elements:
            span_text = span.get_text().strip()
            if span_text.startswith('2025-') and len(span_text) >= 10:
                info_time = span_text[:10]  # Only take date part
                break
        
        # Extract candidate information
        candidates = []
        content_div = soup.find('div', class_='detail-content')
        
        if content_div:
            # Get all text content, including table content
            all_text = content_div.get_text()
            
            # Also parse tables in HTML structure
            tables = content_div.find_all('table')
            table_text = ""
            for table in tables:
                table_text += table.get_text() + "\n"
            
            # Combine all text
            combined_text = all_text + "\n" + table_text
            lines = combined_text.split('\n')
            
            for line in lines:
                line = line.strip()
                # Skip empty lines and too short lines
                if not line or len(line) < 4:
                    continue
                    
                # Extended candidate format matching
                candidate_patterns = [
                    # Standard formats
                    r'第[一二三四五六七八九十\d]+入围单位\s*[:：]\s*(.+)',
                    r'第[一二三四五六七八九十\d]+中标候选人\s*[:：]\s*(.+)',
                    r'第[一二三四五六七八九十\d]+名\s*[:：]\s*(.+)',
                    r'入围单位\s*[:：]\s*(.+)',
                    r'中标候选人\s*[:：]\s*(.+)',
                    r'成交候选人\s*[:：]\s*(.+)',
                    r'供应商\s*[:：]\s*(.+)',
                    
                    # Extended formats - handle more complex expressions
                    r'第[一二三四五六七八九十\d]+\s*[:：]\s*(.+)',  # Simplified: No.[X]: Company name
                    r'[一二三四五六七八九十\d]+\s*[:：]\s*(.+)',    # More simplified: Number: Company name
                    r'入围.*?[:：]\s*(.+)',                        # Line containing "shortlisted"
                    r'中标.*?[:：]\s*(.+)',                        # Line containing "winning bid"
                    r'成交.*?[:：]\s*(.+)',                        # Line containing "transaction"
                    r'候选人.*?[:：]\s*(.+)',                      # Line containing "candidate"
                    
                    # Common formats in tables
                    r'^\s*([^：:]*有限公司)\s*$',                  # Company name on its own line
                    r'^\s*([^：:]*集团[^：:]*)\s*$',               # Group name on its own line
                    r'^\s*([^：:]*企业[^：:]*)\s*$',               # Enterprise name on its own line
                    r'^\s*([^：:]*股份[^：:]*)\s*$',               # Corporation name on its own line
                ]
                
                matched = False
                for pattern in candidate_patterns:
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        candidate_name = match.group(1).strip()
                        # Clean candidate name
                        cleaned_name = self.clean_candidate_name(candidate_name)
                        if cleaned_name and cleaned_name not in candidates:
                            candidates.append(cleaned_name)
                            logging.debug(f"Extracted candidate: {cleaned_name} (source: {line[:50]}...)")
                        matched = True
                        break
                
                # If no pattern matched but the line contains company keywords, also try to extract
                if not matched and self.contains_company_keywords(line):
                    cleaned_name = self.clean_candidate_name(line)
                    if cleaned_name and cleaned_name not in candidates:
                        candidates.append(cleaned_name)
                        logging.debug(f"Keyword matched candidate: {cleaned_name}")
        
        return {
            'title': title,
            'candidates': candidates,
            'date': info_time
        }
    
    def contains_company_keywords(self, text):
        """Check if text contains company keywords"""
        company_keywords = ['有限公司', '股份有限公司', '集团有限公司', '建设集团', '投资集团', 
                           '科技有限公司', '工程有限公司', '建筑有限公司', '商贸有限公司',
                           '实业有限公司', '发展有限公司', '贸易有限公司']
        return any(keyword in text for keyword in company_keywords)
    
    def clean_candidate_name(self, name):
        """Clean candidate name, keep only company name"""
        if not name:
            return None
            
        # Remove leading numbers and spaces
        name = re.sub(r'^[\d一二三四五六七八九十\s\.、\-\(\)（）]+', '', name)
        
        # Remove common descriptive text
        unwanted_patterns = [
            r'[（(].*?[）)]',          # Remove content in parentheses
            r'投标报价.*',             # Remove bid price info
            r'技术得分.*',             # Remove technical score info
            r'综合得分.*',             # Remove comprehensive score info
            r'商务得分.*',             # Remove business score info
            r'总得分.*',               # Remove total score info
            r'得分.*',                 # Remove score info
            r'评分.*',                 # Remove rating info
            r'分数.*',                 # Remove score number info
            r'\d+\.?\d*\s*元',         # Remove price info
            r'\d+\.?\d*\s*万元',       # Remove price in 10k yuan
            r'投标价.*',               # Remove bid price info
            r'报价.*',                 # Remove quote info
            r'工期.*',                 # Remove project duration info
            r'质量.*',                 # Remove quality info
            r'项目经理.*',             # Remove project manager info
            r'联合体.*',               # Remove consortium info
            r'联系人.*',               # Remove contact person info
            r'电话.*',                 # Remove phone info
            r'地址.*',                 # Remove address info
            r'邮编.*',                 # Remove postal code info
            r'开标时间.*',             # Remove bid opening time
            r'评标委员会.*',           # Remove bid evaluation committee info
        ]
        
        for pattern in unwanted_patterns:
            name = re.sub(pattern, '', name, flags=re.IGNORECASE)
        
        # Remove extra spaces and punctuation
        name = re.sub(r'\s+', ' ', name)  # Replace multiple spaces with a single space
        name = re.sub(r'[,，;；、\.\s]+$', '', name)  # Remove trailing punctuation
        name = name.strip()
        
        # Filter out some obviously non-company names
        if not name or len(name) < 3:  # Too short name
            return None
            
        # Filter out pure numbers or obvious non-company names
        if re.match(r'^[\d\s\.\-\(\)（）]+$', name):  # Pure numbers or symbols
            return None
            
        # Filter out obviously non-company content
        exclude_words = ['无', '未中标', '未入围', '暂无', '空缺', 'N/A', 'n/a', '评标委员会',
                        '开标', '投标', '招标', '公示', '公告', '现对', '进行', '评审',
                        '开标时间', '投标人', '招标人', '采购人', '供应商名称']
        
        if any(word in name for word in exclude_words):
            return None
            
        # Ensure it's a company name (contains company keywords)
        company_keywords = ['公司', '企业', '集团', '厂', '院', '所', '中心', '局', '部', 
                           '司', '社', '会', '站', '店', '行', '银行', '保险', '证券', 
                           '基金', '投资', '科技', '工程', '建设', '发展', '贸易', 
                           '商贸', '实业', '股份', '合作社', '联合体']
        
        # If it contains company keywords, or name is long enough and looks like a company, keep it
        if any(keyword in name for keyword in company_keywords):
            return name
        elif len(name) >= 8 and not any(char.isdigit() for char in name):
            # If the name is long enough and doesn't contain numbers, it might be a company name
            return name
            
        return None
    
    def scrape_candidates(self):
        """Execute complete scraping process"""
        try:
            logging.info(f"Starting to scrape candidate data for {self.target_date}...")
            
            # Connect to database
            if not self.db.connect():
                logging.error("Cannot connect to database, aborting scraping")
                return
            
            page_num = 1
            total_links_found = 0
            saved_count = 0
            
            # Traverse all pages until no more data for target date is found
            while True:
                page_url = self.get_page_url(page_num)
                logging.info(f"Scraping page {page_num}: {page_url}")
                
                try:
                    # Get list page
                    list_content = self.get_page_content(page_url)
                    candidate_links, should_continue = self.extract_candidate_links(list_content)
                    
                    if candidate_links:
                        total_links_found += len(candidate_links)
                        logging.info(f"Found {len(candidate_links)} records with target date on page {page_num}")
                        
                        # Process each detail link
                        for i, link_info in enumerate(candidate_links):
                            try:
                                detail_url = self.base_url + link_info['href']
                                logging.info(f"Processing link {i+1}/{len(candidate_links)} on page {page_num}")
                                
                                # Get detail page
                                detail_content = self.get_page_content(detail_url)
                                
                                # Extract detail information
                                details = self.extract_candidate_details(
                                    detail_content, 
                                    link_info['title'], 
                                    link_info['date']
                                )
                                
                                # Check for duplicates
                                if not self.db.check_duplicate('candidate', details['title'], details['date']):
                                    # Extract zhongbiaoPeople div content for storage
                                    content_to_save = self.extract_zhongbiao_content(detail_content)
                                    
                                    # Save to database
                                    candidate_str = '; '.join(details['candidates']) if details['candidates'] else 'No candidate information extracted'
                                    
                                    if self.db.insert_candidate(
                                        title=details['title'],
                                        time_str=details['date'],
                                        content=content_to_save,  # Only save zhongbiaoPeople div content
                                        candidate=candidate_str
                                    ):
                                        saved_count += 1
                                        logging.info(f"Saved to database: {details['title'][:50]}...")
                                else:
                                    logging.info(f"Record already exists, skipping: {details['title'][:50]}...")
                                
                                # Avoid requesting too frequently
                                time.sleep(1)
                                
                            except Exception as e:
                                logging.error(f"Error processing link {link_info['href']}: {e}")
                                continue
                    else:
                        logging.info(f"No data found with target date on page {page_num}")
                    
                    # Check if we should continue to next page
                    if not should_continue:
                        logging.info(f"Reached data beyond target date range or no more data, stopping pagination")
                        break
                    
                    page_num += 1
                    
                    # Safety check: avoid infinite loop
                    if page_num > 50:
                        logging.warning("Checked 50 pages, stopping to avoid infinite loop")
                        break
                        
                except Exception as e:
                    logging.error(f"Error processing page {page_num}: {e}")
                    break
            
            # Close database connection
            self.db.close()
            
            logging.info(f"Candidate scraping completed! Processed {page_num} pages, found {total_links_found} links, successfully saved {saved_count} records to database")
                
        except Exception as e:
            logging.error(f"Error during scraping process: {e}")
            if hasattr(self, 'db'):
                self.db.close()
    
    def extract_zhongbiao_content(self, html_content):
        """Extract content from zhongbiaoPeople div tag"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find zhongbiaoPeople div
            zhongbiao_div = soup.find('div', class_='zhongbiaoPeople')
            
            if zhongbiao_div:
                # Return HTML content of the div, including the tag itself
                return str(zhongbiao_div)
            else:
                # If zhongbiaoPeople div is not found, try to find other possible containers
                detail_content = soup.find('div', class_='detail-content')
                if detail_content:
                    logging.warning("zhongbiaoPeople div not found, using detail-content as fallback")
                    return str(detail_content)
                else:
                    logging.warning("Neither zhongbiaoPeople nor detail-content div found, saving empty content")
                    return ""
                    
        except Exception as e:
            logging.error(f"Error extracting zhongbiaoPeople content: {e}")
            return ""

class BidAnnouncementScraper:
    """Bid Announcement Scraper"""
    
    def __init__(self, target_date=None):
        self.base_url = "https://zb.shudaojt.com"
        self.list_url = "https://zb.shudaojt.com/zbgg/zhaobiao.html"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Set target date, if not specified use yesterday
        if target_date:
            self.target_date = target_date
        else:
            yesterday = datetime.now() - timedelta(days=1)
            self.target_date = yesterday.strftime('%Y-%m-%d')
        
        # Initialize database manager
        self.db = DatabaseManager()
        
        logging.info(f"Bid announcement target scraping date: {self.target_date}")
    
    def get_page_content(self, url, max_retries=3):
        """Get webpage content with retry mechanism"""
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                response.encoding = 'utf-8'
                return response.text
            except requests.RequestException as e:
                logging.warning(f"Attempt {attempt + 1} to get {url} failed: {e}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(2)
    
    def get_page_url(self, page_num):
        """Generate bid announcement URL based on page number"""
        if page_num == 1:
            return self.list_url
        else:
            return f"https://zb.shudaojt.com/zbgg/{page_num}.html"
    
    def is_target_date(self, date_str):
        """Check if date matches target date"""
        if not date_str:
            return False
        try:
            if date_str.startswith('2025-') and len(date_str) >= 10:
                date_part = date_str[:10]
                return date_part == self.target_date
            return False
        except Exception as e:
            logging.warning(f"Date format parsing error: {date_str}, error: {e}")
            return False
    
    def extract_announcement_links(self, html_content):
        """Extract bid announcement detail links from list page"""
        soup = BeautifulSoup(html_content, 'html.parser')
        links = []
        
        # Find main content area - bid announcements use different class
        main_section = soup.find('div', {'class': 'zhaobiao-content', 'id': 'main'})
        if not main_section:
            logging.error("Bid announcement main content area not found")
            return links, False
        
        # Extract all bid announcement links
        announcement_items = main_section.find_all('div', class_='list-details-right-single')
        
        target_date_found = False
        should_stop = False
        
        for item in announcement_items:
            link_element = item.find('a')
            if link_element and link_element.get('href'):
                href = link_element.get('href')
                title = link_element.get('title', '').strip()
                
                # Extract time information
                time_element = item.find('div', class_='single-time')
                date_str = time_element.text.strip() if time_element else ''
                
                logging.debug(f"Checking bid announcement: {title[:50]}..., date: {date_str}")
                
                # Check date
                if self.is_target_date(date_str):
                    target_date_found = True
                    links.append({
                        'href': href,
                        'title': title,
                        'date': date_str
                    })
                    logging.debug(f"✓ Found target date bid announcement: {title[:50]}...")
                elif date_str < self.target_date and date_str.startswith('2025-'):
                    should_stop = True
                    logging.debug(f"Encountered earlier date: {date_str}, stopping pagination")
                    break
        
        should_continue = not should_stop
        
        logging.info(f"Extracted {len(links)} bid announcement links with target date from current page")
        if should_stop:
            logging.info("Encountered data earlier than target date, will stop pagination")
        
        return links, should_continue
    
    def extract_announcement_details(self, html_content, original_title, original_date):
        """Extract bid announcement information from detail page"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract title
        title_element = soup.find('h3', class_='detail-tt')
        title = title_element.text.strip() if title_element else original_title
        
        # Extract publish time
        info_time = original_date
        time_elements = soup.find_all('span')
        for span in time_elements:
            span_text = span.get_text().strip()
            if span_text.startswith('2025-') and len(span_text) >= 10:
                info_time = span_text[:10]
                break
        
        # Initialize extraction results
        result = {
            'title': title,
            'time': info_time,
            'bid_conditions': '',
            'tenderer': '',
            'address': '',
            'contact_person': '',
            'contact_phone': '',
            'email': '',
            'packages': ''
        }
        
        # Get detail content
        content_div = soup.find('div', class_='detail-content')
        if content_div:
            full_text = content_div.get_text()
            lines = full_text.split('\n')
            
            # Use regex to extract various fields
            for line in lines:
                line = line.strip()
                if not line or len(line) < 3:
                    continue
                
                # Tenderer (bidding party)
                if not result['tenderer']:
                    patterns = [
                        r'招标人[：:\s]*([^：:\n\r]+?)(?=\n|地址|联系|电话|邮编|$)',
                        r'采购人[：:\s]*([^：:\n\r]+?)(?=\n|地址|联系|电话|邮编|$)',
                        r'建设单位[：:\s]*([^：:\n\r]+?)(?=\n|地址|联系|电话|邮编|$)',
                    ]
                    for pattern in patterns:
                        match = re.search(pattern, line, re.IGNORECASE)
                        if match:
                            result['tenderer'] = match.group(1).strip()
                            break
                
                # Contact person
                if not result['contact_person']:
                    patterns = [
                        r'联系人[：:\s]*([^：:\n\r电话邮箱地址]+?)(?=\n|电话|邮箱|地址|$)',
                        r'项目联系人[：:\s]*([^：:\n\r电话邮箱地址]+?)(?=\n|电话|邮箱|地址|$)',
                    ]
                    for pattern in patterns:
                        match = re.search(pattern, line, re.IGNORECASE)
                        if match:
                            result['contact_person'] = match.group(1).strip()
                            break
                
                # Contact phone
                if not result['contact_phone']:
                    patterns = [
                        r'联系电话[：:\s]*([^：:\n\r邮箱地址传真]+?)(?=\n|邮箱|地址|$)',
                        r'电话[：:\s]*([^：:\n\r邮箱地址传真]+?)(?=\n|邮箱|地址|$)',
                        r'(\d{3,4}[-\s]?\d{7,8}(?:[-\s]?\d{1,6})?)',  # Landline
                        r'(1[3-9]\d{9})',  # Mobile
                    ]
                    for pattern in patterns:
                        match = re.search(pattern, line)
                        if match:
                            result['contact_phone'] = match.group(1).strip()
                            break
                
                # Email
                if not result['email']:
                    pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
                    match = re.search(pattern, line)
                    if match:
                        result['email'] = match.group(1)
                
                # Address
                if not result['address']:
                    patterns = [
                        r'地址[：:\s]*([^：:\n\r]+?)(?=\n|邮编|电话|联系|$)',
                        r'联系地址[：:\s]*([^：:\n\r]+?)(?=\n|邮编|电话|联系|$)',
                    ]
                    for pattern in patterns:
                        match = re.search(pattern, line, re.IGNORECASE)
                        if match:
                            result['address'] = match.group(1).strip()
                            break
                
                # Bid conditions
                if not result['bid_conditions']:
                    patterns = [
                        r'招标条件[：:\s]*(.+?)(?=\n|$)',
                        r'(.+?已具备招标条件[^。]*?)(?=现|，|。)',
                    ]
                    for pattern in patterns:
                        match = re.search(pattern, line, re.IGNORECASE)
                        if match:
                            result['bid_conditions'] = match.group(1).strip()
                            break
        
        # If bid conditions is empty, use default value
        if not result['bid_conditions']:
            result['bid_conditions'] = 'See bidding document for details'
            
        return result
    
    def scrape_announcements(self):
        """Execute complete bid announcement scraping process"""
        try:
            logging.info(f"Starting to scrape bid announcement data for {self.target_date}...")
            
            # Connect to database
            if not self.db.connect():
                logging.error("Cannot connect to database, aborting bid announcement scraping")
                return
            
            page_num = 1
            total_links_found = 0
            saved_count = 0
            
            # Traverse all pages until no more data for target date is found
            while True:
                page_url = self.get_page_url(page_num)
                logging.info(f"Scraping bid announcement page {page_num}: {page_url}")
                
                try:
                    # Get list page
                    list_content = self.get_page_content(page_url)
                    announcement_links, should_continue = self.extract_announcement_links(list_content)
                    
                    if announcement_links:
                        total_links_found += len(announcement_links)
                        logging.info(f"Found {len(announcement_links)} records with target date on bid announcement page {page_num}")
                        
                        # Process each detail link
                        for i, link_info in enumerate(announcement_links):
                            try:
                                detail_url = self.base_url + link_info['href']
                                logging.info(f"Processing bid announcement link {i+1}/{len(announcement_links)} on page {page_num}")
                                
                                # Get detail page
                                detail_content = self.get_page_content(detail_url)
                                
                                # Extract detail information
                                details = self.extract_announcement_details(
                                    detail_content, 
                                    link_info['title'], 
                                    link_info['date']
                                )
                                
                                # Check for duplicates
                                if not self.db.check_duplicate('crawler', details['title'], details['time']):
                                    # Extract specific div content for storage
                                    content_to_save = self.extract_announcement_content(detail_content)
                                    
                                    # Save to database
                                    if self.db.insert_announcement(
                                        title=details['title'],
                                        time_str=details['time'],
                                        condition=details['bid_conditions'],
                                        content=content_to_save,  # Only save specific div content
                                        tenderer=details['tenderer'],
                                        address=details['address'],
                                        contacts=details['contact_person'],
                                        mobile=details['contact_phone'],
                                        email=details['email']
                                    ):
                                        saved_count += 1
                                        logging.info(f"Saved bid announcement to database: {details['title'][:50]}...")
                                else:
                                    logging.info(f"Bid announcement record already exists, skipping: {details['title'][:50]}...")
                                
                                # Avoid requesting too frequently
                                time.sleep(1)
                                
                            except Exception as e:
                                logging.error(f"Error processing bid announcement link {link_info['href']}: {e}")
                                continue
                    else:
                        logging.info(f"No data found with target date on bid announcement page {page_num}")
                    
                    # Check if we should continue to next page
                    if not should_continue:
                        logging.info(f"Reached data beyond target date range or no more data, stopping bid announcement pagination")
                        break
                    
                    page_num += 1
                    
                    # Safety check: avoid infinite loop
                    if page_num > 50:
                        logging.warning("Checked 50 pages of bid announcements, stopping to avoid infinite loop")
                        break
                        
                except Exception as e:
                    logging.error(f"Error processing bid announcement page {page_num}: {e}")
                    break
            
            # Close database connection
            self.db.close()
            
            logging.info(f"Bid announcement scraping completed! Processed {page_num} pages, found {total_links_found} links, successfully saved {saved_count} records to database")
                
        except Exception as e:
            logging.error(f"Error during bid announcement scraping process: {e}")
            if hasattr(self, 'db'):
                self.db.close()
    
    def extract_announcement_content(self, html_content):
        """Extract content from specific div tag for bid announcements"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Prioritize finding zhaobiao-content div
            zhaobiao_div = soup.find('div', class_='zhaobiao-content')
            if zhaobiao_div:
                return str(zhaobiao_div)
            
            # If not found, try to find detail-content div
            detail_content = soup.find('div', class_='detail-content')
            if detail_content:
                logging.warning("zhaobiao-content div not found, using detail-content as fallback")
                return str(detail_content)
            
            # If both not found, try to find main container
            main_div = soup.find('div', id='main')
            if main_div:
                logging.warning("Specific content div not found, using main container as fallback")
                return str(main_div)
            
            # Last resort
            logging.warning("No specific div found, saving empty content")
            return ""
                    
        except Exception as e:
            logging.error(f"Error extracting bid announcement content: {e}")
            return ""

def main():
    """Main function - execute candidate and bid announcement scraping in sequence"""
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Bid information scraping tool')
    parser.add_argument('--date', type=str, help='Specify scraping date (format: YYYY-MM-DD)')
    parser.add_argument('--type', choices=['candidates', 'announcements', 'both'], 
                       default='both', help='Specify scraping type: candidates, announcements, or both')
    parser.add_argument('date_positional', nargs='?', help='Positional argument for date (format: YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    # Determine target date
    target_date = None
    if args.date:
        target_date = args.date
        logging.info(f"Date specified by --date: {target_date}")
    elif args.date_positional:
        target_date = args.date_positional
        logging.info(f"Date specified by positional argument: {target_date}")
    else:
        logging.info("No date specified, using yesterday as target date")
    
    # Execute tasks based on type argument
    if args.type in ['candidates', 'both']:
        # Execute candidate information scraping
        logging.info("=" * 60)
        logging.info("Starting bid candidate information scraping task")
        logging.info("=" * 60)
        
        candidate_scraper = BidCandidateScraper(target_date)
        candidate_scraper.scrape_candidates()
        
        # If also scraping bid announcements, wait before starting
        if args.type == 'both':
            logging.info("Candidate scraping completed, waiting 5 seconds before starting bid announcement scraping...")
            time.sleep(5)
    
    if args.type in ['announcements', 'both']:
        # Execute bid announcement scraping
        logging.info("=" * 60)
        logging.info("Starting bid announcement information scraping task")
        logging.info("=" * 60)
        
        announcement_scraper = BidAnnouncementScraper(target_date)
        announcement_scraper.scrape_announcements()
    
    logging.info("=" * 60)
    logging.info("All scraping tasks completed!")
    logging.info("=" * 60)

if __name__ == "__main__":
    main()
