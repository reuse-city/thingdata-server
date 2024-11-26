from typing import Dict, Optional
import psutil
import asyncio
from datetime import datetime
import aiohttp
from sqlalchemy import text
from app.database import get_db
from app.schemas import ComponentStatus, HealthResponse, HealthMetrics
from app.logger import setup_logger

logger = setup_logger(__name__)

class HealthChecker:
    def __init__(self):
        self.last_check: Optional[datetime] = None
        self.cache_duration = 60  # seconds
        self._health_cache: Optional[HealthResponse] = None

    async def check_health(self, force: bool = False) -> HealthResponse:
        """Comprehensive system health check."""
        try:
            # Use cached response if available and recent
            if not force and self._health_cache and self.last_check:
                if (datetime.utcnow() - self.last_check).seconds < self.cache_duration:
                    return self._health_cache

            # Check all components concurrently
            db_status, storage_status, federation_status, metrics = await asyncio.gather(
                self._check_database(),
                self._check_storage(),
                self._check_federation(),
                self._collect_metrics()
            )

            # Determine overall status
            overall_status = self._determine_overall_status({
                "database": db_status,
                "storage": storage_status,
                "federation": federation_status
            })

            health_response = HealthResponse(
                status=overall_status,
                timestamp=datetime.utcnow().isoformat(),
                version="0.1.0",
                components={
                    "database": db_status,
                    "storage": storage_status,
                    "federation": federation_status,
                    "api": ComponentStatus.HEALTHY
                },
                metrics=metrics
            )

            # Update cache
            self._health_cache = health_response
            self.last_check = datetime.utcnow()

            return health_response

        except Exception as e:
            logger.error(f"Health check failed: {str(e)}", exc_info=True)
            return HealthResponse(
                status="unhealthy",
                timestamp=datetime.utcnow().isoformat(),
                version="0.1.0",
                components={
                    "database": ComponentStatus.UNHEALTHY,
                    "storage": ComponentStatus.UNHEALTHY,
                    "federation": ComponentStatus.UNHEALTHY,
                    "api": ComponentStatus.HEALTHY
                },
                metrics=await self._collect_metrics()
            )

    async def _check_database(self) -> ComponentStatus:
        """Check database connectivity and performance."""
        try:
            db = next(get_db())
            
            # Basic connectivity check
            db.execute(text("SELECT 1"))
            
            # Check connection pool
            pool_info = db.execute(text("""
                SELECT count(*) as connections
                FROM pg_stat_activity
                WHERE datname = current_database()
            """)).scalar()
            
            # Check database size
            db_size = db.execute(text("""
                SELECT pg_database_size(current_database())
            """)).scalar()
            
            if pool_info > 100 or db_size > 10_000_000_000:  # 10GB
                return ComponentStatus.DEGRADED
                
            return ComponentStatus.HEALTHY
            
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return ComponentStatus.UNHEALTHY

    async def _check_storage(self) -> ComponentStatus:
        """Check storage system health."""
        try:
            from app.storage import storage_manager
            
            # Check S3/MinIO connectivity
            storage_status = await storage_manager.check_health()
            
            # Check disk space
            disk = psutil.disk_usage('/')
            if disk.percent > 90:
                return ComponentStatus.DEGRADED
                
            return storage_status
            
        except Exception as e:
            logger.error(f"Storage health check failed: {str(e)}")
            return ComponentStatus.UNHEALTHY

    async def _check_federation(self) -> ComponentStatus:
        """Check federation network health."""
        try:
            from app.federation import federation_manager
            
            # Check federation network
            federation_status = await federation_manager.check_health()
            
            # Additional federation metrics could be checked here
            
            return federation_status
            
        except Exception as e:
            logger.error(f"Federation health check failed: {str(e)}")
            return ComponentStatus.UNHEALTHY

    async def _collect_metrics(self) -> HealthMetrics:
        """Collect system metrics."""
        try:
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Get active connections (could be tracked in your app)
            active_connections = 0  # Implement connection tracking
            
            # Get storage usage
            storage_usage = psutil.disk_usage('/').percent
            
            # Get federation peers count
            from app.federation import federation_manager
            federation_peers = len(federation_manager.known_instances)
            
            return HealthMetrics(
                memory_usage=memory.percent,
                cpu_usage=cpu_percent,
                active_connections=active_connections,
                storage_usage=storage_usage,
                federation_peers=federation_peers
            )
            
        except Exception as e:
            logger.error(f"Metrics collection failed: {str(e)}")
            return HealthMetrics(
                memory_usage=0,
                cpu_usage=0,
                active_connections=0
            )

    def _determine_overall_status(self, component_statuses: Dict[str, ComponentStatus]) -> str:
        """Determine overall system health status."""
        if any(status == ComponentStatus.UNHEALTHY for status in component_statuses.values()):
            return "unhealthy"
        elif any(status == ComponentStatus.DEGRADED for status in component_statuses.values()):
            return "degraded"
        return "healthy"
