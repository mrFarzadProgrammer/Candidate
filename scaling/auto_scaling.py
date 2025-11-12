"""
سیستم Auto-Scaling و Load Balancing
مدیریت خودکار فشار و توزیع بار
"""

import psutil
import os
from datetime import datetime
import redis
import logging

logger = logging.getLogger('scaling')


# ============================================================
# 1. HEALTH CHECK & MONITORING
# ============================================================

class SystemMonitor:
    """مانیتورینگ سلامت سیستم"""
    
    def __init__(self):
        self.redis_client = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))
        self.thresholds = {
            'cpu': 80,  # درصد
            'memory': 85,  # درصد
            'disk': 90,  # درصد
            'response_time': 2000,  # میلی‌ثانیه
        }
    
    def get_system_health(self):
        """دریافت وضعیت سلامت سیستم"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        health_status = {
            'timestamp': datetime.utcnow().isoformat(),
            'cpu': {
                'percent': cpu_percent,
                'status': 'healthy' if cpu_percent < self.thresholds['cpu'] else 'warning'
            },
            'memory': {
                'percent': memory.percent,
                'available_mb': memory.available / (1024 * 1024),
                'status': 'healthy' if memory.percent < self.thresholds['memory'] else 'warning'
            },
            'disk': {
                'percent': disk.percent,
                'free_gb': disk.free / (1024 * 1024 * 1024),
                'status': 'healthy' if disk.percent < self.thresholds['disk'] else 'warning'
            }
        }
        
        # ذخیره در Redis
        self.redis_client.setex(
            f'health_check:{os.getenv("SERVER_ID", "default")}',
            60,  # 1 دقیقه
            str(health_status)
        )
        
        return health_status
    
    def should_scale_up(self):
        """آیا نیاز به افزایش ظرفیت است؟"""
        health = self.get_system_health()
        
        critical_conditions = [
            health['cpu']['percent'] > self.thresholds['cpu'],
            health['memory']['percent'] > self.thresholds['memory'],
        ]
        
        return any(critical_conditions)
    
    def get_all_servers_health(self):
        """دریافت وضعیت همه سرورها"""
        pattern = 'health_check:*'
        servers = []
        
        for key in self.redis_client.scan_iter(pattern):
            server_id = key.decode().split(':')[1]
            health = eval(self.redis_client.get(key).decode())
            servers.append({
                'server_id': server_id,
                'health': health
            })
        
        return servers


# ============================================================
# 2. LOAD BALANCING STRATEGIES
# ============================================================

class LoadBalancer:
    """توزیع بار بین سرورها"""
    
    def __init__(self):
        self.redis_client = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))
        self.servers = self._get_available_servers()
        self.strategy = os.getenv('LB_STRATEGY', 'least_connections')  # یا 'round_robin' یا 'geo'
    
    def _get_available_servers(self):
        """لیست سرورهای آنلاین"""
        # از Redis بخواند
        servers_key = 'available_servers'
        servers = self.redis_client.smembers(servers_key)
        return [s.decode() for s in servers]
    
    def register_server(self, server_id, server_url, province=None):
        """ثبت سرور جدید"""
        self.redis_client.sadd('available_servers', server_id)
        self.redis_client.hset('server_info', server_id, f'{server_url}|{province or ""}')
        self.redis_client.hset('server_connections', server_id, 0)
        
        logger.info(f'Server registered: {server_id} - {server_url}')
    
    def unregister_server(self, server_id):
        """حذف سرور"""
        self.redis_client.srem('available_servers', server_id)
        self.redis_client.hdel('server_info', server_id)
        self.redis_client.hdel('server_connections', server_id)
        
        logger.info(f'Server unregistered: {server_id}')
    
    def get_server_for_request(self, user_province=None):
        """انتخاب سرور مناسب برای درخواست"""
        
        if self.strategy == 'geo' and user_province:
            # انتخاب بر اساس استان
            return self._get_server_by_province(user_province)
        
        elif self.strategy == 'least_connections':
            # کمترین تعداد connection
            return self._get_least_loaded_server()
        
        else:  # round_robin
            return self._get_next_server_round_robin()
    
    def _get_server_by_province(self, province):
        """سرور اختصاصی استان"""
        # جستجوی سرور اختصاصی استان
        for server_id, info in self.redis_client.hgetall('server_info').items():
            server_url, server_province = info.decode().split('|')
            if server_province == province:
                self._increment_connections(server_id.decode())
                return server_url
        
        # اگر نبود، از least_loaded استفاده کن
        return self._get_least_loaded_server()
    
    def _get_least_loaded_server(self):
        """سرور با کمترین بار"""
        connections = self.redis_client.hgetall('server_connections')
        
        if not connections:
            return None
        
        # پیدا کردن کمترین
        min_server = min(connections.items(), key=lambda x: int(x[1]))
        server_id = min_server[0].decode()
        
        self._increment_connections(server_id)
        
        # دریافت URL
        server_info = self.redis_client.hget('server_info', server_id).decode()
        server_url = server_info.split('|')[0]
        
        return server_url
    
    def _get_next_server_round_robin(self):
        """توزیع نوبتی"""
        current = self.redis_client.incr('round_robin_counter')
        servers = list(self.redis_client.smembers('available_servers'))
        
        if not servers:
            return None
        
        server_id = servers[current % len(servers)].decode()
        server_info = self.redis_client.hget('server_info', server_id).decode()
        
        return server_info.split('|')[0]
    
    def _increment_connections(self, server_id):
        """افزایش تعداد connection"""
        self.redis_client.hincrby('server_connections', server_id, 1)
    
    def release_connection(self, server_id):
        """کاهش تعداد connection"""
        self.redis_client.hincrby('server_connections', server_id, -1)


# ============================================================
# 3. CIRCUIT BREAKER (جلوگیری از overload)
# ============================================================

class CircuitBreaker:
    """
    جلوگیری از ارسال درخواست به سرور مشکل‌دار
    """
    
    def __init__(self, failure_threshold=5, timeout=60):
        self.redis_client = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))
        self.failure_threshold = failure_threshold
        self.timeout = timeout
    
    def is_open(self, server_id):
        """آیا circuit باز است؟ (نباید درخواست بفرستیم)"""
        key = f'circuit_breaker:{server_id}'
        failures = self.redis_client.get(key)
        
        if not failures:
            return False
        
        return int(failures) >= self.failure_threshold
    
    def record_failure(self, server_id):
        """ثبت خطا"""
        key = f'circuit_breaker:{server_id}'
        failures = self.redis_client.incr(key)
        
        if failures == 1:
            # اولین خطا - تنظیم timeout
            self.redis_client.expire(key, self.timeout)
        
        if failures >= self.failure_threshold:
            logger.warning(f'Circuit breaker opened for server: {server_id}')
    
    def record_success(self, server_id):
        """ثبت موفقیت - ریست circuit"""
        key = f'circuit_breaker:{server_id}'
        self.redis_client.delete(key)


# ============================================================
# 4. REQUEST QUEUE (صف درخواست‌ها)
# ============================================================

from celery import Celery

celery_app = Celery(
    'election_bot',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
)

celery_app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='Asia/Tehran',
    enable_utc=True,
    task_acks_late=True,  # تایید بعد از اتمام
    worker_prefetch_multiplier=1,  # یکی یکی بگیر
    task_soft_time_limit=300,  # 5 دقیقه
    task_time_limit=600,  # 10 دقیقه max
)


@celery_app.task(bind=True, max_retries=3)
def send_broadcast_async(self, message_id):
    """ارسال پیام همگانی به صورت async"""
    try:
        from bot_engine.broadcast_sender import send_broadcast_to_subscribers
        send_broadcast_to_subscribers(message_id)
    except Exception as exc:
        # تلاش مجدد با delay
        raise self.retry(exc=exc, countdown=60)


@celery_app.task
def generate_analytics_report(candidate_id):
    """تولید گزارش آماری"""
    from candidate_panel.benchmark_utils import calculate_candidate_ranking
    return calculate_candidate_ranking(candidate_id)


@celery_app.task
def backup_database():
    """پشتیبان‌گیری خودکار"""
    import subprocess
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f'/backups/db_backup_{timestamp}.sql'
    
    # PostgreSQL
    subprocess.run([
        'pg_dump',
        '-U', os.getenv('DB_USER'),
        '-h', os.getenv('DB_HOST'),
        '-d', os.getenv('DB_NAME'),
        '-f', backup_file
    ])
    
    logger.info(f'Database backup created: {backup_file}')


# ============================================================
# 5. CACHING STRATEGY
# ============================================================

class CacheManager:
    """مدیریت cache با Redis"""
    
    def __init__(self):
        self.redis_client = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))
        self.default_ttl = 300  # 5 دقیقه
    
    def get(self, key):
        """دریافت از cache"""
        value = self.redis_client.get(key)
        return eval(value) if value else None
    
    def set(self, key, value, ttl=None):
        """ذخیره در cache"""
        ttl = ttl or self.default_ttl
        self.redis_client.setex(key, ttl, str(value))
    
    def delete(self, key):
        """حذف از cache"""
        self.redis_client.delete(key)
    
    def clear_pattern(self, pattern):
        """حذف گروهی"""
        for key in self.redis_client.scan_iter(pattern):
            self.redis_client.delete(key)
    
    # مثال‌های استفاده:
    
    def get_candidate_ranking(self, candidate_id):
        """دریافت رتبه با cache"""
        key = f'ranking:candidate:{candidate_id}'
        cached = self.get(key)
        
        if cached:
            return cached
        
        # محاسبه
        from candidate_panel.benchmark_utils import calculate_candidate_ranking
        ranking = calculate_candidate_ranking(candidate_id)
        
        # ذخیره در cache
        self.set(key, ranking, ttl=600)  # 10 دقیقه
        
        return ranking
    
    def invalidate_candidate_cache(self, candidate_id):
        """پاک کردن cache نامزد"""
        self.clear_pattern(f'ranking:candidate:{candidate_id}*')
        self.clear_pattern(f'analytics:candidate:{candidate_id}*')


# ============================================================
# 6. DATABASE CONNECTION POOLING
# ============================================================

class DatabasePoolConfig:
    """تنظیمات connection pool"""
    
    # SQLAlchemy Pool Settings
    SQLALCHEMY_POOL_SIZE = 20  # تعداد connectionهای permanent
    SQLALCHEMY_MAX_OVERFLOW = 40  # تعداد اضافی در شرایط peak
    SQLALCHEMY_POOL_TIMEOUT = 30  # timeout برای گرفتن connection
    SQLALCHEMY_POOL_RECYCLE = 3600  # recycle بعد از 1 ساعت
    SQLALCHEMY_POOL_PRE_PING = True  # بررسی سلامت قبل از استفاده
    
    # برای Production با PostgreSQL
    @staticmethod
    def get_database_url():
        """ساخت URL با pooling"""
        return f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', 5432)}/{os.getenv('DB_NAME')}?pool_size=20&max_overflow=40"
