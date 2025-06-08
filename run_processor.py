from integration.processor import IntegrationProcessor
import logging
import time
import sys

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("processor_runner")

def main():
    """运行集成处理器"""
    processor = IntegrationProcessor()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--daemon":
        # 守护模式
        logger.info("启动处理器守护进程...")
        while True:
            try:
                result = processor.process_pending_articles()
                logger.info(f"处理结果: {result}")
                # 等待10秒后再次处理
                time.sleep(10)
            except KeyboardInterrupt:
                logger.info("收到中断信号，退出...")
                break
            except Exception as e:
                logger.error(f"处理时发生错误: {str(e)}")
                time.sleep(30)  # 错误后等待更长时间
    else:
        # 单次运行模式
        result = processor.process_pending_articles()
        logger.info(f"处理结果: {result}")

if __name__ == "__main__":
    main()