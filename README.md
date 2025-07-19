# 招标信息自动抓取工具（数据库版）

> 专业的蜀道投资集团招标信息自动化抓取工具，支持MySQL数据库存储

## 🚀 项目特色

- ✅ **智能抓取**：自动识别和提取中标候选人及招标公告信息
- ✅ **数据库存储**：直接保存至MySQL数据库，支持结构化查询和分析
- ✅ **重复检测**：自动检测并跳过重复数据，避免数据冗余
- ✅ **定时任务**：支持配置自动定时抓取，无需人工干预
- ✅ **灵活配置**：可自定义抓取参数、时间间隔等设置
- ✅ **跨平台**：支持Windows、macOS、Linux多种操作系统
- ✅ **易于使用**：提供批处理文件和命令行两种使用方式

## 📋 功能列表

### 中标候选人信息抓取
- 项目名称和编号
- 招标人信息
- 中标候选人排名和详情
- 公示时间和监督信息
- **自动存储到fa_candidate表**

### 招标公告信息抓取
- 项目标题和招标编号
- 招标人联系方式
- 招标条件和包件信息
- 发布时间和详情链接
- **自动存储到fa_crawler表**

## 🗄️ 数据库配置

程序使用以下MySQL数据库配置：
- 主机：8.156.76.75
- 数据库：bczy
- 用户名：bczzy
- 表结构：
  - `fa_candidate`：中标候选人表
  - `fa_crawler`：招标公告表

## 🛠️ 快速开始

### Windows用户（推荐）

1. **下载解压**：将项目文件解压到任意目录
2. **环境设置**：双击 `setup.bat` 自动安装Python依赖（包括pymysql）
3. **开始使用**：双击 `start.bat` 立即开始抓取并存储到数据库

### 通用方法

```bash
# 1. 安装依赖（包含新增的pymysql数据库驱动）
pip install -r requirements.txt

# 2. 开始抓取（数据直接存储到MySQL数据库）
python scraper.py

# 3. 启动定时任务
python scheduler.py
```

## 📖 使用示例

```bash
# 抓取昨天的所有信息并存储到数据库
python scraper.py

# 抓取指定日期的信息并存储到数据库
python scraper.py --date 2025-07-17

# 只抓取中标候选人信息并存储到fa_candidate表
python scraper.py --type candidates --date 2025-07-17

# 只抓取招标公告信息并存储到fa_crawler表
python scraper.py --type announcements --date 2025-07-17
```

## 📁 项目结构

```
招标抓取工具/
├── scraper.py              # 主程序文件（支持数据库存储）
├── scheduler.py            # 定时任务程序
├── config.ini              # 配置文件
├── requirements.txt        # 依赖包列表（包含pymysql）
├── setup.bat              # Windows环境设置脚本
├── setup.sh               # Linux/macOS环境设置脚本
├── start.bat              # Windows快速启动脚本
├── 数据库信息.md           # 数据库连接和表结构信息
└── README.md              # 项目说明文件
```

## ⚙️ 配置说明

编辑 `config.ini` 文件可自定义程序行为：

```ini
[抓取配置]
REQUEST_DELAY = 1        # 请求间隔时间（秒）
MAX_RETRIES = 3          # 最大重试次数
TIMEOUT = 30             # 请求超时时间

[定时任务配置]
SCHEDULE_HOUR = 8        # 执行时间（小时）
SCHEDULE_MINUTE = 0      # 执行时间（分钟）
```

## 📊 数据库表结构

### fa_candidate（中标候选人表）
- `id`：自增主键
- `title`：项目标题
- `time`：发布时间
- `content`：完整详情页内容
- `candidate`：候选人信息
- `createtime`：创建时间戳

### fa_crawler（招标公告表）
- `id`：自增主键
- `title`：项目标题
- `time`：发布时间
- `condition`：招标条件
- `content`：完整详情页内容
- `tenderer`：招标人
- `address`：地址
- `contacts`：联系人
- `mobile`：联系电话
- `email`：邮箱
- `createtime`：创建时间戳

## 🔧 系统要求

- **Python**：3.8 或更高版本
- **操作系统**：Windows 7+、macOS 10.12+、Linux
- **网络**：稳定的互联网连接
- **数据库**：MySQL数据库访问权限
- **内存**：建议 2GB 以上

## 📝 注意事项

1. **合规使用**：请遵守网站使用条款，合理控制访问频率
2. **数据准确性**：抓取数据仅供参考，重要决策请以官方为准
3. **网络环境**：建议在稳定网络环境下运行
4. **数据库连接**：确保数据库服务器可访问且权限正确
5. **定期维护**：网站结构变化时可能需要更新程序

## 🆘 故障排除

常见问题解决方案：

1. **依赖安装失败**：使用国内镜像源 `pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/`
2. **数据库连接失败**：检查数据库配置信息和网络连接
3. **编码问题**：Windows用户执行 `chcp 65001` 设置UTF-8编码
4. **网络问题**：检查网络连接，确认可访问目标网站
5. **权限问题**：使用管理员权限运行命令提示符

## 📄 更新日志

### v2.0.0 (2025-07-19)
- 🎉 **重大更新**：支持MySQL数据库直接存储
- ✨ 添加DatabaseManager数据库管理类
- ✨ 实现重复数据检测功能
- ✨ 优化数据提取和清理算法
- ✨ 保留完整页面内容到数据库
- ✨ 添加pymysql数据库驱动支持

### v1.0.0 (2025-07-18)
- 🎉 初始版本发布
- ✨ 支持中标候选人信息抓取
- ✨ 支持招标公告信息抓取
- ✨ 支持定时任务执行
- ✨ 生成结构化Markdown报告

---

**版本**：v2.0.0 | **最后更新**：2025-07-19 | **数据库支持**：MySQL
