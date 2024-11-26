import aiofiles
import hashlib
import mimetypes
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import BinaryIO, Dict, Any
from PIL import Image
from io import BytesIO

from app.schemas import ComponentStatus
from app.logger import setup_logger

logger = setup_logger(__name__)

class StorageManager:
    def __init__(self):
        self.local_storage = Path("/data/local_cache")
        self.max_cache_age = timedelta(days=7)
        
        # Ensure local storage exists
        self.local_storage.mkdir(parents=True, exist_ok=True)

    async def store_media(self, file: BinaryIO, content_type: str, metadata: Dict[str, Any]) -> str:
        """Store media file with optimizations and versioning."""
        try:
            file_content = await self._read_file(file)
            file_hash = self._calculate_hash(file_content)
            
            # Generate optimized versions if it's an image
            versions = {}
            if content_type.startswith('image/'):
                versions = await self._create_image_versions(file_content)

            # Store original
            key = f"media/{file_hash}/{metadata.get('filename', 'original')}"
            await self._store_file(key, file_content, metadata)

            # Store versions
            for version_name, version_content in versions.items():
                version_key = f"media/{file_hash}/{version_name}"
                version_metadata = {
                    **metadata,
                    'version': version_name,
                    'original_key': key
                }
                await self._store_file(version_key, version_content, version_metadata)

            return key
        except Exception as e:
            logger.error(f"Failed to store media: {str(e)}")
            raise

    async def retrieve_media(self, key: str, version: str = None) -> bytes:
        """Retrieve media file with caching."""
        try:
            # Check local cache first
            cache_path = self.local_storage / key
            if cache_path.exists() and self._is_cache_valid(cache_path):
                async with aiofiles.open(cache_path, 'rb') as f:
                    return await f.read()

            if version:
                key = f"{os.path.dirname(key)}/{version}"

            # Load from storage
            storage_path = self.local_storage / key
            if not storage_path.exists():
                raise FileNotFoundError(f"File not found: {key}")

            async with aiofiles.open(storage_path, 'rb') as f:
                content = await f.read()
                
            # Cache the file locally
            await self._cache_file(key, content)
                
            return content
        except Exception as e:
            logger.error(f"Failed to retrieve media: {str(e)}")
            raise

    async def delete_media(self, key: str) -> bool:
        """Delete media file and all its versions."""
        try:
            # Get the directory containing all versions
            base_dir = os.path.dirname(key)
            storage_dir = self.local_storage / base_dir

            # Delete all files in the directory
            if storage_dir.exists():
                for file_path in storage_dir.glob("*"):
                    file_path.unlink()
                storage_dir.rmdir()

            # Remove from cache
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
            # Check write access
            test_file = self.local_storage / "health_check"
            test_file.touch()
            test_file.unlink()

            # Check storage space
            disk_usage = self.local_storage.stat().st_size
            total_space = os.statvfs(self.local_storage).f_blocks
            if disk_usage / total_space > 0.9:  # Over 90% used
                return ComponentStatus.DEGRADED

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
            
            # Thumbnail version (200x200)
            thumb = self._resize_image(image, (200, 200))
            thumb_buffer = BytesIO()
            thumb.save(thumb_buffer, format=image.format, optimize=True)
            versions['thumbnail'] = thumb_buffer.getvalue()
            
            # Medium version (800x800)
            medium = self._resize_image(image, (800, 800))
            medium_buffer = BytesIO()
            medium.save(medium_buffer, format=image.format, optimize=True)
            versions['medium'] = medium_buffer.getvalue()
            
            # Large version (1600x1600)
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

    async def _store_file(self, key: str, content: bytes, metadata: Dict[str, Any]):
        """Store file with metadata."""
        storage_path = self.local_storage / key
        storage_path.parent.mkdir(parents=True, exist_ok=True)

        # Store file
        async with aiofiles.open(storage_path, 'wb') as f:
            await f.write(content)

        # Store metadata
        meta_path = storage_path.parent / f"{storage_path.name}.meta"
        async with aiofiles.open(meta_path, 'w') as f:
            await f.write(str(metadata))

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

    async def _get_mime_type(self, filename: str) -> str:
        """Get MIME type from filename."""
        return mimetypes.guess_type(filename)[0] or 'application/octet-stream'
