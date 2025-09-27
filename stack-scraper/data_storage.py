"""
Data Storage System for Distributed Stack Overflow Scraper
Handles persistent storage to MongoDB with duplicate detection and data integrity
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json
import threading
from config import CONFIG

try:
    from pymongo import MongoClient, ASCENDING, DESCENDING
    from pymongo.errors import DuplicateKeyError, ConnectionFailure
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False

logger = logging.getLogger(__name__)


class DataStorage:
    """MongoDB-based data storage with thread safety and duplicate handling"""
    
    def __init__(self):
        self.client = None
        self.db = None
        self.questions_collection = None
        self.metadata_collection = None
        self.stats_collection = None
        self._lock = threading.RLock()
        
        self._connect_to_database()
        self._setup_indexes()
    
    def _connect_to_database(self):
        """Establish connection to MongoDB"""
        try:
            self.client = MongoClient(
                CONFIG.database.mongo_uri,
                serverSelectionTimeoutMS=5000,
                maxPoolSize=50,
                minPoolSize=5
            )
            
            # Test connection
            self.client.server_info()
            
            self.db = self.client[CONFIG.database.mongo_db]
            self.questions_collection = self.db.questions
            self.metadata_collection = self.db.metadata
            self.stats_collection = self.db.statistics
            
            logger.info("Successfully connected to MongoDB")
            
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise
    
    def _setup_indexes(self):
        """Create necessary database indexes for performance and uniqueness"""
        try:
            with self._lock:
                # Question ID index (unique)
                self.questions_collection.create_index(
                    [("question_id", ASCENDING)],
                    unique=True,
                    background=True
                )
                
                # URL index (unique)
                self.questions_collection.create_index(
                    [("link", ASCENDING)],
                    unique=True,
                    background=True
                )
                
                # Compound index for efficient querying
                self.questions_collection.create_index([
                    ("scraped_at", DESCENDING),
                    ("votes", DESCENDING),
                    ("answers", DESCENDING)
                ], background=True)
                
                # Tag index for filtering
                self.questions_collection.create_index(
                    [("tags", ASCENDING)],
                    background=True
                )
                
                # Worker tracking
                self.questions_collection.create_index(
                    [("worker_id", ASCENDING)],
                    background=True
                )
                
                logger.info("Database indexes created successfully")
                
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
    
    def store_question(self, question_data: Dict) -> bool:
        """Store a single question with duplicate checking"""
        try:
            with self._lock:
                # Add storage timestamp
                question_data['stored_at'] = datetime.now()
                
                # Ensure question_id exists
                if not question_data.get('question_id'):
                    logger.warning("Question missing question_id, skipping storage")
                    return False
                
                # Insert with duplicate handling
                try:
                    result = self.questions_collection.insert_one(question_data)
                    logger.debug(f"Stored question {question_data['question_id']}")
                    return True
                    
                except DuplicateKeyError:
                    logger.debug(f"Question {question_data['question_id']} already exists, skipping")
                    return False
                    
        except Exception as e:
            logger.error(f"Error storing question: {e}")
            return False
    
    def store_questions_batch(self, questions_data: List[Dict]) -> int:
        """Store multiple questions in a batch for better performance"""
        if not questions_data:
            return 0
        
        stored_count = 0
        
        try:
            with self._lock:
                # Add storage timestamp to all questions
                current_time = datetime.now()
                for question in questions_data:
                    question['stored_at'] = current_time
                    
                    # Ensure question_id exists
                    if not question.get('question_id'):
                        logger.warning("Question missing question_id in batch, skipping")
                        continue
                
                # Use ordered=False to continue on duplicates
                try:
                    result = self.questions_collection.insert_many(
                        questions_data, 
                        ordered=False
                    )
                    stored_count = len(result.inserted_ids)
                    logger.info(f"Stored batch of {stored_count} questions")
                    
                except Exception as e:
                    # Handle partial success in batch insert
                    if hasattr(e, 'details') and 'writeErrors' in e.details:
                        # Count successful inserts
                        total_errors = len(e.details['writeErrors'])
                        stored_count = len(questions_data) - total_errors
                        logger.info(f"Stored {stored_count} questions from batch (skipped {total_errors} duplicates)")
                    else:
                        logger.error(f"Batch insert error: {e}")
                        # Fallback to individual inserts
                        for question in questions_data:
                            if self.store_question(question):
                                stored_count += 1
                
        except Exception as e:
            logger.error(f"Error in batch storage: {e}")
        
        return stored_count
    
    def get_question_count(self) -> int:
        """Get total number of stored questions"""
        try:
            with self._lock:
                return self.questions_collection.count_documents({})
        except Exception as e:
            logger.error(f"Error getting question count: {e}")
            return 0
    
    def get_unique_question_count(self) -> int:
        """Get count of unique questions by question_id"""
        try:
            with self._lock:
                pipeline = [
                    {"$group": {"_id": "$question_id"}},
                    {"$count": "unique_questions"}
                ]
                result = list(self.questions_collection.aggregate(pipeline))
                return result[0]["unique_questions"] if result else 0
        except Exception as e:
            logger.error(f"Error getting unique question count: {e}")
            return 0
    
    def question_exists(self, question_id: str) -> bool:
        """Check if a question already exists in the database"""
        try:
            with self._lock:
                return self.questions_collection.count_documents(
                    {"question_id": question_id}, limit=1
                ) > 0
        except Exception as e:
            logger.error(f"Error checking question existence: {e}")
            return False
    
    def get_questions_by_tags(self, tags: List[str], limit: int = 100) -> List[Dict]:
        """Retrieve questions filtered by tags"""
        try:
            with self._lock:
                cursor = self.questions_collection.find(
                    {"tags": {"$in": tags}}
                ).sort("votes", DESCENDING).limit(limit)
                
                return list(cursor)
        except Exception as e:
            logger.error(f"Error retrieving questions by tags: {e}")
            return []
    
    def get_top_questions(self, limit: int = 100) -> List[Dict]:
        """Get top questions by vote count"""
        try:
            with self._lock:
                cursor = self.questions_collection.find().sort([
                    ("votes", DESCENDING),
                    ("answers", DESCENDING)
                ]).limit(limit)
                
                return list(cursor)
        except Exception as e:
            logger.error(f"Error retrieving top questions: {e}")
            return []
    
    def get_scraping_statistics(self) -> Dict:
        """Get comprehensive scraping statistics"""
        try:
            with self._lock:
                stats = {}
                
                # Basic counts
                stats['total_questions'] = self.get_question_count()
                stats['unique_questions'] = self.get_unique_question_count()
                
                # Questions by worker
                pipeline = [
                    {"$group": {
                        "_id": "$worker_id",
                        "count": {"$sum": 1}
                    }},
                    {"$sort": {"count": -1}}
                ]
                worker_stats = list(self.questions_collection.aggregate(pipeline))
                stats['questions_by_worker'] = {item['_id']: item['count'] for item in worker_stats}
                
                # Questions by day
                pipeline = [
                    {"$group": {
                        "_id": {
                            "$dateToString": {
                                "format": "%Y-%m-%d",
                                "date": "$scraped_at"
                            }
                        },
                        "count": {"$sum": 1}
                    }},
                    {"$sort": {"_id": -1}},
                    {"$limit": 7}
                ]
                daily_stats = list(self.questions_collection.aggregate(pipeline))
                stats['questions_by_day'] = {item['_id']: item['count'] for item in daily_stats}
                
                # Tag distribution (top 20)
                pipeline = [
                    {"$unwind": "$tags"},
                    {"$group": {
                        "_id": "$tags",
                        "count": {"$sum": 1}
                    }},
                    {"$sort": {"count": -1}},
                    {"$limit": 20}
                ]
                tag_stats = list(self.questions_collection.aggregate(pipeline))
                stats['top_tags'] = {item['_id']: item['count'] for item in tag_stats}
                
                # Vote statistics
                pipeline = [
                    {"$group": {
                        "_id": None,
                        "avg_votes": {"$avg": {"$toInt": "$votes"}},
                        "max_votes": {"$max": {"$toInt": "$votes"}},
                        "total_votes": {"$sum": {"$toInt": "$votes"}}
                    }}
                ]
                vote_stats = list(self.questions_collection.aggregate(pipeline))
                if vote_stats:
                    stats['vote_statistics'] = vote_stats[0]
                
                return stats
                
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
    
    def export_questions_json(self, filename: str = None, limit: int = None) -> str:
        """Export questions to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"exported_questions_{timestamp}.json"
        
        try:
            with self._lock:
                cursor = self.questions_collection.find()
                if limit:
                    cursor = cursor.limit(limit)
                
                questions = []
                for question in cursor:
                    # Convert ObjectId to string
                    question['_id'] = str(question['_id'])
                    questions.append(question)
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(questions, f, indent=2, ensure_ascii=False, default=str)
                
                logger.info(f"Exported {len(questions)} questions to {filename}")
                return filename
                
        except Exception as e:
            logger.error(f"Error exporting questions: {e}")
            return ""
    
    def cleanup_old_data(self, days_old: int = 30) -> int:
        """Remove questions older than specified days"""
        try:
            with self._lock:
                cutoff_date = datetime.now() - timedelta(days=days_old)
                
                result = self.questions_collection.delete_many({
                    "scraped_at": {"$lt": cutoff_date}
                })
                
                logger.info(f"Cleaned up {result.deleted_count} old questions")
                return result.deleted_count
                
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            return 0
    
    def close_connection(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            logger.info("Database connection closed")


class PostgreSQLStorage:
    """Alternative PostgreSQL storage implementation"""
    
    def __init__(self):
        # Import here to make it optional
        try:
            import psycopg2
            from sqlalchemy import create_engine, text as sql_text
            self.engine = create_engine(CONFIG.database.postgres_uri)
            self.sql_text = sql_text
            logger.info("PostgreSQL storage initialized")
        except ImportError:
            logger.warning("PostgreSQL dependencies not installed, using MongoDB only")
            self.engine = None
            self.sql_text = None
    
    def create_tables(self):
        """Create necessary tables for PostgreSQL storage"""
        if not self.engine:
            return
        
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS questions (
            id SERIAL PRIMARY KEY,
            question_id VARCHAR(50) UNIQUE NOT NULL,
            title TEXT NOT NULL,
            link TEXT UNIQUE NOT NULL,
            votes INTEGER DEFAULT 0,
            answers INTEGER DEFAULT 0,
            views INTEGER DEFAULT 0,
            tags TEXT[],
            author VARCHAR(255),
            question_content TEXT,
            question_code TEXT[],
            top_answer_content TEXT,
            top_answer_votes INTEGER DEFAULT 0,
            top_answer_accepted BOOLEAN DEFAULT FALSE,
            scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            stored_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            worker_id VARCHAR(100)
        );
        
        CREATE INDEX IF NOT EXISTS idx_question_id ON questions(question_id);
        CREATE INDEX IF NOT EXISTS idx_scraped_at ON questions(scraped_at);
        CREATE INDEX IF NOT EXISTS idx_votes ON questions(votes DESC);
        CREATE INDEX IF NOT EXISTS idx_tags ON questions USING GIN(tags);
        """
        
        try:
            with self.engine.connect() as conn:
                conn.execute(self.sql_text(create_table_sql))
                conn.commit()
            logger.info("PostgreSQL tables created successfully")
        except Exception as e:
            logger.error(f"Error creating PostgreSQL tables: {e}")


# Global storage instance
data_storage = DataStorage()