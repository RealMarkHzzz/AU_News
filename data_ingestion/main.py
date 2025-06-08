from fastapi import FastAPI, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict
import os

from . import models, database
from .rss_collector import RSSCollector
from .database import engine

# 创建数据表
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="数据采集服务")

# 依赖项：获取数据库会话
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "澳大利亚新闻数据采集服务"}

@app.post("/sources/")
def create_rss_source(name: str, url: str, db: Session = Depends(get_db)):
    """创建新的RSS源"""
    source = models.RSSSource(name=name, url=url)
    db.add(source)
    db.commit()
    db.refresh(source)
    return source

@app.get("/sources/", response_model=List[Dict])
def list_sources(db: Session = Depends(get_db)):
    """获取所有RSS源列表"""
    sources = db.query(models.RSSSource).all()
    return [{"id": s.id, "name": s.name, "url": s.url, "is_active": s.is_active} for s in sources]

@app.post("/trigger-collection/")
def trigger_collection(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """触发RSS数据采集"""
    collector = RSSCollector(db)
    
    # 获取所有活跃的RSS源
    sources = db.query(models.RSSSource).filter(models.RSSSource.is_active == True).all()
    
    if not sources:
        raise HTTPException(status_code=404, detail="没有找到活跃的RSS源")
    
    # 在后台任务中执行采集
    background_tasks.add_task(collector.fetch_all_active_sources)
    
    return {"message": f"已触发 {len(sources)} 个RSS源的数据采集任务"}

@app.get("/articles/")
def list_articles(limit: int = 10, db: Session = Depends(get_db)):
    """获取最新的文章列表"""
    articles = db.query(models.Article).order_by(models.Article.published_at.desc()).limit(limit).all()
    result = []
    for article in articles:
        result.append({
            "id": article.id,
            "title": article.title,
            "source": article.source,
            "published_at": article.published_at,
            "url": article.url,
            "status": article.status
        })
    return result

@app.post("/articles/{article_id}/update")
def update_article(article_id: int, data: Dict, db: Session = Depends(get_db)):
    """更新文章信息"""
    article = db.query(models.Article).filter(models.Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章未找到")
    
    # 更新文章字段
    for key, value in data.items():
        if hasattr(article, key):
            setattr(article, key, value)
    
    db.commit()
    db.refresh(article)
    
    return {"status": "success", "message": f"文章 {article_id} 已更新"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("data_ingestion.main:app", host="127.0.0.1", port=8001, reload=True)