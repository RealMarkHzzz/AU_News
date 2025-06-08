import os
import logging
import datetime
from fastapi import FastAPI, Request, Depends, HTTPException, Form, Query
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Dict, Optional
import threading
import time

# 导入各个模块
from data_ingestion.database import SessionLocal as DataSessionLocal, engine as data_engine
from data_ingestion.models import Base as DataBase, Article, RSSSource, Keyword
from data_ingestion.rss_collector import RSSCollector
from content_analysis.analyzer import ContentAnalyzer
from local_processor import LocalProcessor

# 创建数据表
DataBase.metadata.create_all(bind=data_engine)

# 创建FastAPI应用
app = FastAPI(title="澳大利亚新闻简报系统")

# 配置静态文件
app.mount("/static", StaticFiles(directory="admin_dashboard/static"), name="static")

# 配置模板
templates = Jinja2Templates(directory="admin_dashboard/templates")

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("admin_dashboard")

# 内存日志缓冲区
log_buffer = []

# 自定义日志处理器
class MemoryLogHandler(logging.Handler):
    def emit(self, record):
        log_entry = self.format(record)
        log_buffer.append(log_entry)
        if len(log_buffer) > 1000:  # 限制日志条数
            log_buffer.pop(0)

# 添加日志处理器
memory_handler = MemoryLogHandler()
memory_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logging.getLogger().addHandler(memory_handler)

# 依赖项：数据库会话
def get_db():
    db = DataSessionLocal()
    try:
        yield db
    finally:
        db.close()

# 后台任务进程
background_processor = None

def background_processing():
    """后台处理循环"""
    logger.info("启动后台处理服务")
    processor = LocalProcessor()
    
    while True:
        try:
            logger.info("执行定时处理...")
            processor.process_pending_articles(limit=20)
            time.sleep(86400)  # 每24小时执行一次
        except Exception as e:
            logger.error(f"后台处理出错: {str(e)}")
            time.sleep(300)  # 出错后等待5分钟再试

# 启动后台处理
def start_background_processor():
    global background_processor
    if background_processor is None or not background_processor.is_alive():
        background_processor = threading.Thread(target=background_processing, daemon=True)
        background_processor.start()

# 路由：首页
@app.get("/", response_class=HTMLResponse)
async def index(request: Request, db: Session = Depends(get_db)):
    # 获取统计数据
    today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    stats = {
        "today_articles": db.query(func.count(Article.id)).filter(Article.created_at >= today).scalar(),
        "active_sources": db.query(func.count(RSSSource.id)).filter(RSSSource.is_active == True).scalar(),
        "pending_articles": db.query(func.count(Article.id)).filter(Article.status == "pending").scalar(),
        "processed_articles": db.query(func.count(Article.id)).filter(Article.status == "processed").scalar()
    }
    
    # 获取最新文章
    articles = db.query(Article).order_by(desc(Article.published_at)).limit(10).all()
    
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "stats": stats,
            "articles": articles
        }
    )

# 路由：新闻列表
@app.get("/news", response_class=HTMLResponse)
async def news_list(
    request: Request,
    db: Session = Depends(get_db),
    page: int = 1,
    search: str = "",
    status: str = "",
    sort_by: str = "date",  # 新增排序参数，可选值: date, relevance
    per_page: int = 20,  # 每页显示数量
):
    # 限制每页显示数量最大为100
    per_page = min(per_page, 100)
    
    # 构建查询
    query = db.query(Article)
    
    # 应用筛选条件
    if search:
        query = query.filter(Article.title.like(f"%{search}%"))
    
    if status:
        query = query.filter(Article.status == status)
    
    # 应用排序
    if sort_by == "relevance":
        query = query.order_by(desc(Article.relevance_score), desc(Article.published_at))
    else:  # 默认按日期排序
        query = query.order_by(desc(Article.published_at))
    
    # 计算分页
    total = query.count()
    total_pages = (total + per_page - 1) // per_page
    
    # 获取当前页数据
    articles = query.offset((page - 1) * per_page).limit(per_page).all()
    
    return templates.TemplateResponse(
        "news.html",
        {
            "request": request,
            "articles": articles,
            "page": page,
            "total_pages": total_pages,
            "search": search,
            "status": status,
            "sort_by": sort_by,
            "per_page": per_page
        }
    )

