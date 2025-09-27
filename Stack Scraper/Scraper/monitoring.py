"""
Health Check and Monitoring System for Distributed Stack Overflow Scraper
Provides health endpoints, metrics collection, and system monitoring
"""

import time
import threading
import psutil
import logging
from datetime import datetime, timedelta
from typing import Dict, List
from flask import Flask, jsonify, request
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from config import CONFIG
from distributed_queue import task_queue
from data_storage import data_storage

logger = logging.getLogger(__name__)

# Prometheus metrics
QUESTIONS_SCRAPED = Counter('questions_scraped_total', 'Total questions scraped', ['worker_id'])
SCRAPING_DURATION = Histogram('scraping_duration_seconds', 'Time spent scraping questions')
ACTIVE_WORKERS = Gauge('active_workers', 'Number of active workers')
QUEUE_SIZE = Gauge('queue_size', 'Number of tasks in queue', ['queue_type'])
SYSTEM_CPU = Gauge('system_cpu_percent', 'System CPU usage percentage')
SYSTEM_MEMORY = Gauge('system_memory_percent', 'System memory usage percentage')
DATABASE_CONNECTIONS = Gauge('database_connections', 'Number of database connections')


class HealthCheckServer:
    """Health check and monitoring web server"""
    
    def __init__(self, port: int = None):
        self.port = port or CONFIG.monitoring.health_check_port
        self.app = Flask(__name__)
        self.setup_routes()
        self.is_healthy = True
        self.start_time = datetime.now()
        
    def setup_routes(self):
        """Setup Flask routes for health checking"""
        
        @self.app.route('/health')
        def health_check():
            """Basic health check endpoint"""
            try:
                # Check database connectivity
                db_healthy = self._check_database_health()
                
                # Check Redis connectivity
                redis_healthy = self._check_redis_health()
                
                # Overall health
                overall_healthy = db_healthy and redis_healthy and self.is_healthy
                
                status = {
                    'status': 'healthy' if overall_healthy else 'unhealthy',
                    'timestamp': datetime.now().isoformat(),
                    'uptime_seconds': (datetime.now() - self.start_time).total_seconds(),
                    'checks': {
                        'database': 'healthy' if db_healthy else 'unhealthy',
                        'redis': 'healthy' if redis_healthy else 'unhealthy',
                        'application': 'healthy' if self.is_healthy else 'unhealthy'
                    }
                }
                
                return jsonify(status), 200 if overall_healthy else 503
                
            except Exception as e:
                logger.error(f"Health check error: {e}")
                return jsonify({
                    'status': 'unhealthy',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 503
        
        @self.app.route('/metrics')
        def metrics():
            """Prometheus metrics endpoint"""
            try:
                # Update system metrics
                self._update_system_metrics()
                
                # Generate Prometheus format
                return generate_latest(), 200, {'Content-Type': 'text/plain'}
                
            except Exception as e:
                logger.error(f"Metrics error: {e}")
                return str(e), 500
        
        @self.app.route('/stats')
        def stats():
            """Detailed statistics endpoint"""
            try:
                stats = self._get_comprehensive_stats()
                return jsonify(stats), 200
                
            except Exception as e:
                logger.error(f"Stats error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/workers')
        def workers():
            """Active workers information"""
            try:
                worker_info = task_queue.get_stats()
                return jsonify(worker_info), 200
                
            except Exception as e:
                logger.error(f"Workers error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/shutdown', methods=['POST'])
        def shutdown():
            """Graceful shutdown endpoint"""
            try:
                auth_key = request.headers.get('Authorization')
                if auth_key != f"Bearer {CONFIG.shutdown_key}":
                    return jsonify({'error': 'Unauthorized'}), 401
                
                logger.info("Received shutdown request")
                self.is_healthy = False
                
                # Trigger graceful shutdown
                threading.Thread(target=self._graceful_shutdown, daemon=True).start()
                
                return jsonify({'status': 'shutting_down'}), 200
                
            except Exception as e:
                logger.error(f"Shutdown error: {e}")
                return jsonify({'error': str(e)}), 500
    
    def _check_database_health(self) -> bool:
        """Check database connectivity"""
        try:
            count = data_storage.get_question_count()
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    def _check_redis_health(self) -> bool:
        """Check Redis connectivity"""
        try:
            stats = task_queue.get_stats()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False
    
    def _update_system_metrics(self):
        """Update system-level Prometheus metrics"""
        try:
            # System metrics
            SYSTEM_CPU.set(psutil.cpu_percent())
            SYSTEM_MEMORY.set(psutil.virtual_memory().percent)
            
            # Queue metrics
            stats = task_queue.get_stats()
            QUEUE_SIZE.labels(queue_type='pending').set(stats.get('pending_tasks', 0))
            QUEUE_SIZE.labels(queue_type='processing').set(stats.get('processing_tasks', 0))
            ACTIVE_WORKERS.set(stats.get('active_workers', 0))
            
        except Exception as e:
            logger.error(f"Error updating metrics: {e}")
    
    def _get_comprehensive_stats(self) -> Dict:
        """Get comprehensive system statistics"""
        try:
            # Task queue stats
            queue_stats = task_queue.get_stats()
            
            # Database stats
            db_stats = data_storage.get_scraping_statistics()
            
            # System stats
            system_stats = {
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('/').percent,
                'network_io': dict(psutil.net_io_counters()._asdict()),
                'uptime_seconds': (datetime.now() - self.start_time).total_seconds()
            }
            
            return {
                'timestamp': datetime.now().isoformat(),
                'queue': queue_stats,
                'database': db_stats,
                'system': system_stats,
                'instance_id': CONFIG.aws.instance_id,
                'worker_id': CONFIG.worker_id
            }
            
        except Exception as e:
            logger.error(f"Error getting comprehensive stats: {e}")
            return {'error': str(e)}
    
    def _graceful_shutdown(self):
        """Perform graceful shutdown"""
        logger.info("Starting graceful shutdown process")
        
        # Wait for current operations to complete
        time.sleep(5)
        
        # Close database connections
        data_storage.close_connection()
        
        # Shutdown task queue
        task_queue.shutdown_gracefully()
        
        logger.info("Graceful shutdown completed")
    
    def run(self):
        """Start the health check server"""
        logger.info(f"Starting health check server on port {self.port}")
        self.app.run(host='0.0.0.0', port=self.port, debug=False)


class SystemMonitor:
    """Background system monitoring and alerting"""
    
    def __init__(self):
        self.is_running = False
        self.monitor_thread = None
        self.alert_thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'disk_usage_percent': 90.0,
            'queue_size': 1000,
            'error_rate': 10.0
        }
        
    def start_monitoring(self):
        """Start background monitoring"""
        self.is_running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("System monitoring started")
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        self.is_running = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        logger.info("System monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.is_running:
            try:
                self._check_system_health()
                self._check_queue_health()
                self._check_database_health()
                
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                time.sleep(30)  # Shorter sleep on error
    
    def _check_system_health(self):
        """Check system resource health"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent
            disk_percent = psutil.disk_usage('/').percent
            
            if cpu_percent > self.alert_thresholds['cpu_percent']:
                self._send_alert(f"High CPU usage: {cpu_percent}%")
            
            if memory_percent > self.alert_thresholds['memory_percent']:
                self._send_alert(f"High memory usage: {memory_percent}%")
            
            if disk_percent > self.alert_thresholds['disk_usage_percent']:
                self._send_alert(f"High disk usage: {disk_percent}%")
                
        except Exception as e:
            logger.error(f"System health check error: {e}")
    
    def _check_queue_health(self):
        """Check task queue health"""
        try:
            stats = task_queue.get_stats()
            
            pending_tasks = int(stats.get('pending_tasks', 0))
            if pending_tasks > self.alert_thresholds['queue_size']:
                self._send_alert(f"Large queue size: {pending_tasks} pending tasks")
            
            active_workers = int(stats.get('active_workers', 0))
            if active_workers == 0:
                self._send_alert("No active workers detected")
                
        except Exception as e:
            logger.error(f"Queue health check error: {e}")
    
    def _check_database_health(self):
        """Check database health"""
        try:
            # Simple connectivity check
            count = data_storage.get_question_count()
            logger.debug(f"Database health check: {count} total questions")
            
        except Exception as e:
            self._send_alert(f"Database health issue: {str(e)}")
    
    def _send_alert(self, message: str):
        """Send alert (implement your preferred alerting method)"""
        logger.warning(f"ALERT: {message}")
        
        # TODO: Implement actual alerting (Slack, email, SNS, etc.)
        # For now, just log the alert


class PerformanceCollector:
    """Collect and track performance metrics"""
    
    def __init__(self):
        self.metrics = {
            'questions_per_minute': [],
            'response_times': [],
            'error_counts': {},
            'worker_performance': {}
        }
        self._lock = threading.RLock()
    
    def record_questions_scraped(self, worker_id: str, count: int):
        """Record questions scraped by worker"""
        with self._lock:
            QUESTIONS_SCRAPED.labels(worker_id=worker_id).inc(count)
            
            if worker_id not in self.metrics['worker_performance']:
                self.metrics['worker_performance'][worker_id] = {
                    'total_questions': 0,
                    'start_time': datetime.now()
                }
            
            self.metrics['worker_performance'][worker_id]['total_questions'] += count
    
    def record_scraping_duration(self, duration_seconds: float):
        """Record time taken for scraping operation"""
        SCRAPING_DURATION.observe(duration_seconds)
        
        with self._lock:
            self.metrics['response_times'].append(duration_seconds)
            
            # Keep only last 1000 measurements
            if len(self.metrics['response_times']) > 1000:
                self.metrics['response_times'] = self.metrics['response_times'][-1000:]
    
    def record_error(self, error_type: str):
        """Record an error occurrence"""
        with self._lock:
            self.metrics['error_counts'][error_type] = self.metrics['error_counts'].get(error_type, 0) + 1
    
    def get_performance_summary(self) -> Dict:
        """Get performance summary statistics"""
        with self._lock:
            summary = {
                'total_workers': len(self.metrics['worker_performance']),
                'total_questions': sum(
                    worker['total_questions'] 
                    for worker in self.metrics['worker_performance'].values()
                ),
                'avg_response_time': (
                    sum(self.metrics['response_times']) / len(self.metrics['response_times'])
                    if self.metrics['response_times'] else 0
                ),
                'error_summary': dict(self.metrics['error_counts']),
                'worker_performance': dict(self.metrics['worker_performance'])
            }
            
            return summary


# Global instances
health_server = None
system_monitor = SystemMonitor()
performance_collector = PerformanceCollector()


def start_monitoring_services():
    """Start all monitoring services"""
    global health_server
    
    try:
        # Start health check server
        health_server = HealthCheckServer()
        health_thread = threading.Thread(target=health_server.run, daemon=True)
        health_thread.start()
        
        # Start system monitoring
        system_monitor.start_monitoring()
        
        logger.info("All monitoring services started successfully")
        
    except Exception as e:
        logger.error(f"Error starting monitoring services: {e}")


def stop_monitoring_services():
    """Stop all monitoring services"""
    try:
        system_monitor.stop_monitoring()
        logger.info("Monitoring services stopped")
        
    except Exception as e:
        logger.error(f"Error stopping monitoring services: {e}")


if __name__ == "__main__":
    # Test the health check server
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        server = HealthCheckServer()
        server.run()
    else:
        start_monitoring_services()
        
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            stop_monitoring_services()