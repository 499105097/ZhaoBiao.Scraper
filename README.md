# 招标信息自动抓取工具

> 专业的蜀道投资集团招标信息自动化抓取工具

## 🚀 项目特色

- ✅ **智能抓取**：自动识别和提取中标候选人及招标公告信息
- ✅ **多种格式**：生成结构化的Markdown报告，便于查看和分析
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

### 招标公告信息抓取
- 项目标题和招标编号
- 招标人联系方式
- 招标条件和包件信息
- 发布时间和详情链接

## 🛠️ 快速开始

### Windows用户（推荐）

1. **下载解压**：将项目文件解压到任意目录
2. **环境设置**：双击 `setup.bat` 自动安装Python依赖
3. **开始使用**：双击 `start.bat` 立即开始抓取

### 通用方法

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 开始抓取
python scraper.py

# 3. 启动定时任务
python scheduler.py
```

## 📖 使用示例

```bash
# 抓取昨天的所有信息
python scraper.py

# 抓取指定日期的信息
python scraper.py --date 2025-07-17

# 只抓取中标候选人信息
python scraper.py --type candidates --date 2025-07-17

# 只抓取招标公告信息
python scraper.py --type announcements --date 2025-07-17
```

## 📁 项目结构

```
招标抓取工具/
├── scraper.py              # 主程序文件
├── scheduler.py            # 定时任务程序
├── config.ini              # 配置文件
├── requirements.txt        # 依赖包列表
├── setup.bat              # Windows环境设置脚本
├── setup.sh               # Linux/macOS环境设置脚本
├── start.bat              # Windows快速启动脚本
├── 用户使用手册.md          # 详细使用说明
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

## 📊 输出文件

### 中标候选人信息
- 文件格式：`bid_candidates_YYYYMMDD_YYYYMMDD_HHMMSS.md`
- 包含：项目信息、招标人、候选人排名等

### 招标公告信息
- 文件格式：`bid_announcements_YYYYMMDD_YYYYMMDD_HHMMSS.md`
- 包含：项目标题、联系方式、招标条件等

## 🔧 系统要求

- **Python**：3.8 或更高版本
- **操作系统**：Windows 7+、macOS 10.12+、Linux
- **网络**：稳定的互联网连接
- **内存**：建议 2GB 以上

## 📝 注意事项

1. **合规使用**：请遵守网站使用条款，合理控制访问频率
2. **数据准确性**：抓取数据仅供参考，重要决策请以官方为准
3. **网络环境**：建议在稳定网络环境下运行
4. **定期更新**：网站结构变化时可能需要更新程序

## 🆘 故障排除

常见问题解决方案：

1. **依赖安装失败**：使用国内镜像源 `pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/`
2. **编码问题**：Windows用户执行 `chcp 65001` 设置UTF-8编码
3. **网络问题**：检查网络连接，确认可访问目标网站
4. **权限问题**：使用管理员权限运行命令提示符

详细说明请查看 `用户使用手册.md`

## 📄 更新日志

### v1.0.0 (2025-07-18)
- 🎉 初始版本发布
- ✨ 支持中标候选人信息抓取
- ✨ 支持招标公告信息抓取
- ✨ 支持定时任务执行
- ✨ 生成结构化Markdown报告
- ✨ 提供多种命令行参数选项

---

**版本**：v1.0.0 | **最后更新**：2025-07-18
