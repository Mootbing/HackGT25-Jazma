#!/usr/bin/env python3
"""
Main Orchestration Script for Distributed Stack Overflow Scraper
Coordinates the entire distributed scraping operation
"""

import argparse
import logging
import sys
import time
import signal
import threading
from datetime import datetime
from typing import List, Dict

from config import CONFIG
from distributed_queue import task_queue
from distributed_scraper import DistributedScrapingWorker
from data_storage import data_storage
from monitoring import start_monitoring_services, stop_monitoring_services, performance_collector
from ec2_orchestrator import EC2Orchestrator, AutoScaler

logger = logging.getLogger(__name__)


class ScrapingOrchestrator:
    """Main orchestrator for the distributed scraping system"""
    
    def __init__(self):
        self.workers = []
        self.is_running = False
        self.ec2_orchestrator = None
        self.auto_scaler = None
        self.start_time = None
        
        # Signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.shutdown()
    
    def setup_infrastructure(self):
        """Set up the distributed infrastructure"""
        logger.info("Setting up distributed scraping infrastructure...")
        
        try:
            # Initialize task queue with work distribution
            logger.info("Initializing task distribution...")
            task_queue.initialize_task_distribution(total_pages=20000)  # Adjust based on target
            
            # Start monitoring services
            logger.info("Starting monitoring services...")
            start_monitoring_services()
            
            # Set up EC2 orchestration if in cloud mode
            if CONFIG.instance_type != 'local':
                logger.info("Setting up EC2 orchestration...")
                self.ec2_orchestrator = EC2Orchestrator()
                
                # Upload code to S3
                self.ec2_orchestrator.upload_code_to_s3()
                
                # Set up auto-scaling
                self.auto_scaler = AutoScaler(self.ec2_orchestrator)
            
            logger.info("Infrastructure setup completed")
            
        except Exception as e:
            logger.error(f"Error setting up infrastructure: {e}")
            raise
    
    def start_local_workers(self, worker_count: int = None):
        """Start local worker processes"""
        
        worker_count = worker_count or CONFIG.scraping.max_workers
        
        logger.info(f"Starting {worker_count} local workers...")
        
        try:
            for i in range(worker_count):
                worker_id = f"local-worker-{i+1}"
                worker = DistributedScrapingWorker(worker_id)
                
                # Start worker in separate thread
                worker_thread = threading.Thread(
                    target=worker.run_worker,
                    name=f"Worker-{worker_id}",
                    daemon=True
                )
                worker_thread.start()
                
                self.workers.append({
                    'worker': worker,
                    'thread': worker_thread,
                    'worker_id': worker_id
                })
                
                logger.info(f"Started worker: {worker_id}")
                
                # Small delay between worker starts
                time.sleep(2)
            
            logger.info(f"All {worker_count} local workers started successfully")
            
        except Exception as e:
            logger.error(f"Error starting local workers: {e}")
            raise
    
    def deploy_cloud_workers(self, instance_count: int = 5):
        """Deploy workers to EC2 instances"""
        
        if not self.ec2_orchestrator:
            raise RuntimeError("EC2 orchestrator not initialized")
        
        logger.info(f"Deploying {instance_count} EC2 instances...")
        
        try:
            # Launch EC2 instances
            instance_ids = self.ec2_orchestrator.create_scraper_instances(instance_count)
            
            logger.info(f"Deployed EC2 instances: {instance_ids}")
            
            # Start auto-scaling if configured
            if self.auto_scaler:
                self.auto_scaler.current_instances = instance_ids
                self.auto_scaler.start_auto_scaling()
                logger.info("Auto-scaling started")
            
            return instance_ids
            
        except Exception as e:
            logger.error(f"Error deploying cloud workers: {e}")
            raise
    
    def monitor_progress(self):
        """Monitor scraping progress and system health"""
        
        logger.info("Starting progress monitoring...")
        
        self.is_running = True
        self.start_time = datetime.now()
        
        try:
            while self.is_running:
                # Get current statistics
                queue_stats = task_queue.get_stats()
                db_stats = data_storage.get_scraping_statistics()
                
                # Calculate progress
                total_tasks = int(queue_stats.get('total_tasks', 0))
                completed_tasks = int(queue_stats.get('completed_tasks', 0))
                pending_tasks = int(queue_stats.get('pending_tasks', 0))
                failed_tasks = int(queue_stats.get('failed_tasks', 0))
                
                progress_percent = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
                
                # Calculate runtime and ETA
                runtime = datetime.now() - self.start_time
                runtime_minutes = runtime.total_seconds() / 60
                
                # Calculate rates
                if runtime_minutes > 0:
                    tasks_per_minute = completed_tasks / runtime_minutes
                    eta_minutes = pending_tasks / tasks_per_minute if tasks_per_minute > 0 else 0
                else:
                    tasks_per_minute = 0
                    eta_minutes = 0
                
                # Print progress report
                logger.info("=" * 80)
                logger.info(f"SCRAPING PROGRESS REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info("=" * 80)
                logger.info(f"📊 Overall Progress: {completed_tasks}/{total_tasks} tasks ({progress_percent:.1f}%)")
                logger.info(f"⏳ Pending Tasks: {pending_tasks}")
                logger.info(f"❌ Failed Tasks: {failed_tasks}")
                logger.info(f"🕐 Runtime: {runtime_minutes:.1f} minutes")
                logger.info(f"⚡ Rate: {tasks_per_minute:.1f} tasks/minute")
                
                if eta_minutes > 0:
                    eta_hours = eta_minutes / 60
                    if eta_hours > 24:
                        logger.info(f"⏰ ETA: {eta_hours/24:.1f} days")
                    elif eta_hours > 1:
                        logger.info(f"⏰ ETA: {eta_hours:.1f} hours")
                    else:
                        logger.info(f"⏰ ETA: {eta_minutes:.1f} minutes")
                
                # Database statistics
                total_questions = db_stats.get('total_questions', 0)
                unique_questions = db_stats.get('unique_questions', 0)
                
                logger.info(f"🗄️  Database: {total_questions} total, {unique_questions} unique questions")
                
                if runtime_minutes > 0:
                    questions_per_minute = total_questions / runtime_minutes
                    logger.info(f"📈 Question Rate: {questions_per_minute:.1f} questions/minute")
                
                # Worker statistics
                active_workers = int(queue_stats.get('active_workers', 0))
                logger.info(f"👥 Active Workers: {active_workers}")
                
                # Top tags
                top_tags = db_stats.get('top_tags', {})
                if top_tags:
                    top_5_tags = list(top_tags.items())[:5]
                    tags_str = ', '.join([f"{tag}({count})" for tag, count in top_5_tags])
                    logger.info(f"🏷️  Top Tags: {tags_str}")
                
                logger.info("=" * 80)
                
                # Check if we've reached our target
                if unique_questions >= CONFIG.target_total_questions:
                    logger.info(f"🎉 TARGET REACHED! Scraped {unique_questions} unique questions")
                    self.shutdown()
                    break
                
                # Check for completion
                if pending_tasks == 0 and completed_tasks > 0:
                    logger.info("✅ All tasks completed!")
                    self.shutdown()
                    break
                
                # Sleep before next check
                time.sleep(60)  # Report every minute
                
        except KeyboardInterrupt:
            logger.info("Progress monitoring interrupted by user")
        except Exception as e:
            logger.error(f"Error in progress monitoring: {e}")
    
    def shutdown(self):
        """Gracefully shutdown the entire operation"""
        
        logger.info("Initiating graceful shutdown of scraping operation...")
        
        self.is_running = False
        
        try:
            # Stop local workers
            for worker_info in self.workers:
                worker_info['worker'].is_running = False
            
            logger.info("Stopping local workers...")
            
            # Wait for workers to finish current tasks (with timeout)
            for worker_info in self.workers:
                worker_info['thread'].join(timeout=30)
                if worker_info['thread'].is_alive():
                    logger.warning(f"Worker {worker_info['worker_id']} did not shutdown gracefully")
            
            # Stop auto-scaling
            if self.auto_scaler:
                self.auto_scaler.stop_auto_scaling()
                logger.info("Auto-scaling stopped")
            
            # Cleanup monitoring services
            stop_monitoring_services()
            
            # Final statistics
            self._print_final_stats()
            
            logger.info("Shutdown completed successfully")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    def _print_final_stats(self):
        """Print final statistics summary"""
        
        try:
            queue_stats = task_queue.get_stats()
            db_stats = data_storage.get_scraping_statistics()
            
            runtime = datetime.now() - self.start_time if self.start_time else None
            
            logger.info("\n" + "=" * 80)
            logger.info("FINAL SCRAPING STATISTICS")
            logger.info("=" * 80)
            
            if runtime:
                logger.info(f"Total Runtime: {runtime}")
            
            logger.info(f"Tasks Completed: {queue_stats.get('completed_tasks', 0)}")
            logger.info(f"Tasks Failed: {queue_stats.get('failed_tasks', 0)}")
            logger.info(f"Total Questions Scraped: {db_stats.get('total_questions', 0)}")
            logger.info(f"Unique Questions: {db_stats.get('unique_questions', 0)}")
            
            # Export final data
            filename = data_storage.export_questions_json()
            if filename:
                logger.info(f"Final data exported to: {filename}")
            
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"Error printing final stats: {e}")


