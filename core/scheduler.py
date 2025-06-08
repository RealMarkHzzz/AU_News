import time
import threading
import asyncio
from typing import Dict, Callable, Any, Optional, Union, List
from datetime import datetime, timedelta

from .logger import get_logger

logger = get_logger("scheduler")

class Task:
    """表示一个计划任务"""
    
    def __init__(
        self,
        name: str,
        func: Callable,
        interval: int,
        args: Optional[List] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        run_immediately: bool = False
    ):
        self.name = name
        self.func = func
        self.interval = interval  # 以秒为单位
        self.args = args or []
        self.kwargs = kwargs or {}
        self.run_immediately = run_immediately
        self.last_run = None if run_immediately else datetime.now()
        self.is_running = False
        self.thread = None
    
    def should_run(self) -> bool:
        """检查任务是否应该运行"""
        if self.last_run is None:
            return True
        
        elapsed = (datetime.now() - self.last_run).total_seconds()
        return elapsed >= self.interval
    
    async def execute_async(self) -> Any:
        """异步执行任务"""
        if asyncio.iscoroutinefunction(self.func):
            return await self.func(*self.args, **self.kwargs)
        else:
            return self.func(*self.args, **self.kwargs)
    
    def execute(self) -> Any:
        """同步执行任务"""
        self.is_running = True
        try:
            result = self.func(*self.args, **self.kwargs)
            self.last_run = datetime.now()
            return result
        except Exception as e:
            logger.error(f"任务 '{self.name}' 执行失败: {e}")
            raise
        finally:
            self.is_running = False


class Scheduler:
    """简单的任务调度器"""
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.running = False
        self.thread = None
        logger.info("初始化调度器")
    
    def add_task(
        self,
        name: str,
        func: Callable,
        interval: int,
        args: Optional[List] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        run_immediately: bool = False
    ) -> Task:
        """添加一个新任务"""
        logger.info(f"添加任务: {name}, 间隔: {interval}秒")
        task = Task(name, func, interval, args, kwargs, run_immediately)
        self.tasks[name] = task
        return task
    
    def remove_task(self, name: str) -> bool:
        """移除任务"""
        if name in self.tasks:
            logger.info(f"移除任务: {name}")
            del self.tasks[name]
            return True
        return False
    
    def get_task(self, name: str) -> Optional[Task]:
        """获取指定任务"""
        return self.tasks.get(name)
    
    def list_tasks(self) -> Dict[str, Task]:
        """列出所有任务"""
        return self.tasks
    
    def start(self) -> None:
        """启动调度器"""
        if self.running:
            logger.warning("调度器已在运行")
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        logger.info("调度器已启动")
    
    def stop(self) -> None:
        """停止调度器"""
        if not self.running:
            logger.warning("调度器未运行")
            return
            
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
        logger.info("调度器已停止")
    
    def _run(self) -> None:
        """运行调度器主循环"""
        while self.running:
            for name, task in self.tasks.items():
                if task.is_running:
                    continue
                    
                if task.should_run():
                    logger.info(f"执行任务: {name}")
                    thread = threading.Thread(
                        target=self._run_task,
                        args=(task,),
                        daemon=True
                    )
                    thread.start()
            
            time.sleep(1)  # 检查间隔
    
    def _run_task(self, task: Task) -> None:
        """在单独的线程中运行任务"""
        try:
            task.execute()
        except Exception as e:
            logger.error(f"任务 '{task.name}' 线程执行失败: {e}")


# 创建全局调度器实例
scheduler = Scheduler() 