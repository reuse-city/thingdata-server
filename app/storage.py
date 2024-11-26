import boto3
import aioboto3
from botocore.exceptions import ClientError
from typing import Optional, List, BinaryIO, Dict, Any
import hashlib
import mimetypes
import os
from datetime import datetime, timedelta
from pathlib import Path
import aiofiles
from PIL import Image
from io import BytesIO

from app.logger import setup_logger
from app.schemas import ComponentStatus

logger = setup_logger(__name__)

class StorageManager:
    def __init__(self):
        self.s3_endpoint = os.getenv('S3_ENDPOINT', 'http://minio:9000')
        self.s3_access_key = os.getenv('S3_ACCESS_KEY', 'minioadmin')
        self.s3_secret_key = os.getenv('S3_SECRET_KEY', 'minioadmin')
        self.bucket_name = os.getenv('S3_BUCKET', 'thingdata')
        self.local_storage = Path("/data/local_cache")
        self.max_cache_age = timedelta(days=7)
        
        # Ensure local storage exists
        self.local_storage.mkdir(parents=True, exist_ok=True)
        
        # Initialize S3 client
        self.s3_client = boto3.client(
            's3',
            endpoint_url=self.s3_endpoint,
            aws_access_key_id=self.s3_access_key,
            aws_secret_access_key=self.s3_secret_key
        )
        
        # Initialize async S3 session
        self.async_session = aioboto3.Session()

    async def store_media(self, file: BinaryIO, content_type: str, metadata: Dict[str, Any]) -> str:
        """Store media file with optimizations and versioning."""
        try:
            file_content = await self._read_file(file)
            file_hash = self._calculate_hash(file_content)
            
            # Generate optimized versions if it's an image
            versions = {}
            if content_type.startswith('image/'):
                versions = await self._create_image_versions(file_content)

            # Store original and versions
            async with self.async_session.client(
                's3',
                endpoint_url=self.s3_endpoint,
                aws_access_key_id=self.s3_access_key,
                aws_secret_access_key=self.s3_secret_key
            ) as s3:
                # Store original
                key = f"media/{file_hash}/{metadata.get('filename', 'original')}"
                await s3.put_object(
                    Bucket=self.bucket_name,
                    Key=key,
                    Body=file_content,
                    ContentType=content_type,
                    Metadata={
                        **metadata,
                        'original_name': metadata.get('filename', ''),
                        'content_type': content_type,
                        'created_at': datetime.utcnow().isoformat()
                    }
                )

                # Store versions
                for version_name, version_content in versions.items():
                    version_key = f"media/{file_hash}/{version_name}"
                    await s3.put_object(
                        Bucket=self.bucket_name,
                        Key=version_key,
                        Body=version_content,
                        ContentType=content_type,
                        Metadata={
                            **metadata,
                            'version': version_name,
                            'original_key': key
                        }
                    )

            return key
        except Exception as e:
            logger.error(f"Failed to store media: {str(e)}")
            raise

    async def retrieve_media(self, key: str, version: Optional[str] = None) -> BinaryIO:
        """Retrieve media file with caching."""
        try:
            # Check local cache first
            cache_path = self.local_storage / key
            if cache_path.exists() and self._is_cache_valid(cache_path):
                async with aiofiles.open(cache_path, 'rb') as f:
                    return await f.read()

            # Retrieve from S3
            async with self.async_session.client(
                's3',
                endpoint_url=self.s3_endpoint,
                aws_access_key_id=self.s3_access_key,
                aws_secret_access_key=self.s3_secret_key
            ) as s3:
                if version:
                    key = f"{os.path.dirname(key)}/{version}"
                
                response = await s3.get_object(
                    Bucket=self.bucket_name,
                    Key=key
                )
                
                content = await response['Body'].read()
                
                # Cache the file locally
                await self._cache_file(key, content)
                
                return content
        except Exception as e:
            logger.error(f"Failed to retrieve media: {str(e)}")
            raise

    async def delete_media(self, key: str) -> bool:
        """Delete media file and all its versions."""
        try:
            async with self.async_session.client(
                's3',
                endpoint_url=self.s3_endpoint,
                aws_access_key_id=self.s3_access_key,
                aws_secret_access_key=self.s3_secret_key
            ) as s3:
                # List all versions
                response = await s3.list_objects_v2(
                    Bucket=self.bucket_name,
                    Prefix=os.path.dirname(key)
                )
                
                # Delete all versions
                for obj in response.get('Contents', []):
                    await s3.delete_object(
                        Bucket=self.bucket_name,
                        Key=obj['Key']
                    )
                
                # Remove from local cache
                cache_path = self.local_storage / key
                if cache_path.exists():
                    cache_path.unlink()
                
                return True
        except Exception as e:
            logger.error(f"Failed to delete media: {str(e)}")
            return False

    async def check_health(self) -> ComponentStatus:
        """Check storage system health."""
        try:
            # Check S3 connectivity
            async with self.async_session.client(
                's3',
                endpoint_url=self.s3_endpoint,
                aws_access_key_id=self.s3_access_key,
                aws_secret_access_key=self.s3_secret_key
            ) as s3:
                await s3.head_bucket(Bucket=self.bucket_name)
            
            # Check local storage
            test_file = self.local_storage / "health_check"
            test_file.touch()
            test_file.unlink()
            
            return ComponentStatus.HEALTHY
        except Exception as e:
            logger.error(f"Storage health check failed: {str(e)}")
            return ComponentStatus.UNHEALTHY

    async def cleanup_cache(self):
        """Clean up expired cache files."""
        try:
            current_time = datetime.utcnow()
            for file_path in self.local_storage.rglob("*"):
                if file_path.is_file() and not self._is_cache_valid(file_path):
                    file_path.unlink()
        except Exception as e:
            logger.error(f"Cache cleanup failed: {str(e)}")

    async def _create_image_versions(self, content: bytes) -> Dict[str, bytes]:
        """Create optimized versions of image."""
        versions = {}
        try:
            image = Image.open(BytesIO(content))
            
            # Thumbnail version
            thumb = self._resize_image(image, (200, 200))
            thumb_buffer = BytesIO()
            thumb.save(thumb_buffer, format=image.format, optimize=True)
            versions['thumbnail'] = thumb_buffer.getvalue()
            
            # Medium version
            medium = self._resize_image(image, (800, 800))
            medium_buffer = BytesIO()
            medium.save(medium_buffer, format=image.format, optimize=True)
            versions['medium'] = medium_buffer.getvalue()
            
            # Large version
            large = self._resize_image(image, (1600, 1600))
            large_buffer = BytesIO()
            large.save(large_buffer, format=image.format, optimize=True)
            versions['large'] = large_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Failed to create image versions: {str(e)}")
            
        return versions

    def _resize_image(self, image: Image.Image, size: tuple) -> Image.Image:
        """Resize image maintaining aspect ratio."""
        image.thumbnail(size, Image.LANCZOS)
        return image

    async def _cache_file(self, key: str, content: bytes):
        """Cache file locally."""
        cache_path = self.local_storage / key
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        
        async with aiofiles.open(cache_path, 'wb') as f:
            await f.write(content)

    def _is_cache_valid(self, path: Path) -> bool:
        """Check if cached file is still valid."""
        return datetime.fromtimestamp(path.stat().st_mtime) > (
            datetime.utcnow() - self.max_cache_age
        )

    def _calculate_hash(self, content: bytes) -> str:
        """Calculate SHA-256 hash of content."""
        return hashlib.sha256(content).hexdigest()

    async def _read_file(self, file: BinaryIO) -> bytes:
        """Read file content."""
        return file.read()