def main():
    """Main entry point"""
    
    parser = argparse.ArgumentParser(description='Distributed Stack Overflow Scraper')
    parser.add_argument('mode', choices=['local', 'cloud', 'hybrid'], 
                       help='Scraping mode: local (single machine), cloud (EC2 only), or hybrid (both)')
    parser.add_argument('--workers', type=int, default=5,
                       help='Number of local workers (default: 5)')
    parser.add_argument('--instances', type=int, default=5,
                       help='Number of EC2 instances for cloud/hybrid mode (default: 5)')
    parser.add_argument('--target', type=int, default=100000,
                       help='Target number of questions to scrape (default: 100000)')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO', help='Logging level (default: INFO)')
    parser.add_argument('--setup-only', action='store_true',
                       help='Only set up infrastructure without starting scraping')
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('/var/log/stackoverflow-scraper.log' if sys.platform.startswith('linux') else 'scraper.log')
        ]
    )
    
    # Update target in config
    CONFIG.target_total_questions = args.target
    
    logger.info(f"Starting Distributed Stack Overflow Scraper in {args.mode} mode")
    logger.info(f"Target: {args.target:,} questions")
    
    orchestrator = ScrapingOrchestrator()
    
    try:
        # Set up infrastructure
        orchestrator.setup_infrastructure()
        
        if args.setup_only:
            logger.info("Infrastructure setup completed. Exiting as requested.")
            return
        
        # Start workers based on mode
        if args.mode in ['local', 'hybrid']:
            orchestrator.start_local_workers(args.workers)
        
        if args.mode in ['cloud', 'hybrid']:
            orchestrator.deploy_cloud_workers(args.instances)
        
        # Start monitoring progress
        orchestrator.monitor_progress()
        
    except KeyboardInterrupt:
        logger.info("Scraping operation interrupted by user")
    except Exception as e:
        logger.error(f"Scraping operation failed: {e}")
        raise
    finally:
        orchestrator.shutdown()


if __name__ == "__main__":
    main()