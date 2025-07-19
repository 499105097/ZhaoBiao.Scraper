import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.blocking import BlockingScheduler
import time
import os
import sys
import re

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class BidCandidateScraper:
    def __init__(self, target_date=None):
        self.base_url = "https://zb.shudaojt.com"
        self.list_url = "https://zb.shudaojt.com/hxrgs/people.html"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # 设置目标日期，如果没有指定则使用前一天
        if target_date:
            self.target_date = target_date
        else:
            yesterday = datetime.now() - timedelta(days=1)
            self.target_date = yesterday.strftime('%Y-%m-%d')
        
        logging.info(f"目标抓取日期: {self.target_date}")
        
    def get_page_content(self, url, max_retries=3):
        """获取网页内容，带重试机制"""
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                response.encoding = 'utf-8'
                return response.text
            except requests.RequestException as e:
                logging.warning(f"第{attempt + 1}次尝试获取 {url} 失败: {e}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(2)
    
    def get_page_url(self, page_num):
        """根据页码生成URL"""
        if page_num == 1:
            return self.list_url
        else:
            return f"https://zb.shudaojt.com/hxrgs/{page_num}.html"
    
    def is_target_date(self, date_str):
        """检查日期是否为目标日期"""
        if not date_str:
            return False
        try:
            # 标准化日期格式，处理可能的格式变化
            if date_str.startswith('2025-') and len(date_str) >= 10:
                # 只比较日期部分，忽略可能的时间部分
                date_part = date_str[:10]
                return date_part == self.target_date
            return False
        except Exception as e:
            logging.warning(f"日期格式解析错误: {date_str}, 错误: {e}")
            return False
    
    def extract_candidate_links(self, html_content):
        """从列表页面提取候选人详情链接"""
        soup = BeautifulSoup(html_content, 'html.parser')
        links = []
        
        # 查找主要内容区域
        main_section = soup.find('div', {'class': 'zhongbiaoPeople', 'id': 'main'})
        if not main_section:
            logging.error("未找到主要内容区域")
            return links, False
        
        # 提取所有候选人链接
        candidate_items = main_section.find_all('div', class_='list-details-right-single')
        
        target_date_found = False
        should_stop = False  # 是否应该停止分页
        
        for item in candidate_items:
            link_element = item.find('a')
            if link_element and link_element.get('href'):
                href = link_element.get('href')
                title = link_element.get('title', '').strip()
                
                # 提取时间信息
                time_element = item.find('div', class_='single-time')
                date_str = time_element.text.strip() if time_element else ''
                
                logging.debug(f"检查项目: {title[:50]}..., 日期: {date_str}")
                
                # 检查日期
                if self.is_target_date(date_str):
                    target_date_found = True
                    links.append({
                        'href': href,
                        'title': title,
                        'date': date_str
                    })
                    logging.debug(f"✓ 找到目标日期数据: {title[:50]}...")
                elif date_str < self.target_date and date_str.startswith('2025-'):
                    # 如果遇到比目标日期更早的日期，说明应该停止分页
                    should_stop = True
                    logging.debug(f"遇到更早日期: {date_str}，应该停止分页")
                    break
        
        # 继续下一页的条件：还没有遇到更早的日期
        should_continue = not should_stop
        
        logging.info(f"从当前页面提取到 {len(links)} 个目标日期的候选人链接")
        if should_stop:
            logging.info("遇到比目标日期更早的数据，将停止分页")
        
        return links, should_continue
    
    def extract_candidate_details(self, html_content, original_title, original_date):
        """从详情页面提取候选人信息"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 提取标题
        title_element = soup.find('h3', class_='detail-tt')
        title = title_element.text.strip() if title_element else original_title
        
        # 提取发布时间
        info_time = original_date
        time_elements = soup.find_all('span')
        for span in time_elements:
            span_text = span.get_text().strip()
            if span_text.startswith('2025-') and len(span_text) >= 10:
                info_time = span_text[:10]  # 只取日期部分
                break
        
        # 提取候选人信息
        candidates = []
        content_div = soup.find('div', class_='detail-content')
        
        if content_div:
            # 获取所有文本内容，包括表格内容
            all_text = content_div.get_text()
            
            # 同时解析HTML结构中的表格数据
            tables = content_div.find_all('table')
            table_text = ""
            for table in tables:
                table_text += table.get_text() + "\n"
            
            # 合并所有文本
            combined_text = all_text + "\n" + table_text
            lines = combined_text.split('\n')
            
            for line in lines:
                line = line.strip()
                # 跳过空行和太短的行
                if not line or len(line) < 4:
                    continue
                    
                # 扩展的候选人格式匹配
                candidate_patterns = [
                    # 标准格式
                    r'第[一二三四五六七八九十\d]+入围单位\s*[:：]\s*(.+)',
                    r'第[一二三四五六七八九十\d]+中标候选人\s*[:：]\s*(.+)',
                    r'第[一二三四五六七八九十\d]+名\s*[:：]\s*(.+)',
                    r'入围单位\s*[:：]\s*(.+)',
                    r'中标候选人\s*[:：]\s*(.+)',
                    r'成交候选人\s*[:：]\s*(.+)',
                    r'供应商\s*[:：]\s*(.+)',
                    
                    # 扩展格式 - 处理更复杂的表述
                    r'第[一二三四五六七八九十\d]+\s*[:：]\s*(.+)',  # 简化的第X：公司名
                    r'[一二三四五六七八九十\d]+\s*[:：]\s*(.+)',    # 更简化的数字：公司名
                    r'入围.*?[:：]\s*(.+)',                        # 包含"入围"的行
                    r'中标.*?[:：]\s*(.+)',                        # 包含"中标"的行
                    r'成交.*?[:：]\s*(.+)',                        # 包含"成交"的行
                    r'候选人.*?[:：]\s*(.+)',                      # 包含"候选人"的行
                    
                    # 表格中的常见格式
                    r'^\s*([^：:]*有限公司)\s*$',                  # 单独一行的公司名
                    r'^\s*([^：:]*集团[^：:]*)\s*$',               # 单独一行的集团名
                    r'^\s*([^：:]*企业[^：:]*)\s*$',               # 单独一行的企业名
                    r'^\s*([^：:]*股份[^：:]*)\s*$',               # 单独一行的股份公司名
                ]
                
                matched = False
                for pattern in candidate_patterns:
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        candidate_name = match.group(1).strip()
                        # 清理候选人名称
                        cleaned_name = self.clean_candidate_name(candidate_name)
                        if cleaned_name and cleaned_name not in candidates:
                            candidates.append(cleaned_name)
                            logging.debug(f"提取到候选人: {cleaned_name} (来源: {line[:50]}...)")
                        matched = True
                        break
                
                # 如果没有匹配到模式，但行中包含公司关键词，也尝试提取
                if not matched and self.contains_company_keywords(line):
                    cleaned_name = self.clean_candidate_name(line)
                    if cleaned_name and cleaned_name not in candidates:
                        candidates.append(cleaned_name)
                        logging.debug(f"关键词匹配提取到候选人: {cleaned_name}")
        
        return {
            'title': title,
            'candidates': candidates,
            'date': info_time
        }
    
    def contains_company_keywords(self, text):
        """检查文本是否包含公司关键词"""
        company_keywords = ['有限公司', '股份有限公司', '集团有限公司', '建设集团', '投资集团', 
                           '科技有限公司', '工程有限公司', '建筑有限公司', '商贸有限公司',
                           '实业有限公司', '发展有限公司', '贸易有限公司']
        return any(keyword in text for keyword in company_keywords)
    
    def clean_candidate_name(self, name):
        """清理候选人名称，只保留公司名称"""
        if not name:
            return None
            
        # 移除开头的序号和空格
        name = re.sub(r'^[\d一二三四五六七八九十\s\.、\-\(\)（）]+', '', name)
        
        # 移除常见的描述性文字
        unwanted_patterns = [
            r'[（(].*?[）)]',          # 移除括号内容
            r'投标报价.*',             # 秮除投标报价信息
            r'技术得分.*',             # 移除技术得分信息
            r'综合得分.*',             # 秮除综合得分信息
            r'商务得分.*',             # 移除商务得分信息
            r'总得分.*',               # 移除总得分信息
            r'得分.*',                 # 移除得分信息
            r'评分.*',                 # 移除评分信息
            r'分数.*',                 # 秮除分数信息
            r'\d+\.?\d*\s*元',         # 移除价格信息
            r'\d+\.?\d*\s*万元',       # 秮除万元价格
            r'投标价.*',               # 移除投标价信息
            r'报价.*',                 # 移除报价信息
            r'工期.*',                 # 移除工期信息
            r'质量.*',                 # 秼除质量信息
            r'项目经理.*',             # 移除项目经理信息
            r'联合体.*',               # 秠除联合体信息
            r'联系人.*',               # 移除联系人信息
            r'电话.*',                 # 移除电话信息
            r'地址.*',                 # 秠除地址信息
            r'邮编.*',                 # 移除邮编信息
            r'开标时间.*',             # 秮除开标时间
            r'评标委员会.*',           # 秮除评标委员会信息
        ]
        
        for pattern in unwanted_patterns:
            name = re.sub(pattern, '', name, flags=re.IGNORECASE)
        
        # 移除多余的空格和标点
        name = re.sub(r'\s+', ' ', name)  # 多个空格替换为单个空格
        name = re.sub(r'[,，;；、\.\s]+$', '', name)  # 移除末尾的标点符号
        name = name.strip()
        
        # 过滤掉一些明显不是公司名称的内容
        if not name or len(name) < 3:  # 太短的名称
            return None
            
        # 过滤掉纯数字或明显的非公司名称
        if re.match(r'^[\d\s\.\-\(\)（）]+$', name):  # 纯数字或符号
            return None
            
        # 过滤掉明显的非公司内容
        exclude_words = ['无', '未中标', '未入围', '暂无', '空缺', 'N/A', 'n/a', '评标委员会',
                        '开标', '投标', '招标', '公示', '公告', '现对', '进行', '评审',
                        '开标时间', '投标人', '招标人', '采购人', '供应商名称']
        
        if any(word in name for word in exclude_words):
            return None
            
        # 确保是公司名称（包含公司关键词）
        company_keywords = ['公司', '企业', '集团', '厂', '院', '所', '中心', '局', '部', 
                           '司', '社', '会', '站', '店', '行', '银行', '保险', '证券', 
                           '基金', '投资', '科技', '工程', '建设', '发展', '贸易', 
                           '商贸', '实业', '股份', '合作社', '联合体']
        
        # 如果包含公司关键词，或者名称足够长且看起来像公司名，则保留
        if any(keyword in name for keyword in company_keywords):
            return name
        elif len(name) >= 8 and not any(char.isdigit() for char in name):
            # 如果名称较长且不包含数字，可能是公司名
            return name
            
        return None
    
    def scrape_candidates(self):
        """执行完整的抓取流程"""
        try:
            logging.info(f"开始抓取 {self.target_date} 的候选人信息...")
            
            # 准备数据 - 每个项目一条记录
            project_data = {}
            page_num = 1
            total_links_found = 0
            
            # 遍历所有页面，直到没有目标日期的数据
            while True:
                page_url = self.get_page_url(page_num)
                logging.info(f"正在抓取第 {page_num} 页: {page_url}")
                
                try:
                    # 获取列表页面
                    list_content = self.get_page_content(page_url)
                    candidate_links, should_continue = self.extract_candidate_links(list_content)
                    
                    if candidate_links:
                        total_links_found += len(candidate_links)
                        logging.info(f"第 {page_num} 页找到 {len(candidate_links)} 条目标日期的记录")
                        
                        # 遍历每个详情链接
                        for i, link_info in enumerate(candidate_links):
                            try:
                                detail_url = self.base_url + link_info['href']
                                logging.info(f"正在处理第 {page_num} 页第 {i+1}/{len(candidate_links)} 个链接")
                                
                                # 获取详情页面
                                detail_content = self.get_page_content(detail_url)
                                
                                # 提取详情信息
                                details = self.extract_candidate_details(
                                    detail_content, 
                                    link_info['title'], 
                                    link_info['date']
                                )
                                
                                # 按项目标题分组候选人
                                project_title = details['title']
                                if project_title not in project_data:
                                    project_data[project_title] = {
                                        'candidates': [],
                                        'date': details['date'],
                                        'url': detail_url
                                    }
                                
                                # 添加候选人到对应项目
                                if details['candidates']:
                                    project_data[project_title]['candidates'].extend(details['candidates'])
                                else:
                                    if not project_data[project_title]['candidates']:
                                        project_data[project_title]['candidates'].append('未提取到候选人信息')
                                
                                # 避免请求过于频繁
                                time.sleep(1)
                                
                            except Exception as e:
                                logging.error(f"处理链接 {link_info['href']} 时出错: {e}")
                                continue
                    else:
                        logging.info(f"第 {page_num} 页未找到目标日期的数据")
                    
                    # 检查是否应该继续下一页
                    if not should_continue:
                        logging.info(f"已经超过目标日期范围或无更多数据，停止分页抓取")
                        break
                    
                    page_num += 1
                    
                    # 安全检查：避免无限循环
                    if page_num > 50:  # 假设最多检查50页
                        logging.warning("已检查50页，停止抓取以避免无限循环")
                        break
                        
                except Exception as e:
                    logging.error(f"处理第 {page_num} 页时出错: {e}")
                    break
            
            # 保存到Markdown文件
            if project_data:
                self.save_to_markdown(project_data)
                logging.info(f"抓取完成！共处理 {page_num} 页，找到 {total_links_found} 条链接，保存 {len(project_data)} 个项目的信息")
            else:
                logging.warning(f"没有找到 {self.target_date} 的数据")
                
        except Exception as e:
            logging.error(f"抓取过程中发生错误: {e}")
    
    def save_to_markdown(self, project_data):
        """保存数据到Markdown表格文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"bid_candidates_{self.target_date.replace('-', '')}_{timestamp}.md"
        
        with open(filename, 'w', encoding='utf-8') as mdfile:
            # 写入Markdown表格头部
            mdfile.write("# 招标候选人信息\n\n")
            mdfile.write(f"抓取日期：{self.target_date}\n")
            mdfile.write(f"生成时间：{datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}\n\n")
            mdfile.write("| 项目标题 | 候选人 | 发布时间 | 详情链接 |\n")
            mdfile.write("|----------|--------|----------|----------|\n")
            
            # 写入数据行
            for project_title, info in project_data.items():
                # 去重候选人列表
                unique_candidates = list(dict.fromkeys(info['candidates']))
                candidates_str = '; '.join(unique_candidates)
                
                # 处理标题中的特殊字符，避免破坏表格格式
                safe_title = project_title.replace('|', '\\|').replace('\n', ' ').replace('\r', '')
                safe_candidates = candidates_str.replace('|', '\\|').replace('\n', ' ').replace('\r', '')
                
                # 写入表格行
                mdfile.write(f"| {safe_title} | {safe_candidates} | {info['date']} | [查看详情]({info['url']}) |\n")
        
        logging.info(f"数据已保存到Markdown文件: {filename}")


class BidAnnouncementScraper:
    """招标公告抓取器"""
    
    def __init__(self, target_date=None):
        self.base_url = "https://zb.shudaojt.com"
        self.list_url = "https://zb.shudaojt.com/zbgg/zhaobiao.html"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # 设置目标日期，如果没有指定则使用前一天
        if target_date:
            self.target_date = target_date
        else:
            yesterday = datetime.now() - timedelta(days=1)
            self.target_date = yesterday.strftime('%Y-%m-%d')
        
        logging.info(f"招标公告目标抓取日期: {self.target_date}")
    
    def get_page_content(self, url, max_retries=3):
        """获取网页内容，带重试机制"""
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                response.encoding = 'utf-8'
                return response.text
            except requests.RequestException as e:
                logging.warning(f"第{attempt + 1}次尝试获取 {url} 失败: {e}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(2)
    
    def get_page_url(self, page_num):
        """根据页码生成招标公告URL"""
        if page_num == 1:
            return self.list_url
        else:
            return f"https://zb.shudaojt.com/zbgg/{page_num}.html"
    
    def is_target_date(self, date_str):
        """检查日期是否为目标日期"""
        if not date_str:
            return False
        try:
            if date_str.startswith('2025-') and len(date_str) >= 10:
                date_part = date_str[:10]
                return date_part == self.target_date
            return False
        except Exception as e:
            logging.warning(f"日期格式解析错误: {date_str}, 错误: {e}")
            return False
    
    def extract_announcement_links(self, html_content):
        """从列表页面提取招标公告详情链接"""
        soup = BeautifulSoup(html_content, 'html.parser')
        links = []
        
        # 查找主要内容区域 - 招标公告使用不同的class
        main_section = soup.find('div', {'class': 'zhaobiao-content', 'id': 'main'})
        if not main_section:
            logging.error("未找到招标公告主要内容区域")
            return links, False
        
        # 提取所有招标公告链接
        announcement_items = main_section.find_all('div', class_='list-details-right-single')
        
        target_date_found = False
        should_stop = False
        
        for item in announcement_items:
            link_element = item.find('a')
            if link_element and link_element.get('href'):
                href = link_element.get('href')
                title = link_element.get('title', '').strip()
                
                # 提取时间信息
                time_element = item.find('div', class_='single-time')
                date_str = time_element.text.strip() if time_element else ''
                
                logging.debug(f"检查招标公告: {title[:50]}..., 日期: {date_str}")
                
                # 检查日期
                if self.is_target_date(date_str):
                    target_date_found = True
                    links.append({
                        'href': href,
                        'title': title,
                        'date': date_str
                    })
                    logging.debug(f"✓ 找到目标日期招标公告: {title[:50]}...")
                elif date_str < self.target_date and date_str.startswith('2025-'):
                    should_stop = True
                    logging.debug(f"遇到更早日期: {date_str}，停止分页")
                    break
        
        should_continue = not should_stop
        
        logging.info(f"从当前页面提取到 {len(links)} 个目标日期的招标公告链接")
        if should_stop:
            logging.info("遇到比目标日期更早的招标公告数据，将停止分页")
        
        return links, should_continue
    
    def extract_announcement_details(self, html_content, original_title, original_date):
        """从详情页面提取招标公告信息"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 提取标题
        title_element = soup.find('h3', class_='detail-tt')
        title = title_element.text.strip() if title_element else original_title
        
        # 提取发布时间
        info_time = original_date
        time_elements = soup.find_all('span')
        for span in time_elements:
            span_text = span.get_text().strip()
            if span_text.startswith('2025-') and len(span_text) >= 10:
                info_time = span_text[:10]
                break
        
        # 初始化提取结果
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
        
        # 获取详情内容
        content_div = soup.find('div', class_='detail-content')
        if content_div:
            # 获取纯文本内容，保留换行结构
            full_text = content_div.get_text()
            
            # 同时处理HTML结构，获取更准确的信息
            all_elements = content_div.find_all(['p', 'div', 'span', 'td', 'h1', 'h2', 'h3'])
            
            # 构建文本块列表，保持结构信息
            text_blocks = []
            
            # 添加完整文本
            text_blocks.append(full_text)
            
            # 添加各个元素的文本
            for element in all_elements:
                element_text = element.get_text().strip()
                if element_text and len(element_text) > 3:
                    text_blocks.append(element_text)
            
            # 处理表格数据
            tables = content_div.find_all('table')
            for table in tables:
                table_text = self.extract_table_info(table)
                if table_text:
                    text_blocks.append(table_text)
            
            # 合并所有文本块进行处理
            all_text = '\n'.join(text_blocks)
            
            # 使用增强的提取规则
            result = self.extract_fields_with_enhanced_rules(all_text, result, title)
        
        return result
    
    def extract_table_info(self, table):
        """从表格中提取结构化信息"""
        table_info = []
        rows = table.find_all('tr')
        
        for row in rows:
            cells = row.find_all(['td', 'th'])
            row_text = []
            for cell in cells:
                cell_text = cell.get_text().strip()
                if cell_text:
                    row_text.append(cell_text)
            if row_text:
                table_info.append(' | '.join(row_text))
        
        return '\n'.join(table_info)
    
    def extract_fields_with_enhanced_rules(self, all_text, result, title):
        """使用增强规则提取各个字段"""
        
        # 分行处理，保持文本结构
        lines = all_text.split('\n')
        
        # 增强的字段提取规则
        enhanced_patterns = {
            'bid_conditions': [
                # 基本招标条件模式
                r'1[\.、\s]*招标条件[：:\s]*(.+?)(?=\n.*?2[\.、\s]|$)',
                r'招标条件[：:\s]*(.+?)(?=\n.*?[2-9][\.、\s]|$)',
                r'(?:本项目|该项目).*?已具备招标条件[，,]*(.+?)(?=现|，|。|$)',
                
                # 从具体描述中提取
                r'(.+?已具备招标条件[^。]*?)(?=现|，|。)',
                r'(.+?进行(?:公开|邀请)?招标)',
                
                # 资金和审批相关
                r'(.+?资金[来源已落实确保]+[^。]*?)(?=现|，|。)',
                r'(.+?审批[^。]*?)(?=现|，|。)',
                
                # 项目背景信息
                r'(.+?工程[项目]*[^。]*已[^。]*?)(?=现|，|。)',
            ],
            
            'tenderer': [
                # 标准招标人格式
                r'招标人[：:\s]*[（(]?[^）)]*[）)]?[：:\s]*([^：:\n\r]+?)(?=\n|地址|联系|电话|邮编|$)',
                r'采购人[：:\s]*[（(]?[^）)]*[）)]?[：:\s]*([^：:\n\r]+?)(?=\n|地址|联系|电话|邮编|$)',
                r'建设单位[：:\s]*[（(]?[^）)]*[）)]?[：:\s]*([^：:\n\r]+?)(?=\n|地址|联系|电话|邮编|$)',
                r'发包人[：:\s]*[（(]?[^）)]*[）)]?[：:\s]*([^：:\n\r]+?)(?=\n|地址|联系|电话|邮编|$)',
                
                # 从项目描述中提取
                r'现由[^。]*?([^。]*?(?:公司|集团|企业|单位|中心|院|所))[^。]*?作为[^。]*?招标人',
                r'由[^。]*?([^。]*?(?:公司|集团|企业|单位|中心|院|所))[^。]*?(?:招标|采购)',
                
                # 从标题中提取 - 增强版
                r'^([^（(]*?(?:公司|集团|企业|单位|中心|院|所))(?:.*?(?:招标|采购|项目))',
            ],
            
            'contact_person': [
                # 标准联系人格式
                r'联系人[：:\s]*([^：:\n\r电话邮箱地址]+?)(?=\n|电话|邮箱|地址|传真|$)',
                r'项目联系人[：:\s]*([^：:\n\r电话邮箱地址]+?)(?=\n|电话|邮箱|地址|传真|$)',
                r'联系方式[：:\s]*([^：:\n\r\d]+?)(?=\n|电话|邮箱|地址|传真|\d|$)',
                
                # 从详细联系信息中提取
                r'姓名[：:\s]*([^：:\n\r]+?)(?=\n|电话|邮箱|地址|$)',
                r'联\s*系\s*人[：:\s]*([^：:\n\r]+?)(?=\n|电话|邮箱|地址|$)',
                
                # 模糊匹配 - 姓+先生/女士格式
                r'([张王李赵刘陈杨黄周吴徐孙胡朱高林何郭马罗梁宋郑谢韩唐冯于董萧程曹袁邓许傅沈曾彭吕苏卢蒋蔡贾丁魏薛叶阎余潘杜戴夏钟汪田任姜范方石姚谭廖邹熊金陆郝孔白崔康毛邱秦江史顾侯邵孟龙万段漕钱汤尹黎易常武乔贺赖龚文][一-龯]{0,2}(?:先生|女士|经理|总监|主任|部长|科长))',
            ],
            
            'contact_phone': [
                # 标准电话格式
                r'联系电话[：:\s]*([^：:\n\r邮箱地址传真]+?)(?=\n|邮箱|地址|传真|$)',
                r'电话[：:\s]*([^：:\n\r邮箱地址传真]+?)(?=\n|邮箱|地址|传真|$)',
                r'联系方式[：:\s]*([^：:\n\r邮箱地址传真]*\d+[^：:\n\r邮箱地址传真]*)(?=\n|邮箱|地址|传真|$)',
                
                # 直接匹配电话号码格式
                r'(\d{3,4}[-\s]?\d{7,8}(?:[-\s]?\d{1,6})?)',  # 固定电话
                r'(1[3-9]\d{9})',  # 手机号
                r'(400[-\s]?\d{3}[-\s]?\d{4})',  # 400电话
                r'(028[-\s]?\d{8})',  # 成都区号
                
                # 表格中的电话
                r'电\s*话[：:\s]*([^：:\n\r]+?)(?=\n|邮箱|地址|$)',
            ],
            
            'email': [
                # 标准邮箱格式
                r'电子邮件[：:\s]*([^：:\n\r\s]+@[^：:\n\r\s]+)(?=\n|\s|$)',
                r'邮箱[：:\s]*([^：:\n\r\s]+@[^：:\n\r\s]+)(?=\n|\s|$)',
                r'E-?mail[：:\s]*([^：:\n\r\s]+@[^：:\n\r\s]+)(?=\n|\s|$)',
                
                # 直接匹配邮箱格式
                r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                
                # 表格中的邮箱
                r'邮\s*箱[：:\s]*([^：:\n\r\s]+@[^：:\n\r\s]+)',
            ],
            
            'address': [
                # 标准地址格式
                r'地址[：:\s]*([^：:\n\r]+?)(?=\n|邮编|电话|联系|$)',
                r'联系地址[：:\s]*([^：:\n\r]+?)(?=\n|邮编|电话|联系|$)',
                r'项目地址[：:\s]*([^：:\n\r]+?)(?=\n|邮编|电话|联系|$)',
                r'通讯地址[：:\s]*([^：:\n\r]+?)(?=\n|邮编|电话|联系|$)',
                r'办公地址[：:\s]*([^：:\n\r]+?)(?=\n|邮编|电话|联系|$)',
                
                # 表格中的地址
                r'地\s*址[：:\s]*([^：:\n\r]+?)(?=\n|邮编|电话|联系|$)',
                
                # 匹配包含省市的完整地址
                r'(四川省[^：:\n\r]+?)(?=\n|邮编|电话|联系|$)',
                r'(成都市[^：:\n\r]+?)(?=\n|邮编|电话|联系|$)',
                
                # 从招标人后面的地址信息中提取
                r'四川高路信息科技有限公司[^：:\n\r]*地址[：:\s]*([^：:\n\r]+?)(?=\n|邮编|电话|$)',
            ],
            
            'packages': [
                # 标准包件格式
                r'本次招标共划分[^：:\n\r]*?(\d+[^：:\n\r]*?标段[^：:\n\r]*?)(?=，|。|\n|$)',
                r'标段[编]?号[：:\s]*([^：:\n\r]+?)(?=\n|主要|内容|$)',
                r'包件[：:\s]*([^：:\n\r]+?)(?=\n|标段|内容|$)',
                
                # 从表格中提取包件信息
                r'(LXCLCG\d+[^：:\n\r]*?)(?=\n|$)',
                r'([A-Z]+\d+标段[^：:\n\r]*?)(?=\n|$)',
                
                # 从标题中提取包件信息
                r'(LXCLCG\d+标段)',
                r'(\d+包件[^：:\n\r]*?)(?=招标|采购|公告)',
                r'(\d+标段[^：:\n\r]*?)(?=招标|采购|公告)',
                
                # 投标保证金相关的包件信息
                r'(LXCLCG\d+标段[：:\s]*人民币[^：:\n\r]*?)(?=\n|$)',
            ]
        }
        
        # 逐行匹配，支持多轮匹配以提高准确性
        for line in lines:
            line = line.strip()
            if not line or len(line) < 3:
                continue
            
            for field, field_patterns in enhanced_patterns.items():
                if not result[field] or len(result[field]) < 5:  # 如果字段为空或内容太少，继续尝试
                    for pattern in field_patterns:
                        try:
                            match = re.search(pattern, line, re.IGNORECASE | re.DOTALL)
                            if match:
                                value = match.group(1).strip()
                                cleaned_value = self.clean_extracted_value(value, field)
                                if cleaned_value and len(cleaned_value) > 2:
                                    # 如果新值更好，就替换
                                    if not result[field] or len(cleaned_value) > len(result[field]):
                                        result[field] = cleaned_value
                                        logging.debug(f"提取到{field}: {cleaned_value} (来源: {line[:50]}...)")
                                    break
                        except Exception as e:
                            logging.debug(f"正则匹配错误: {e}")
                            continue
        
        # 特殊处理：如果某些字段仍为空，使用备用提取方法
        if not result['bid_conditions']:
            result['bid_conditions'] = self.extract_bid_conditions_fallback(all_text, title)
        
        if not result['tenderer']:
            result['tenderer'] = self.extract_tenderer_from_title(title)
        
        if not result['packages']:
            result['packages'] = self.extract_packages_from_title(title)
        
        return result
    
    def extract_bid_conditions_fallback(self, content, title):
        """备用的招标条件提取方法"""
        # 从标题中推断项目类型作为招标条件的一部分
        project_types = []
        
        if '采购' in title:
            project_types.append('政府采购项目')
        if '招标' in title:
            project_types.append('公开招标项目')
        if '工程' in title:
            project_types.append('建设工程项目')
        if '服务' in title:
            project_types.append('服务采购项目')
        if '材料' in title or '设备' in title:
            project_types.append('货物采购项目')
        
        # 查找资金来源等信息
        funding_patterns = [
            r'资金来源[:：]\s*([^\n\r]+)',
            r'项目资金[:：]\s*([^\n\r]+)',
            r'资金.*?(?:来源|筹措)[:：]\s*([^\n\r]+)',
            r'已具备招标条件[，,]*([^现，。]+)',
        ]
        
        funding_info = ''
        for pattern in funding_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                funding_info = match.group(1).strip()
                break
        
        # 组合招标条件信息
        conditions = []
        if project_types:
            conditions.extend(project_types)
        if funding_info:
            conditions.append(f'资金来源：{funding_info}')
        
        return '；'.join(conditions) if conditions else '详见招标文件'
    
    def extract_tenderer_from_title(self, title):
        """从标题中提取招标人信息"""
        # 常见的招标人模式
        tenderer_patterns = [
            r'^([^（(]+(?:公司|集团|有限责任公司|股份有限公司|企业|厂|院|所|局|部|中心))',
            r'([^（(]+(?:公司|集团|有限责任公司|股份有限公司|企业)).*?(?:采购|招标)',
            r'([^（(]+(?:公司|集团|有限责任公司|股份有限公司|企业)).*?项目',
        ]
        
        for pattern in tenderer_patterns:
            match = re.search(pattern, title)
            if match:
                tenderer = match.group(1).strip()
                # 清理提取的招标人名称
                tenderer = re.sub(r'[，,。.；;]*$', '', tenderer)
                if len(tenderer) > 3:
                    return tenderer
        
        return ''
    
    def extract_packages_from_title(self, title):
        """从标题中提取包件信息"""
        package_patterns = [
            r'(LXCLCG\d+标段)',
            r'(\d+包件[^招标采购公告]*)',
            r'(\d+标段[^招标采购公告]*)',
            r'([A-Z]{2,}\d+标段)',
        ]
        
        for pattern in package_patterns:
            match = re.search(pattern, title)
            if match:
                return match.group(1).strip()
        
        return ''
    
    def clean_extracted_value(self, value, field_type=''):
        """清理提取的值 - 针对不同字段类型优化"""
        if not value:
            return ''
        
        # 基本清理
        value = re.sub(r'\s+', ' ', value)
        value = value.strip()
        
        # 针对不同字段类型的特殊处理
        if field_type == 'contact_phone':
            # 电话号码清理
            value = re.sub(r'[^\d\-\s\(\)（）+]', '', value)
            value = re.sub(r'\s+', ' ', value).strip()
            # 如果太短，可能不是有效电话号码
            if len(value.replace(' ', '').replace('-', '')) < 7:
                return ''
        
        elif field_type == 'email':
            # 邮箱清理
            email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', value)
            if email_match:
                return email_match.group(0)
            else:
                return ''
        
        elif field_type == 'contact_person':
            # 联系人清理
            value = re.sub(r'[：:,，。.；;]', '', value)
            # 过滤明显不是人名的内容
            if any(word in value for word in ['电话', '邮箱', '地址', '公司', '项目', '招标', '采购']):
                return ''
        
        elif field_type == 'tenderer':
            # 招标人清理
            value = re.sub(r'^[：:\s,，。.；;]*', '', value)
            value = re.sub(r'[：:\s,，。.；;]*$', '', value)
            # 确保包含公司关键词
            if not any(keyword in value for keyword in ['公司', '集团', '企业', '单位', '中心', '院', '所', '局', '部']):
                return ''
        
        elif field_type == 'bid_conditions':
            # 招标条件清理
            value = re.sub(r'^[：:\s,，。.；;]*', '', value)
            # 移除明显的无关信息
            unwanted_in_conditions = ['联系', '电话', '邮箱', '地址', '下载', '登录']
            for unwanted in unwanted_in_conditions:
                if unwanted in value:
                    # 截取到无关信息前的部分
                    parts = value.split(unwanted)
                    if parts[0].strip():
                        value = parts[0].strip()
                    break
        
        # 通用清理
        unwanted_patterns = [
            r'^[，,；;。.\s]*',  # 开头的标点符号
            r'[，,；;。.\s]*$',  # 结尾的标点符号
        ]
        
        for pattern in unwanted_patterns:
            value = re.sub(pattern, '', value)
        
        # 最终检查
        value = value.strip()
        if len(value) < 2:
            return ''
        
        # 过滤明显的无意义文本
        meaningless_texts = [
            '无', '暂无', '待定', '见文件', '详见', 'N/A', 'n/a', 
            '/', '-', '——', '***', '具体要求', '详细信息'
        ]
        
        if value.lower() in [t.lower() for t in meaningless_texts]:
            return ''
        
        return value

    def scrape_announcements(self):
        """执行完整的招标公告抓取流程"""
        try:
            logging.info(f"开始抓取 {self.target_date} 的招标公告信息...")
            
            # 准备数据
            announcement_data = {}
            page_num = 1
            total_links_found = 0
            
            # 遍历所有页面，直到没有目标日期的数据
            while True:
                page_url = self.get_page_url(page_num)
                logging.info(f"正在抓取招标公告第 {page_num} 页: {page_url}")
                
                try:
                    # 获取列表页面
                    list_content = self.get_page_content(page_url)
                    announcement_links, should_continue = self.extract_announcement_links(list_content)
                    
                    if announcement_links:
                        total_links_found += len(announcement_links)
                        logging.info(f"招标公告第 {page_num} 页找到 {len(announcement_links)} 条目标日期的记录")
                        
                        # 遍历每个详情链接
                        for i, link_info in enumerate(announcement_links):
                            try:
                                detail_url = self.base_url + link_info['href']
                                logging.info(f"正在处理招标公告第 {page_num} 页第 {i+1}/{len(announcement_links)} 个链接")
                                
                                # 获取详情页面
                                detail_content = self.get_page_content(detail_url)
                                
                                # 提取详情信息
                                details = self.extract_announcement_details(
                                    detail_content, 
                                    link_info['title'], 
                                    link_info['date']
                                )
                                
                                # 保存招标公告信息
                                announcement_title = details['title']
                                details['url'] = detail_url
                                announcement_data[announcement_title] = details
                                
                                # 避免请求过于频繁
                                time.sleep(1)
                                
                            except Exception as e:
                                logging.error(f"处理招标公告链接 {link_info['href']} 时出错: {e}")
                                continue
                    else:
                        logging.info(f"招标公告第 {page_num} 页未找到目标日期的数据")
                    
                    # 检查是否应该继续下一页
                    if not should_continue:
                        logging.info(f"招标公告已经超过目标日期范围或无更多数据，停止分页抓取")
                        break
                    
                    page_num += 1
                    
                    # 安全检查：避免无限循环
                    if page_num > 50:
                        logging.warning("招标公告已检查50页，停止抓取以避免无限循环")
                        break
                        
                except Exception as e:
                    logging.error(f"处理招标公告第 {page_num} 页时出错: {e}")
                    break
            
            # 保存到Markdown文件
            if announcement_data:
                self.save_announcements_to_markdown(announcement_data)
                logging.info(f"招标公告抓取完成！共处理 {page_num} 页，找到 {total_links_found} 条链接，保存 {len(announcement_data)} 个招标公告的信息")
            else:
                logging.warning(f"没有找到 {self.target_date} 的招标公告数据")
                
        except Exception as e:
            logging.error(f"招标公告抓取过程中发生错误: {e}")
    
    def save_announcements_to_markdown(self, announcement_data):
        """保存招标公告数据到Markdown表格文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"bid_announcements_{self.target_date.replace('-', '')}_{timestamp}.md"
        
        with open(filename, 'w', encoding='utf-8') as mdfile:
            # 写入Markdown表格头部
            mdfile.write("# 招标公告信息\n\n")
            mdfile.write(f"抓取日期：{self.target_date}\n")
            mdfile.write(f"生成时间：{datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}\n\n")
            mdfile.write("| 项目标题 | 招标人 | 联系人 | 联系电话 | 邮箱 | 地址 | 招标条件 | 包件信息 | 发布时间 | 详情链接 |\n")
            mdfile.write("|----------|--------|--------|----------|------|------|----------|----------|----------|----------|\n")
            
            # 写入数据行
            for announcement_title, info in announcement_data.items():
                # 处理字段中的特殊字符，避免破坏表格格式
                safe_title = announcement_title.replace('|', '\\|').replace('\n', ' ').replace('\r', '')
                safe_tenderer = info.get('tenderer', '').replace('|', '\\|').replace('\n', ' ').replace('\r', '')
                safe_contact_person = info.get('contact_person', '').replace('|', '\\|').replace('\n', ' ').replace('\r', '')
                safe_contact_phone = info.get('contact_phone', '').replace('|', '\\|').replace('\n', ' ').replace('\r', '')
                safe_email = info.get('email', '').replace('|', '\\|').replace('\n', ' ').replace('\r', '')
                safe_address = info.get('address', '').replace('|', '\\|').replace('\n', ' ').replace('\r', '')
                safe_bid_conditions = info.get('bid_conditions', '').replace('|', '\\|').replace('\n', ' ').replace('\r', '')
                safe_packages = info.get('packages', '').replace('|', '\\|').replace('\n', ' ').replace('\r', '')
                
                # 写入表格行
                mdfile.write(f"| {safe_title} | {safe_tenderer} | {safe_contact_person} | {safe_contact_phone} | {safe_email} | {safe_address} | {safe_bid_conditions} | {safe_packages} | {info['time']} | [查看详情]({info['url']}) |\n")
        
        logging.info(f"招标公告数据已保存到Markdown文件: {filename}")

def main():
    """主函数 - 依次执行候选人和招标公告抓取"""
    import argparse
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='招标信息抓取工具')
    parser.add_argument('--date', type=str, help='指定抓取日期 (格式: YYYY-MM-DD)')
    parser.add_argument('--type', choices=['candidates', 'announcements', 'both'], 
                       default='both', help='指定抓取类型: candidates(候选人), announcements(招标公告), both(两者)')
    parser.add_argument('date_positional', nargs='?', help='位置参数指定日期 (格式: YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    # 确定目标日期
    target_date = None
    if args.date:
        target_date = args.date
        logging.info(f"使用 --date 指定日期: {target_date}")
    elif args.date_positional:
        target_date = args.date_positional
        logging.info(f"使用位置参数指定日期: {target_date}")
    else:
        logging.info("未指定日期，将使用前一天作为目标日期")
    
    # 根据类型参数决定执行哪些任务
    if args.type in ['candidates', 'both']:
        # 执行候选人信息抓取
        logging.info("=" * 60)
        logging.info("开始执行中标候选人信息抓取任务")
        logging.info("=" * 60)
        
        candidate_scraper = BidCandidateScraper(target_date)
        candidate_scraper.scrape_candidates()
        
        # 如果还要执行招标公告抓取，等待一段时间
        if args.type == 'both':
            logging.info("候选人抓取完成，等待5秒后开始招标公告抓取...")
            time.sleep(5)
    
    if args.type in ['announcements', 'both']:
        # 执行招标公告抓取
        logging.info("=" * 60)
        logging.info("开始执行招标公告信息抓取任务")
        logging.info("=" * 60)
        
        announcement_scraper = BidAnnouncementScraper(target_date)
        announcement_scraper.scrape_announcements()
    
    logging.info("=" * 60)
    logging.info("所有抓取任务完成！")
    logging.info("=" * 60)

if __name__ == "__main__":
    main()
