import logging
from sqlalchemy.orm import Session
from data_ingestion.database import SessionLocal as DataSessionLocal, engine as data_engine
from data_ingestion.models import Base as DataBase, Article, RSSSource, Keyword

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("init_data")

# 创建数据表
DataBase.metadata.create_all(bind=data_engine)

def init_rss_sources():
    """初始化一些澳大利亚新闻的RSS源"""
    db = DataSessionLocal()
    
    # 检查是否已存在数据
    if db.query(RSSSource).count() > 0:
        print("已存在RSS源数据，跳过初始化")
        db.close()
        return
    
    # 准备初始数据
    sources = [
        {"name": "ABC News", "url": "https://www.abc.net.au/news/feed/51120/rss.xml"},
        {"name": "Sydney Morning Herald", "url": "https://www.smh.com.au/rss/feed.xml"},
        {"name": "The Australian", "url": "https://www.theaustralian.com.au/feed/"},
        {"name": "SBS News", "url": "https://www.sbs.com.au/news/feed"}
    ]
    
    # 添加到数据库
    for source_data in sources:
        source = RSSSource(**source_data)
        db.add(source)
    
    db.commit()
    print("成功初始化了4个RSS源")
    db.close()

def init_keywords():
    # 创建数据库会话
    db = DataSessionLocal()
    
    try:
        # 推荐的关键词及其权重（全英文版本）
        keywords = [
            {"word": "chinese students", "category": "student", "weight": 3.0}
        ]
        
        # 获取现有关键词
        existing_keywords = {k.word: k for k in db.query(Keyword).all()}
        logger.info(f"当前数据库中有{len(existing_keywords)}个关键词")
        
        # 添加新关键词（只添加不存在的）
        added_count = 0
        for kw in keywords:
            # 检查关键词是否已存在
            if kw["word"] not in existing_keywords:
                keyword = Keyword(word=kw["word"], category=kw["category"], weight=kw["weight"])
                db.add(keyword)
                added_count += 1
        
        # 提交事务
        if added_count > 0:
            db.commit()
            logger.info(f"成功添加{added_count}个新关键词")
        else:
            logger.info("没有需要添加的新关键词")
        
        return {"status": "success", "added": added_count, "existing": len(existing_keywords)}
    
    except Exception as e:
        db.rollback()
        logger.error(f"初始化关键词时出错: {str(e)}")
        return {"status": "error", "message": str(e)}
    
    finally:
        db.close()

if __name__ == "__main__":
    # 确保数据表已创建
    DataBase.metadata.create_all(bind=data_engine)
    
    # 初始化RSS源
    init_rss_sources()
    
    # 初始化关键词
    result = init_keywords()
    print(f"初始化关键词结果: {result}")