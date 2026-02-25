import httpx
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import redis
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import psutil
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
ACTIVE_CONNECTIONS = Gauge('active_connections', 'Active database connections')
REDIS_MEMORY_USAGE = Gauge('redis_memory_usage_bytes', 'Redis memory usage')
CPU_USAGE = Gauge('cpu_usage_percent', 'CPU usage percentage')
MEMORY_USAGE = Gauge('memory_usage_percent', 'Memory usage percentage')
DISK_USAGE = Gauge('disk_usage_percent', 'Disk usage percentage')

class PerformanceMonitor:
    """
    Performance monitoring system for MotionMath AI
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_client = redis.from_url(redis_url)
        self.metrics_server_port = 9090
        self.start_metrics_server()
        
    def start_metrics_server(self):
        """Start Prometheus metrics server"""
        start_http_server(self.metrics_server_port)
        logger.info(f"Metrics server started on port {self.metrics_server_port}")
    
    async def collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system performance metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            CPU_USAGE.set(cpu_percent)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            MEMORY_USAGE.set(memory.percent)
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            DISK_USAGE.set(disk.percent)
            
            # Network metrics
            network = psutil.net_io_counters()
            
            metrics = {
                'timestamp': datetime.utcnow().isoformat(),
                'cpu': {
                    'usage_percent': cpu_percent,
                    'count': psutil.cpu_count(),
                    'freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
                },
                'memory': {
                    'usage_percent': memory.percent,
                    'available': memory.available,
                    'used': memory.used,
                    'total': memory.total
                },
                'disk': {
                    'usage_percent': disk.percent,
                    'free': disk.free,
                    'used': disk.used,
                    'total': disk.total
                },
                'network': {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                }
            }
            
            # Store metrics in Redis for time-series analysis
            await self.store_metrics('system', metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return {}
    
    async def collect_application_metrics(self) -> Dict[str, Any]:
        """Collect application-specific metrics"""
        try:
            # Get metrics from Redis
            app_metrics = {
                'timestamp': datetime.utcnow().isoformat(),
                'active_users': await self.get_active_users(),
                'equations_processed': await self.get_equations_processed(),
                'api_response_time': await self.get_api_response_time(),
                'error_rate': await self.get_error_rate(),
                'cache_hit_rate': await self.get_cache_hit_rate(),
                'queue_length': await self.get_queue_length()
            }
            
            # Store metrics in Redis
            await self.store_metrics('application', app_metrics)
            
            return app_metrics
            
        except Exception as e:
            logger.error(f"Error collecting application metrics: {e}")
            return {}
    
    async def collect_database_metrics(self) -> Dict[str, Any]:
        """Collect database performance metrics"""
        try:
            # In production, connect to actual database
            db_metrics = {
                'timestamp': datetime.utcnow().isoformat(),
                'active_connections': 25,  # Placeholder
                'query_time_avg': 0.05,  # Placeholder
                'slow_queries': 2,  # Placeholder
                'database_size': '1.2GB',  # Placeholder
                'index_usage': 0.85,  # Placeholder
                'cache_hit_ratio': 0.95  # Placeholder
            }
            
            ACTIVE_CONNECTIONS.set(db_metrics['active_connections'])
            
            # Store metrics in Redis
            await self.store_metrics('database', db_metrics)
            
            return db_metrics
            
        except Exception as e:
            logger.error(f"Error collecting database metrics: {e}")
            return {}
    
    async def collect_redis_metrics(self) -> Dict[str, Any]:
        """Collect Redis performance metrics"""
        try:
            info = self.redis_client.info()
            
            redis_metrics = {
                'timestamp': datetime.utcnow().isoformat(),
                'connected_clients': info.get('connected_clients', 0),
                'used_memory': info.get('used_memory', 0),
                'used_memory_human': info.get('used_memory_human', '0B'),
                'used_memory_peak': info.get('used_memory_peak', 0),
                'used_memory_peak_human': info.get('used_memory_peak_human', '0B'),
                'total_commands_processed': info.get('total_commands_processed', 0),
                'instantaneous_ops_per_sec': info.get('instantaneous_ops_per_sec', 0),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'hit_rate': self.calculate_hit_rate(info)
            }
            
            REDIS_MEMORY_USAGE.set(redis_metrics['used_memory'])
            
            # Store metrics in Redis
            await self.store_metrics('redis', redis_metrics)
            
            return redis_metrics
            
        except Exception as e:
            logger.error(f"Error collecting Redis metrics: {e}")
            return {}
    
    def calculate_hit_rate(self, info: Dict) -> float:
        """Calculate Redis hit rate"""
        hits = info.get('keyspace_hits', 0)
        misses = info.get('keyspace_misses', 0)
        total = hits + misses
        
        if total == 0:
            return 0.0
        
        return (hits / total) * 100
    
    async def store_metrics(self, metric_type: str, metrics: Dict[str, Any]):
        """Store metrics in Redis for time-series analysis"""
        try:
            key = f"metrics:{metric_type}:{datetime.utcnow().strftime('%Y%m%d%H%M')}"
            self.redis_client.setex(key, 86400, json.dumps(metrics))  # Keep for 24 hours
            
            # Also store latest metrics
            latest_key = f"latest_metrics:{metric_type}"
            self.redis_client.set(latest_key, json.dumps(metrics))
            
        except Exception as e:
            logger.error(f"Error storing metrics: {e}")
    
    async def get_active_users(self) -> int:
        """Get number of active users"""
        try:
            # In production, query database for active users
            return 1000  # Placeholder
        except Exception:
            return 0
    
    async def get_equations_processed(self) -> int:
        """Get number of equations processed"""
        try:
            # In production, query database or Redis
            return 5000  # Placeholder
        except Exception:
            return 0
    
    async def get_api_response_time(self) -> float:
        """Get average API response time"""
        try:
            # In production, calculate from request logs
            return 0.5  # Placeholder
        except Exception:
            return 0.0
    
    async def get_error_rate(self) -> float:
        """Get current error rate"""
        try:
            # In production, calculate from error logs
            return 0.02  # Placeholder
        except Exception:
            return 0.0
    
    async def get_cache_hit_rate(self) -> float:
        """Get cache hit rate"""
        try:
            info = self.redis_client.info()
            return self.calculate_hit_rate(info)
        except Exception:
            return 0.0
    
    async def get_queue_length(self) -> int:
        """Get Celery queue length"""
        try:
            return self.redis_client.llen('celery')
        except Exception:
            return 0
    
    async def analyze_performance_trends(self) -> Dict[str, Any]:
        """Analyze performance trends over time"""
        try:
            # Get metrics from last 24 hours
            trends = {}
            
            for metric_type in ['system', 'application', 'database', 'redis']:
                trends[metric_type] = await self.analyze_metric_trends(metric_type)
            
            return trends
            
        except Exception as e:
            logger.error(f"Error analyzing performance trends: {e}")
            return {}
    
    async def analyze_metric_trends(self, metric_type: str) -> Dict[str, Any]:
        """Analyze trends for a specific metric type"""
        try:
            # Get historical metrics from Redis
            pattern = f"metrics:{metric_type}:*"
            keys = self.redis_client.keys(pattern)
            
            if not keys:
                return {}
            
            # Sort keys by timestamp
            keys.sort()
            
            # Get last 24 hours of data
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            recent_keys = [k for k in keys if self.parse_key_timestamp(k) > cutoff_time]
            
            if not recent_keys:
                return {}
            
            # Analyze trends
            metrics_data = []
            for key in recent_keys[-24:]:  # Last 24 data points
                data = self.redis_client.get(key)
                if data:
                    metrics_data.append(json.loads(data))
            
            return self.calculate_trends(metrics_data)
            
        except Exception as e:
            logger.error(f"Error analyzing {metric_type} trends: {e}")
            return {}
    
    def parse_key_timestamp(self, key: str) -> datetime:
        """Parse timestamp from Redis key"""
        try:
            timestamp_str = key.decode().split(':')[-1]
            return datetime.strptime(timestamp_str, '%Y%m%d%H%M')
        except Exception:
            return datetime.min
    
    def calculate_trends(self, metrics_data: List[Dict]) -> Dict[str, Any]:
        """Calculate trends from metrics data"""
        if not metrics_data:
            return {}
        
        # Simple trend analysis - can be enhanced with more sophisticated algorithms
        trends = {
            'data_points': len(metrics_data),
            'time_range': {
                'start': metrics_data[0].get('timestamp'),
                'end': metrics_data[-1].get('timestamp')
            }
        }
        
        # Analyze CPU trend if available
        if 'cpu' in metrics_data[0]:
            cpu_values = [m['cpu']['usage_percent'] for m in metrics_data if 'cpu' in m]
            if cpu_values:
                trends['cpu'] = {
                    'current': cpu_values[-1],
                    'average': sum(cpu_values) / len(cpu_values),
                    'trend': 'increasing' if cpu_values[-1] > cpu_values[0] else 'decreasing'
                }
        
        # Analyze memory trend if available
        if 'memory' in metrics_data[0]:
            memory_values = [m['memory']['usage_percent'] for m in metrics_data if 'memory' in m]
            if memory_values:
                trends['memory'] = {
                    'current': memory_values[-1],
                    'average': sum(memory_values) / len(memory_values),
                    'trend': 'increasing' if memory_values[-1] > memory_values[0] else 'decreasing'
                }
        
        return trends
    
    async def generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        try:
            # Collect current metrics
            system_metrics = await self.collect_system_metrics()
            app_metrics = await self.collect_application_metrics()
            db_metrics = await self.collect_database_metrics()
            redis_metrics = await self.collect_redis_metrics()
            
            # Analyze trends
            trends = await self.analyze_performance_trends()
            
            # Generate recommendations
            recommendations = self.generate_recommendations(
                system_metrics, app_metrics, db_metrics, redis_metrics, trends
            )
            
            report = {
                'timestamp': datetime.utcnow().isoformat(),
                'current_metrics': {
                    'system': system_metrics,
                    'application': app_metrics,
                    'database': db_metrics,
                    'redis': redis_metrics
                },
                'trends': trends,
                'recommendations': recommendations,
                'health_score': self.calculate_health_score(
                    system_metrics, app_metrics, db_metrics, redis_metrics
                )
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating performance report: {e}")
            return {}
    
    def generate_recommendations(self, *metrics) -> List[str]:
        """Generate performance recommendations"""
        recommendations = []
        
        # System recommendations
        if metrics and len(metrics) > 0 and metrics[0]:
            system = metrics[0]
            if system.get('cpu', {}).get('usage_percent', 0) > 80:
                recommendations.append("High CPU usage detected. Consider scaling up or optimizing CPU-intensive tasks.")
            
            if system.get('memory', {}).get('usage_percent', 0) > 85:
                recommendations.append("High memory usage detected. Consider adding more memory or optimizing memory usage.")
            
            if system.get('disk', {}).get('usage_percent', 0) > 90:
                recommendations.append("Low disk space. Consider cleaning up old files or expanding storage.")
        
        # Application recommendations
        if len(metrics) > 1 and metrics[1]:
            app = metrics[1]
            if app.get('error_rate', 0) > 0.05:
                recommendations.append("High error rate detected. Review error logs and fix underlying issues.")
            
            if app.get('api_response_time', 0) > 1.0:
                recommendations.append("Slow API response times. Consider optimizing database queries or adding caching.")
        
        # Database recommendations
        if len(metrics) > 2 and metrics[2]:
            db = metrics[2]
            if db.get('active_connections', 0) > 80:
                recommendations.append("High database connection count. Consider connection pooling optimization.")
            
            if db.get('slow_queries', 0) > 5:
                recommendations.append("Slow queries detected. Review and optimize database queries.")
        
        # Redis recommendations
        if len(metrics) > 3 and metrics[3]:
            redis = metrics[3]
            if redis.get('hit_rate', 0) < 80:
                recommendations.append("Low Redis hit rate. Review caching strategy and cache keys.")
        
        return recommendations
    
    def calculate_health_score(self, *metrics) -> float:
        """Calculate overall health score (0-100)"""
        score = 100.0
        
        # Deduct points for high resource usage
        if metrics and len(metrics) > 0 and metrics[0]:
            system = metrics[0]
            cpu_usage = system.get('cpu', {}).get('usage_percent', 0)
            memory_usage = system.get('memory', {}).get('usage_percent', 0)
            
            if cpu_usage > 80:
                score -= (cpu_usage - 80) * 0.5
            if memory_usage > 85:
                score -= (memory_usage - 85) * 0.5
        
        # Deduct points for application issues
        if len(metrics) > 1 and metrics[1]:
            app = metrics[1]
            error_rate = app.get('error_rate', 0)
            response_time = app.get('api_response_time', 0)
            
            if error_rate > 0.05:
                score -= error_rate * 100
            if response_time > 1.0:
                score -= (response_time - 1.0) * 10
        
        # Ensure score doesn't go below 0
        return max(0, score)

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

async def main():
    """Main monitoring loop"""
    logger.info("Starting performance monitoring...")
    
    while True:
        try:
            # Collect all metrics
            await performance_monitor.collect_system_metrics()
            await performance_monitor.collect_application_metrics()
            await performance_monitor.collect_database_metrics()
            await performance_monitor.collect_redis_metrics()
            
            # Generate report every hour
            if datetime.utcnow().minute == 0:
                report = await performance_monitor.generate_performance_report()
                logger.info(f"Performance report generated: {report.get('health_score', 0)}")
            
            # Sleep for 1 minute
            await asyncio.sleep(60)
            
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}")
            await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
