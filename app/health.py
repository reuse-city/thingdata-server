from typing import Dict, Optional
import psutil
from datetime import datetime
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
        """Basic system health check."""
        try:
            # Use cached response if available and recent
            if not force and self._health_cache and self.last_check:
                if (datetime.utcnow() - self.last_check).seconds < self.cache_duration:
                    return self._health_cache

            # Check database
            db_status = await self._check_database()
            metrics = await self._collect_metrics()

            health_response = HealthResponse(
                status="healthy" if db_status == ComponentStatus.HEALTHY else "unhealthy",
                timestamp=datetime.utcnow().isoformat(),
                version="0.1.2",
                components={
                    "database": db_status,
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
            pool_info = db.execute(
                text("""
                    SELECT count(*) as connections
                    FROM pg_stat_activity
                    WHERE datname = current_database()
                """)
            ).scalar()
            
            if pool_info > 100:  # Simplified check
                return ComponentStatus.DEGRADED
                
            return ComponentStatus.HEALTHY
            
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return ComponentStatus.UNHEALTHY

    async def _collect_metrics(self) -> HealthMetrics:
        """Collect basic system metrics."""
        try:
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=1)
            
            return HealthMetrics(
                memory_usage=memory.percent,
                cpu_usage=cpu_percent,
                active_connections=0,  # Placeholder for future implementation
                storage_usage=psutil.disk_usage('/').percent,
                federation_peers=0  # Placeholder for future implementation
            )
            
        except Exception as e:
            logger.error(f"Metrics collection failed: {str(e)}")
            return HealthMetrics(
                memory_usage=0,
                cpu_usage=0,
                active_connections=0,
                storage_usage=0,
                federation_peers=0
            )