"""
Distributed Task Queue System for Stack Overflow Scraper
Handles job distribution, duplicate detection, and coordination across instances
"""

import redis
import json
import hashlib
import time
import random
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import logging
from config import CONFIG

logger = logging.getLogger(__name__)


@dataclass
class ScrapingTask:
    """Represents a scraping task"""
    task_id: str
    url: str
    start_page: int
    end_page: int
    worker_id: str
    created_at: datetime
    status: str = 'pending'  # pending, running, completed, failed
    retries: int = 0
    questions_scraped: int = 0


class DistributedTaskQueue:
    """Redis-based distributed task queue for coordinating scraping across instances"""
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=CONFIG.redis.host,
            port=CONFIG.redis.port,
            password=CONFIG.redis.password,
            db=CONFIG.redis.db,
            decode_responses=True,
            max_connections=CONFIG.redis.max_connections
        )
        
        # Queue names
        self.task_queue = "scraping_tasks"
        self.processing_queue = "processing_tasks"
        self.completed_queue = "completed_tasks"
        self.failed_queue = "failed_tasks"
        
        # Duplicate tracking
        self.url_set = "scraped_urls"
        self.question_ids = "question_ids"
        
        # Worker tracking
        self.active_workers = "active_workers"
        self.worker_heartbeat = "worker_heartbeat"
        
        # Statistics
        self.stats_key = "scraping_stats"
    
    def initialize_task_distribution(self, total_pages: int = 10000) -> None:
        """Initialize the task queue with URL ranges for scraping"""
        logger.info(f"Initializing task distribution for {total_pages} pages")
        
        # Clear existing tasks
        self.redis_client.delete(self.task_queue)
        
        # Create page ranges for different SO sections
        so_sections = [
            "https://stackoverflow.com/questions",
            "https://stackoverflow.com/questions/tagged/python",
            "https://stackoverflow.com/questions/tagged/javascript", 
            "https://stackoverflow.com/questions/tagged/java",
            "https://stackoverflow.com/questions/tagged/c%23",
            "https://stackoverflow.com/questions/tagged/html",
            "https://stackoverflow.com/questions/tagged/css",
            "https://stackoverflow.com/questions/tagged/react",
            "https://stackoverflow.com/questions/tagged/node.js",
            "https://stackoverflow.com/questions/tagged/sql"
        ]
        
        pages_per_section = total_pages // len(so_sections)
        pages_per_task = 50  # Each task handles 50 pages
        
        task_counter = 0
        
        for section_url in so_sections:
            for start_page in range(1, pages_per_section, pages_per_task):
                end_page = min(start_page + pages_per_task - 1, pages_per_section)
                
                task = ScrapingTask(
                    task_id=f"task_{task_counter:06d}",
                    url=f"{section_url}?page={start_page}",
                    start_page=start_page,
                    end_page=end_page,
                    worker_id="",
                    created_at=datetime.now()
                )
                
                # Add task to queue
                self.redis_client.lpush(self.task_queue, json.dumps(asdict(task), default=str))
                task_counter += 1
        
        logger.info(f"Created {task_counter} scraping tasks")
        
        # Initialize statistics
        self.redis_client.hset(self.stats_key, mapping={
            "total_tasks": task_counter,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "total_questions": 0,
            "unique_questions": 0,
            "start_time": datetime.now().isoformat()
        })
    
    def get_next_task(self, worker_id: str) -> Optional[ScrapingTask]:
        """Get the next available task for a worker"""
        try:
            # Atomic operation: move task from pending to processing
            task_data = self.redis_client.brpoplpush(
                self.task_queue, 
                self.processing_queue,
                timeout=30
            )
            
            if not task_data:
                return None
            
            task_dict = json.loads(task_data)
            task = ScrapingTask(**task_dict)
            task.worker_id = worker_id
            task.status = 'running'
            
            # Update task in processing queue
            self.redis_client.lrem(self.processing_queue, 1, task_data)
            self.redis_client.lpush(self.processing_queue, json.dumps(asdict(task), default=str))
            
            # Register worker heartbeat
            self.register_worker_heartbeat(worker_id)
            
            logger.info(f"Assigned task {task.task_id} to worker {worker_id}")
            return task
            
        except Exception as e:
            logger.error(f"Error getting next task: {e}")
            return None
    
    def complete_task(self, task: ScrapingTask, questions_scraped: int) -> None:
        """Mark a task as completed"""
        task.status = 'completed'
        task.questions_scraped = questions_scraped
        
        # Remove from processing and add to completed
        task_data = json.dumps(asdict(task), default=str)
        self.redis_client.lrem(self.processing_queue, 1, task_data)
        self.redis_client.lpush(self.completed_queue, task_data)
        
        # Update statistics
        self.redis_client.hincrby(self.stats_key, "completed_tasks", 1)
        self.redis_client.hincrby(self.stats_key, "total_questions", questions_scraped)
        
        logger.info(f"Task {task.task_id} completed with {questions_scraped} questions")
    
    def fail_task(self, task: ScrapingTask, error: str) -> None:
        """Mark a task as failed and potentially retry"""
        task.retries += 1
        
        if task.retries < CONFIG.scraping.max_retries:
            # Retry task - put back in queue
            task.status = 'pending'
            task.worker_id = ""
            self.redis_client.lpush(self.task_queue, json.dumps(asdict(task), default=str))
            logger.info(f"Task {task.task_id} failed, retrying ({task.retries}/{CONFIG.scraping.max_retries})")
        else:
            # Mark as permanently failed
            task.status = 'failed'
            task_data = json.dumps(asdict(task), default=str)
            self.redis_client.lpush(self.failed_queue, task_data)
            self.redis_client.hincrby(self.stats_key, "failed_tasks", 1)
            logger.error(f"Task {task.task_id} permanently failed after {task.retries} retries: {error}")
        
        # Remove from processing queue
        self.redis_client.lrem(self.processing_queue, 1, json.dumps(asdict(task), default=str))
    
    def is_duplicate_url(self, url: str) -> bool:
        """Check if a URL has already been scraped"""
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return self.redis_client.sismember(self.url_set, url_hash)
    
    def add_scraped_url(self, url: str) -> None:
        """Mark a URL as scraped"""
        url_hash = hashlib.md5(url.encode()).hexdigest()
        self.redis_client.sadd(self.url_set, url_hash)
    
    def is_duplicate_question(self, question_id: str) -> bool:
        """Check if a question ID has already been scraped"""
        return self.redis_client.sismember(self.question_ids, question_id)
    
    def add_question_id(self, question_id: str) -> None:
        """Mark a question ID as scraped"""
        self.redis_client.sadd(self.question_ids, question_id)
        self.redis_client.hincrby(self.stats_key, "unique_questions", 1)
    
    def register_worker_heartbeat(self, worker_id: str) -> None:
        """Register that a worker is alive"""
        self.redis_client.hset(self.worker_heartbeat, worker_id, datetime.now().isoformat())
        self.redis_client.sadd(self.active_workers, worker_id)
    
    def cleanup_dead_workers(self) -> None:
        """Clean up tasks from workers that haven't sent heartbeat recently"""
        cutoff_time = datetime.now() - timedelta(minutes=5)
        
        # Get all workers and their last heartbeat
        workers = self.redis_client.hgetall(self.worker_heartbeat)
        
        for worker_id, last_heartbeat in workers.items():
            try:
                heartbeat_time = datetime.fromisoformat(last_heartbeat)
                if heartbeat_time < cutoff_time:
                    logger.warning(f"Worker {worker_id} appears dead, cleaning up tasks")
                    self._reassign_worker_tasks(worker_id)
                    self.redis_client.hdel(self.worker_heartbeat, worker_id)
                    self.redis_client.srem(self.active_workers, worker_id)
            except Exception as e:
                logger.error(f"Error checking worker {worker_id}: {e}")
    
    def _reassign_worker_tasks(self, dead_worker_id: str) -> None:
        """Reassign tasks from a dead worker back to the queue"""
        processing_tasks = self.redis_client.lrange(self.processing_queue, 0, -1)
        
        for task_data in processing_tasks:
            try:
                task_dict = json.loads(task_data)
                if task_dict.get('worker_id') == dead_worker_id:
                    # Remove from processing and add back to pending
                    task_dict['worker_id'] = ""
                    task_dict['status'] = 'pending'
                    
                    self.redis_client.lrem(self.processing_queue, 1, task_data)
                    self.redis_client.lpush(self.task_queue, json.dumps(task_dict))
                    
                    logger.info(f"Reassigned task {task_dict['task_id']} from dead worker {dead_worker_id}")
            except Exception as e:
                logger.error(f"Error reassigning task: {e}")
    
    def get_stats(self) -> Dict:
        """Get current scraping statistics"""
        stats = self.redis_client.hgetall(self.stats_key)
        
        # Add real-time counts
        stats.update({
            "pending_tasks": self.redis_client.llen(self.task_queue),
            "processing_tasks": self.redis_client.llen(self.processing_queue),
            "active_workers": self.redis_client.scard(self.active_workers),
            "scraped_urls": self.redis_client.scard(self.url_set),
            "current_time": datetime.now().isoformat()
        })
        
        return stats
    
    def shutdown_gracefully(self) -> None:
        """Gracefully shutdown the task queue system"""
        logger.info("Shutting down task queue system")
        
        # Move any processing tasks back to pending
        processing_tasks = self.redis_client.lrange(self.processing_queue, 0, -1)
        for task_data in processing_tasks:
            try:
                task_dict = json.loads(task_data)
                task_dict['worker_id'] = ""
                task_dict['status'] = 'pending'
                
                self.redis_client.lrem(self.processing_queue, 1, task_data)
                self.redis_client.lpush(self.task_queue, json.dumps(task_dict))
            except Exception as e:
                logger.error(f"Error during shutdown cleanup: {e}")


# Global task queue instance
task_queue = DistributedTaskQueue()