# 路由：查看单篇文章
@app.get("/news/{article_id}", response_class=HTMLResponse)
async def view_article(request: Request, article_id: int, db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章未找到")
    
    return templates.TemplateResponse(
        "article.html",
        {"request": request, "article": article}
    )

# 路由：重新评估单篇文章
@app.get("/news/{article_id}/reevaluate")
async def reevaluate_single_article(article_id: int, db: Session = Depends(get_db)):
    # 查找指定文章
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章未找到")
    
    # 创建处理器
    processor = LocalProcessor()
    
    # 强制重新初始化分析器以获取最新关键词
    processor.analyzer = None
    analyzer = processor.get_analyzer(db)
    
    # 分析文章
    result = analyzer.analyze_article(article.title, article.content or "")
    
    # 更新文章信息
    old_relevance = article.relevance_score
    old_sentiment = article.sentiment
    article.relevance_score = result["relevance_score"]
    article.sentiment = result["sentiment"]
    
    # 提交更改
    db.commit()
    
    # 记录变化
    logger.info(f"重新评估文章 #{article_id}: {article.title}")
    logger.info(f"相关性得分: {old_relevance:.2f} -> {article.relevance_score:.2f}")
    logger.info(f"情感倾向: {old_sentiment:.2f} -> {article.sentiment:.2f}")
    
    return RedirectResponse(f"/news/{article_id}", status_code=303)

# 路由：RSS源管理
@app.get("/sources", response_class=HTMLResponse)
async def sources_list(request: Request, db: Session = Depends(get_db)):
    sources = db.query(RSSSource).order_by(RSSSource.id).all()
    
    # 检测每个源的健康状况
    for source in sources:
        # 如果错误计数大于3且最近一次抓取失败 或者 从未成功抓取过
        if (source.error_count > 3) or (source.last_fetched is None and source.created_at and (datetime.datetime.now() - source.created_at).days > 1):
            source.health_status = "unhealthy"
        # 如果错误计数不为0但小于等于3
        elif source.error_count > 0:
            source.health_status = "warning"
        else:
            source.health_status = "healthy"
    
    return templates.TemplateResponse(
        "sources.html",
        {"request": request, "sources": sources}
    )

# 路由：添加RSS源
@app.post("/sources/add")
async def add_source(name: str = Form(...), url: str = Form(...), db: Session = Depends(get_db)):
    source = RSSSource(name=name, url=url)
    db.add(source)
    db.commit()
    
    logger.info(f"添加了新的RSS源: {name} ({url})")
    
    return RedirectResponse("/sources", status_code=303)

# 路由：编辑RSS源表单
@app.get("/sources/{source_id}/edit", response_class=HTMLResponse)
async def edit_source_form(request: Request, source_id: int, db: Session = Depends(get_db)):
    source = db.query(RSSSource).filter(RSSSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="RSS源未找到")
    
    return templates.TemplateResponse(
        "edit_source.html",
        {"request": request, "source": source}
    )

# 路由：更新RSS源
@app.post("/sources/{source_id}/update")
async def update_source(source_id: int, name: str = Form(...), url: str = Form(...), db: Session = Depends(get_db)):
    source = db.query(RSSSource).filter(RSSSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="RSS源未找到")
    
    source.name = name
    source.url = url
    db.commit()
    
    logger.info(f"更新了RSS源 #{source_id}: {name} ({url})")
    
    return RedirectResponse("/sources", status_code=303)

# 路由：切换RSS源状态
@app.get("/sources/{source_id}/toggle")
async def toggle_source(source_id: int, db: Session = Depends(get_db)):
    source = db.query(RSSSource).filter(RSSSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="RSS源未找到")
    
    source.is_active = not source.is_active
    db.commit()
    
    status = "激活" if source.is_active else "停用"
    logger.info(f"{status}了RSS源 #{source_id}: {source.name}")
    
    return RedirectResponse("/sources", status_code=303)

# 路由：删除RSS源
@app.get("/sources/{source_id}/delete")
async def delete_source(source_id: int, db: Session = Depends(get_db)):
    source = db.query(RSSSource).filter(RSSSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="RSS源未找到")
    
    source_name = source.name
    db.delete(source)
    db.commit()
    
    logger.info(f"删除了RSS源 #{source_id}: {source_name}")
    
    return RedirectResponse("/sources", status_code=303)

# 路由：系统日志
@app.get("/logs", response_class=HTMLResponse)
async def view_logs(request: Request):
    return templates.TemplateResponse(
        "logs.html",
        {"request": request, "logs": log_buffer}
    )

# 路由：清除日志
@app.get("/logs/clear")
async def clear_logs():
    log_buffer.clear()
    logger.info("已清除日志")
    
    return RedirectResponse("/logs", status_code=303)

# 路由：关键词管理
@app.get("/keywords", response_class=HTMLResponse)
async def keywords_list(request: Request, db: Session = Depends(get_db)):
    keywords = db.query(Keyword).order_by(Keyword.category, Keyword.word).all()
    categories = db.query(Keyword.category).distinct().all()
    categories = [c[0] for c in categories]
    
    return templates.TemplateResponse(
        "keywords.html",
        {"request": request, "keywords": keywords, "categories": categories}
    )

# 路由：添加关键词
@app.post("/keywords/add")
async def add_keyword(
    word: str = Form(...), 
    category: str = Form(...), 
    weight: float = Form(...), 
    db: Session = Depends(get_db)
):
    # 检查是否已存在相同关键词
    existing = db.query(Keyword).filter(Keyword.word == word).first()
    if existing:
        logger.warning(f"关键词 '{word}' 已存在")
        return RedirectResponse("/keywords", status_code=303)
    
    keyword = Keyword(word=word, category=category, weight=weight)
    db.add(keyword)
    db.commit()
    
    logger.info(f"添加了新的关键词: {word} (权重: {weight})")
    
    return RedirectResponse("/keywords", status_code=303)

# 路由：编辑关键词
@app.get("/keywords/{keyword_id}/edit", response_class=HTMLResponse)
async def edit_keyword_form(request: Request, keyword_id: int, db: Session = Depends(get_db)):
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    if not keyword:
        raise HTTPException(status_code=404, detail="关键词未找到")
    
    categories = db.query(Keyword.category).distinct().all()
    categories = [c[0] for c in categories]
    
    return templates.TemplateResponse(
        "edit_keyword.html",
        {"request": request, "keyword": keyword, "categories": categories}
    )

# 路由：更新关键词
@app.post("/keywords/{keyword_id}/update")
async def update_keyword(
    keyword_id: int, 
    word: str = Form(...), 
    category: str = Form(...), 
    weight: float = Form(...), 
    db: Session = Depends(get_db)
):
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    if not keyword:
        raise HTTPException(status_code=404, detail="关键词未找到")
    
    keyword.word = word
    keyword.category = category
    keyword.weight = weight
    db.commit()
    
    logger.info(f"更新了关键词 #{keyword_id}: {word} (权重: {weight})")
    
    return RedirectResponse("/keywords", status_code=303)

# 路由：删除关键词
@app.get("/keywords/{keyword_id}/delete")
async def delete_keyword(keyword_id: int, db: Session = Depends(get_db)):
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    if not keyword:
        raise HTTPException(status_code=404, detail="关键词未找到")
    
    word = keyword.word
    db.delete(keyword)
    db.commit()
    
    logger.info(f"删除了关键词 #{keyword_id}: {word}")
    
    return RedirectResponse("/keywords", status_code=303)

# 路由：删除关键词分类
@app.get("/keywords/category/{category}/delete")
async def delete_keyword_category(category: str, db: Session = Depends(get_db)):
    # 找出该分类下的所有关键词
    keywords = db.query(Keyword).filter(Keyword.category == category).all()
    
    if not keywords:
        logger.warning(f"未找到分类 '{category}' 下的关键词")
        return RedirectResponse("/keywords", status_code=303)
    
    # 获取关键词数量
    keyword_count = len(keywords)
    
    # 删除该分类下的所有关键词
    db.query(Keyword).filter(Keyword.category == category).delete()
    db.commit()
    
    logger.info(f"删除了分类 '{category}' 下的所有关键词，共 {keyword_count} 个")
    
    return RedirectResponse("/keywords", status_code=303)

# 路由：切换关键词状态
@app.get("/keywords/{keyword_id}/toggle")
async def toggle_keyword(keyword_id: int, db: Session = Depends(get_db)):
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    if not keyword:
        raise HTTPException(status_code=404, detail="关键词未找到")
    
    keyword.is_active = not keyword.is_active
    db.commit()
    
    status = "激活" if keyword.is_active else "停用"
    logger.info(f"{status}了关键词 #{keyword_id}: {keyword.word}")
    
    return RedirectResponse("/keywords", status_code=303)

# 路由：任务控制页面
@app.get("/tasks", response_class=HTMLResponse)
async def tasks_page(request: Request):
    return templates.TemplateResponse(
        "tasks.html",
        {"request": request}
    )

# 路由：重新评估文章相关性和情感倾向
@app.get("/tasks/reevaluate-articles")
async def reevaluate_articles():
    processor = LocalProcessor()
    
    # 启动文章重新评估
    logger.info("手动触发了文章重新评估")
    
    # 在新线程中执行，避免阻塞主线程
    def do_reevaluation():
        result = processor.reevaluate_articles()
        logger.info(f"文章重新评估完成，结果: {result}")
    
    thread = threading.Thread(target=do_reevaluation)
    thread.start()
    
    return RedirectResponse("/tasks", status_code=303)

# 路由：触发数据采集
@app.get("/tasks/trigger-collection")
async def trigger_collection(db: Session = Depends(get_db)):
    collector = RSSCollector(db)
    
    # 获取所有活跃的RSS源
    sources = db.query(RSSSource).filter(RSSSource.is_active == True).all()
    
    if not sources:
        logger.warning("没有找到活跃的RSS源")
        return RedirectResponse("/tasks", status_code=303)
    
    # 启动数据采集
    logger.info(f"手动触发了RSS数据采集，共{len(sources)}个源")
    
    # 在新线程中执行，避免阻塞主线程
    def do_collection():
        results = collector.fetch_all_active_sources()
        logger.info(f"RSS数据采集完成，结果: {results}")
    
    thread = threading.Thread(target=do_collection)
    thread.start()
    
    return RedirectResponse("/tasks", status_code=303)

# 路由：处理待分析文章
@app.get("/tasks/process-articles")
async def process_articles():
    processor = LocalProcessor()
    
    # 启动文章处理
    logger.info("手动触发了文章处理")
    
    # 在新线程中执行，避免阻塞主线程
    def do_processing():
        result = processor.process_pending_articles(limit=100)
        logger.info(f"文章处理完成，结果: {result}")
    
    thread = threading.Thread(target=do_processing)
    thread.start()
    
    return RedirectResponse("/tasks", status_code=303)

# 路由：启动后台处理器
@app.get("/tasks/start-background-processor")
async def start_bg_processor():
    start_background_processor()
    logger.info("已启动后台处理器")
    
    return RedirectResponse("/tasks", status_code=303)

# 创建文章详情模板
@app.on_event("startup")
async def startup_event():
    # 创建article.html模板
    article_template = """
    {% extends "base.html" %}
    
    {% block title %}{{ article.title }} - 澳大利亚新闻简报系统{% endblock %}
    
    {% block content %}
    <div class="card">
        <h2>{{ article.title }}</h2>
        
        <div style="margin-bottom: 1rem; color: #666;">
            <strong>来源：</strong> {{ article.source }} | 
            <strong>发布时间：</strong> {{ article.published_at }} | 
            <strong>状态：</strong> <span class="status-{{ article.status }}">{{ article.status }}</span>
        </div>
        
        <div style="margin-bottom: 1rem;">
            <strong>原文链接：</strong> <a href="{{ article.url }}" target="_blank">{{ article.url }}</a>
        </div>
        
        <div style="margin-bottom: 1rem;">
            <div style="display: flex; gap: 1rem;">
                <div style="flex: 1;">
                    <strong>相关性得分：</strong> {{ "%.2f"|format(article.relevance_score) if article.relevance_score else "未分析" }}
                </div>
                <div style="flex: 1;">
                    <strong>情感倾向：</strong> {{ "%.2f"|format(article.sentiment) if article.sentiment else "未分析" }}
                </div>
            </div>
        </div>
        
        <h3>内容</h3>
        <div class="article-content">
            {{ article.content }}
        </div>
        
        {% if article.summary %}
        <h3>摘要</h3>
        <div class="article-summary">
            {{ article.summary }}
        </div>
        {% endif %}
        
        <div style="margin-top: 1rem;">
            <a href="/news" class="button">返回列表</a>
            {% if article.status == "pending" %}
            <a href="/tasks/process-articles" class="button">分析文章</a>
            {% endif %}
        </div>
    </div>
    {% endblock %}
    """
    
    # 创建任务页面模板
    tasks_template = """
    {% extends "base.html" %}
    
    {% block title %}任务控制 - 澳大利亚新闻简报系统{% endblock %}
    
    {% block content %}
    <div class="card">
        <h2>任务控制</h2>
        
        <div style="display: flex; gap: 1rem; flex-wrap: wrap;">
            <a href="/tasks/trigger-collection" class="button">触发数据采集</a>
            <a href="/tasks/process-articles" class="button">处理待分析文章</a>
            <a href="/tasks/start-background-processor" class="button">启动后台处理器</a>
        </div>
        
        <h3>任务说明</h3>
        <ul>
            <li><strong>触发数据采集</strong> - 从所有活跃的RSS源获取新文章</li>
            <li><strong>处理待分析文章</strong> - 对待处理状态的文章进行内容分析</li>
            <li><strong>启动后台处理器</strong> - 启动自动定期处理文章的后台任务</li>
        </ul>
    </div>
    {% endblock %}
    """
    
    # 创建编辑源模板
    edit_source_template = """
    {% extends "base.html" %}
    
    {% block title %}编辑RSS源 - 澳大利亚新闻简报系统{% endblock %}
    
    {% block content %}
    <div class="card">
        <h2>编辑RSS源</h2>
        
        <form action="/sources/{{ source.id }}/update" method="post">
            <label for="name">名称</label>
            <input type="text" id="name" name="name" value="{{ source.name }}" required>
            
            <label for="url">URL</label>
            <input type="url" id="url" name="url" value="{{ source.url }}" required>
            
            <div>
                <button type="submit">保存</button>
                <a href="/sources" class="button" style="background-color: #7f8c8d;">取消</a>
            </div>
        </form>
    </div>
    {% endblock %}
    """
    
    # 确保目录存在
    os.makedirs("admin_dashboard/templates", exist_ok=True)
    
    # 写入模板文件
    with open("admin_dashboard/templates/article.html", "w", encoding="utf-8") as f:
        f.write(article_template)
    
    with open("admin_dashboard/templates/tasks.html", "w", encoding="utf-8") as f:
        f.write(tasks_template)
    
    with open("admin_dashboard/templates/edit_source.html", "w", encoding="utf-8") as f:
        f.write(edit_source_template)
    
    # 启动后台处理器
    start_background_processor()

# 运行应用程序
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)