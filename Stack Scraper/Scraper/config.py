"""
Distributed Stack Overflow Scraper Configuration
Manages settings for distributed scraping across multiple EC2 instances
"""

import os
from typing import Optional
from dataclasses import dataclass
from decouple import config


@dataclass
class RedisConfig:
    """Redis configuration for distributed coordination"""
    host: str = config('REDIS_HOST', default='localhost')
    port: int = config('REDIS_PORT', default=6379, cast=int)
    password: Optional[str] = config('REDIS_PASSWORD', default=None)
    db: int = config('REDIS_DB', default=0, cast=int)
    max_connections: int = config('REDIS_MAX_CONNECTIONS', default=100, cast=int)


@dataclass
class DatabaseConfig:
    """Database configuration for storing scraped data"""
    # MongoDB configuration
    mongo_uri: str = config('MONGO_URI', default='mongodb://localhost:27017/')
    mongo_db: str = config('MONGO_DB', default='stackoverflow_scraper')
    
    # PostgreSQL configuration (alternative)
    postgres_uri: str = config('POSTGRES_URI', default='postgresql://localhost/stackoverflow')


@dataclass
class ScrapingConfig:
    """Scraping behavior configuration"""
    # Threading and concurrency
    max_workers: int = config('MAX_WORKERS', default=5, cast=int)
    questions_per_worker: int = config('QUESTIONS_PER_WORKER', default=100, cast=int)
    
    # Rate limiting
    min_delay: float = config('MIN_DELAY', default=2.0, cast=float)
    max_delay: float = config('MAX_DELAY', default=5.0, cast=float)
    
    # Browser configuration
    headless: bool = config('HEADLESS', default=True, cast=bool)
    timeout: int = config('TIMEOUT', default=30, cast=int)
    
    # Retry configuration
    max_retries: int = config('MAX_RETRIES', default=3, cast=int)
    retry_delay: float = config('RETRY_DELAY', default=10.0, cast=float)


@dataclass
class AWSConfig:
    """AWS EC2 and services configuration"""
    region: str = config('AWS_REGION', default='us-east-1')
    instance_id: str = config('EC2_INSTANCE_ID', default='')
    s3_bucket: str = config('S3_BUCKET', default='stackoverflow-scraper-data')
    
    # Auto-scaling configuration
    min_instances: int = config('MIN_INSTANCES', default=1, cast=int)
    max_instances: int = config('MAX_INSTANCES', default=20, cast=int)


@dataclass
class MonitoringConfig:
    """Monitoring and health check configuration"""
    health_check_port: int = config('HEALTH_CHECK_PORT', default=8080, cast=int)
    metrics_port: int = config('METRICS_PORT', default=9090, cast=int)
    log_level: str = config('LOG_LEVEL', default='INFO')


class Config:
    """Main configuration class"""
    def __init__(self):
        self.redis = RedisConfig()
        self.database = DatabaseConfig()
        self.scraping = ScrapingConfig()
        self.aws = AWSConfig()
        self.monitoring = MonitoringConfig()
        
        # Worker identification
        self.worker_id = config('WORKER_ID', default=f"worker-{os.getpid()}")
        self.instance_type = config('INSTANCE_TYPE', default='local')
        
        # Target configuration
        self.target_total_questions = config('TARGET_QUESTIONS', default=100000, cast=int)
        
        # Duplicate detection
        self.duplicate_check_batch_size = config('DUPLICATE_BATCH_SIZE', default=1000, cast=int)
        
        # Security
        self.shutdown_key = config('SHUTDOWN_KEY', default='secure-key-change-me')


# Global configuration instance
CONFIG = Config()