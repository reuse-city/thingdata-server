import aiohttp
import asyncio
import jwt
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
from sqlalchemy.orm import Session
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app.models import Instance, Thing, Story, Relationship
from app.schemas import ComponentStatus
from app.logger import setup_logger

logger = setup_logger(__name__)

class FederationManager:
    def __init__(self):
        self.instance_key = None
        self.known_instances: Dict[str, Instance] = {}
        self.sync_queues: Dict[str, asyncio.Queue] = {}
        self.active_syncs: Dict[str, asyncio.Task] = {}
        self.retry_delays = [5, 15, 30, 60, 120]  # seconds

    async def initialize(self):
        """Initialize federation system."""
        logger.info("Initializing federation system")
        self.instance_key = await self._generate_instance_key()
        await self._start_sync_workers()
        await self._restore_pending_syncs()

    async def _generate_instance_key(self) -> rsa.RSAPrivateKey:
        """Generate RSA key pair for instance authentication."""
        return rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )

    async def _start_sync_workers(self):
        """Start background sync workers for each known instance."""
        for instance in self.known_instances.values():
            self.sync_queues[instance.uri] = asyncio.Queue()
            self.active_syncs[instance.uri] = asyncio.create_task(
                self._sync_worker(instance.uri)
            )

    async def _sync_worker(self, instance_uri: str):
        """Background worker for handling federation events."""
        queue = self.sync_queues[instance_uri]
        while True:
            try:
                event = await queue.get()
                for attempt, delay in enumerate(self.retry_delays):
                    try:
                        await self._process_federation_event(event)
                        break
                    except Exception as e:
                        logger.error(f"Sync error for {instance_uri}: {str(e)}")
                        if attempt < len(self.retry_delays) - 1:
                            await asyncio.sleep(delay)
                        else:
                            await self._handle_sync_failure(event)
            except Exception as e:
                logger.error(f"Sync worker error: {str(e)}")
                await asyncio.sleep(5)

    async def _process_federation_event(self, event: dict):
        """Process a federation event."""
        instance = self.known_instances[event["target_instance"]]
        
        async with aiohttp.ClientSession() as session:
            headers = await self._prepare_auth_headers(instance)
            endpoint = instance.endpoints[event["event_type"]]
            
            async with session.post(endpoint, headers=headers, json=event) as response:
                if response.status not in (200, 201):
                    raise Exception(f"Federation request failed: {response.status}")
                
                return await response.json()

    async def _prepare_auth_headers(self, instance: Instance) -> Dict[str, str]:
        """Prepare authentication headers for federation requests."""
        now = datetime.utcnow()
        payload = {
            'iss': self.instance_uri,
            'sub': instance.uri,
            'iat': now.timestamp(),
            'exp': (now + timedelta(minutes=5)).timestamp()
        }
        
        token = jwt.encode(payload, self.instance_key, algorithm='RS256')
        
        return {
            'Authorization': f'Bearer {token}',
            'X-Federation-Instance': self.instance_uri
        }

    async def connect_instance(self, instance_data: dict, db: Session) -> Instance:
        """Connect to another ThingData instance."""
        try:
            # Verify instance authenticity
            await self._verify_instance(instance_data)
            
            instance = Instance(
                id=instance_data['id'],
                uri=instance_data['uri'],
                name=instance_data['name'],
                type=instance_data['type'],
                endpoints=instance_data['endpoints'],
                capabilities=instance_data.get('capabilities', []),
                languages=instance_data.get('languages', []),
                trust_status='verified',
                public_key=instance_data['public_key'],
                last_seen=datetime.utcnow(),
                sync_status={
                    'last_sync': None,
                    'sync_count': 0,
                    'failed_syncs': 0
                }
            )
            
            if db:
                db.add(instance)
                db.commit()

            # Initialize sync queue
            self.sync_queues[instance.uri] = asyncio.Queue()
            self.active_syncs[instance.uri] = asyncio.create_task(
                self._sync_worker(instance.uri)
            )

            # Start initial sync
            await self._initial_sync(instance)
            
            return instance
        except Exception as e:
            logger.error(f"Failed to connect instance: {str(e)}")
            if db:
                db.rollback()
            raise

    async def check_health(self) -> ComponentStatus:
        """Check federation network health."""
        try:
            active_instances = 0
            total_instances = len(self.known_instances)
            
            for instance in self.known_instances.values():
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(f"{instance.endpoints['health']}") as response:
                            if response.status == 200:
                                active_instances += 1
                except:
                    continue
            
            if active_instances == total_instances:
                return ComponentStatus.HEALTHY
            elif active_instances > 0:
                return ComponentStatus.DEGRADED
            else:
                return ComponentStatus.UNHEALTHY
                
        except Exception as e:
            logger.error(f"Federation health check failed: {str(e)}")
            return ComponentStatus.UNHEALTHY

    async def handle_webfinger(self):
        """Handle WebFinger discovery requests."""
        return {
            "subject": self.instance_uri,
            "links": [
                {
                    "rel": "self",
                    "href": self.instance_uri,
                    "type": "application/activity+json"
                },
                {
                    "rel": "service",
                    "href": f"{self.instance_uri}/api/v1",
                    "type": "application/json"
                }
            ]
        }

    async def shutdown(self):
        """Gracefully shutdown federation system."""
        logger.info("Shutting down federation system")
        
        # Cancel all active sync tasks
        for task in self.active_syncs.values():
            task.cancel()
            
        # Wait for tasks to complete
        await asyncio.gather(*self.active_syncs.values(), return_exceptions=True)

    async def _restore_pending_syncs(self):
        """Restore any pending sync operations from database."""
        # Implementation here
        pass

    async def _handle_sync_failure(self, event: dict):
        """Handle a sync failure after all retries."""
        # Implementation here
        pass
