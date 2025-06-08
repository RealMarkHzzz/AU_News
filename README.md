# 澳大利亚新闻简报系统 - README.md

## 项目概述

澳大利亚新闻简报系统是一个专为阿德莱德中国留学生和华人社区设计的新闻聚合与分析平台。系统自动从多个澳大利亚新闻源收集文章，并通过自然语言处理技术识别与中国留学生相关的内容，提供便捷的管理界面。

## 项目结构

```
au_news/
├── admin_dashboard/             # Web管理界面
│   ├── static/                  # 静态资源文件(CSS、JS等)
│   └── templates/               # Jinja2模板文件
├── content_analysis/            # 内容分析模块
│   └── analyzer.py              # 文本分析器实现
├── data_ingestion/              # 数据采集模块
│   ├── database.py              # 数据库连接
│   ├── models.py                # 数据模型定义
│   └── rss_collector.py         # RSS数据采集器
├── integration/                 # 集成模块（似乎未使用）
├── tests/                       # 测试目录
├── distribution/                # 分发模块（似乎未使用）
├── ai_summary/                  # AI摘要模块（似乎未使用）
├── main.py                      # 主程序入口和API路由
├── local_processor.py           # 本地处理器
├── init_data.py                 # 初始化数据脚本
├── run_app.py                   # 程序运行脚本
├── run_processor.py             # 处理器运行脚本
├── run_data_ingestion.py        # 数据采集运行脚本
├── run_content_analysis.py      # 内容分析运行脚本
├── test_analyzer.py             # 分析器测试脚本
├── requirements.txt             # 项目依赖
└── au_news_system_design.md     # 系统设计文档
```

## 核心组件思维导图

```
澳大利亚新闻简报系统
├── 数据采集层
│   ├── RSS源管理
│   │   ├── 添加/编辑/删除RSS源
│   │   └── RSS源健康状态监控
│   └── 文章采集
│       └── 定时采集新闻
├── 内容分析层
│   ├── 关键词管理
│   │   ├── 添加/编辑/删除关键词
│   │   ├── 关键词分类管理
│   │   └── 关键词权重设置
│   └── 文本分析
│       ├── 相关性评分计算
│       └── 情感倾向分析
└── 展示层
    ├── 系统管理
    │   ├── 任务控制面板
    │   └── 系统日志查看
    └── 新闻管理
        ├── 新闻列表(支持排序和筛选)
        ├── 单篇文章查看
        └── 文章重新评估
```

## 主要功能模块

### 1. 数据采集模块
- **功能**: 从配置的RSS源自动采集新闻文章
- **核心文件**: `data_ingestion/rss_collector.py`, `data_ingestion/models.py`
- **数据流**: RSS源 → RSS收集器 → 数据库(Article表)

### 2. 内容分析模块
- **功能**: 分析文章内容与中国留学生的相关性及情感倾向
- **核心文件**: `content_analysis/analyzer.py`, `local_processor.py`
- **技术实现**: 关键词匹配 + TextBlob情感分析

### 3. 管理界面模块
- **功能**: 提供Web界面管理系统配置和查看新闻
- **核心文件**: `main.py`, `admin_dashboard/templates/`
- **实现技术**: FastAPI + Jinja2模板

### 4. 数据存储模块
- **功能**: 保存RSS源、文章和关键词数据
- **核心文件**: `data_ingestion/database.py`, `data_ingestion/models.py`
- **使用技术**: SQLAlchemy + SQLite

## 优化建议

### 文件删除/合并建议

1. **可删除的文件/目录**:
   - `integration/` - 未使用的空目录
   - `distribution/` - 未使用的空目录
   - `ai_summary/` - 未使用的空目录
   - `run_content_analysis.py` - 功能已被`local_processor.py`取代
   - `run_data_ingestion.py` - 可合并到`main.py`的任务控制中
   - `run_processor.py` - 可合并到`main.py`的任务控制中

2. **可合并的模块**:
   - 将所有运行脚本(`run_*.py`)合并到一个统一的`cli.py`中，使用命令行参数区分功能
   - 将`local_processor.py`合并到`content_analysis`模块中

### 性能优化建议

1. **数据库优化**:
   - 为高频查询字段添加索引，如`Article.status`，`Article.published_at`
   - 实现文章内容的分页加载，避免一次加载过大内容

2. **后台处理优化**:
   - 将`time.sleep(86400)`定时任务替换为更可靠的调度器，如APScheduler
   - 实现分布式处理能力，支持多实例部署

3. **内存管理**:
   - 日志缓冲区(`log_buffer`)限制为固定大小，防止内存泄漏
   - 在处理大量文章时实现批处理，避免一次性加载过多数据

### 可维护性优化建议

1. **代码结构重构**:
   - 采用明确的分层架构：数据层、服务层、控制器层、视图层
   - 将现有路由按功能模块分组到不同的路由文件中

2. **错误处理增强**:
   - 实现统一的异常处理机制
   - 添加更详细的日志记录，尤其是错误情况

3. **测试覆盖率提升**:
   - 为核心功能编写单元测试
   - 添加集成测试验证完整工作流程

4. **配置管理改进**:
   - 使用环境变量和配置文件替代硬编码参数
   - 实现不同环境(开发、测试、生产)的配置分离

5. **文档完善**:
   - 为所有关键函数添加清晰的文档字符串
   - 提供API接口文档(如通过Swagger UI)

6. **安全性强化**:
   - 添加用户认证和授权系统
   - 实现输入数据验证和清洁

## 最终架构建议

```
au_news/
├── api/                         # API层
│   ├── routes/                  # 按功能分组的路由
│   └── dependencies.py          # 共享依赖项
├── core/                        # 核心功能
│   ├── config.py                # 配置管理
│   ├── security.py              # 安全相关
│   └── scheduler.py             # 任务调度
├── db/                          # 数据库层
│   ├── models.py                # 数据模型
│   ├── database.py              # 数据库连接
│   └── repositories/            # 数据访问层
├── services/                    # 服务层
│   ├── content/                 # 内容分析服务
│   ├── collector/               # 数据采集服务
│   └── processor.py             # 处理服务
├── ui/                          # 用户界面
│   ├── static/                  # 静态资源
│   └── templates/               # UI模板
├── tests/                       # 测试目录
│   ├── unit/                    # 单元测试
│   └── integration/             # 集成测试
├── cli.py                       # 命令行工具
├── main.py                      # 应用程序入口点
└── README.md                    # 项目文档
```
