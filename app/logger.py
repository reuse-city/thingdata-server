import logging
import logging.handlers
import sys
import gzip
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
import json

# Constants
LOGS_DIR = Path("/logs")
MAX_BYTES = 10 * 1024 * 1024  # 10MB
BACKUP_COUNT = 5
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - [%(correlation_id)s] %(message)s'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG')

class GzipRotatingFileHandler(logging.handlers.RotatingFileHandler):
    """Custom handler that compresses rotated logs."""
    
    def doRollover(self):
        if self.stream:
            self.stream.close()
            self.stream = None
        if self.backupCount > 0:
            for i in range(self.backupCount - 1, 0, -1):
                sfn = self.rotation_filename("%s.%d.gz" % (self.baseFilename, i))
                dfn = self.rotation_filename("%s.%d.gz" % (self.baseFilename, i + 1))
                if os.path.exists(sfn):
                    if os.path.exists(dfn):
                        os.remove(dfn)
                    os.rename(sfn, dfn)
            dfn = self.rotation_filename(self.baseFilename + ".1.gz")
            if os.path.exists(dfn):
                os.remove(dfn)
            # Compress the current log file
            with open(self.baseFilename, 'rb') as f_in:
                with gzip.open(dfn, 'wb') as f_out:
                    f_out.writelines(f_in)
        if not self.delay:
            self.stream = self._open()

class ContextFilter(logging.Filter):
    """Adds correlation ID to log records."""
    
    def __init__(self):
        super().__init__()
        self.correlation_id = None

    def filter(self, record):
        record.correlation_id = getattr(self, 'correlation_id', 'no-correlation-id')
        return True

class JSONFormatter(logging.Formatter):
    """Formats log records as JSON."""
    
    def format(self, record):
        log_obj = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "correlation_id": record.correlation_id,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        if record.exc_info:
            log_obj['exception'] = self.formatException(record.exc_info)
            
        if hasattr(record, 'stack_info'):
            log_obj['stack_info'] = self.formatStack(record.stack_info)
            
        return json.dumps(log_obj)

def setup_logger(name: str, correlation_id: Optional[str] = None) -> logging.Logger:
    """
    Set up a logger with both file and console handlers, including rotation and compression.
    
    Args:
        name: Logger name (usually __name__ from the calling module)
        correlation_id: Optional correlation ID for request tracking
        
    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logs directory if it doesn't exist
    LOGS_DIR.mkdir(exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # Add correlation ID filter
    context_filter = ContextFilter()
    if correlation_id:
        context_filter.correlation_id = correlation_id
    logger.addFilter(context_filter)

    # Create formatters
    standard_formatter = logging.Formatter(LOG_FORMAT)
    json_formatter = JSONFormatter()

    # Main log file handler with rotation and compression
    main_log_file = LOGS_DIR / "thingdata.log"
    file_handler = GzipRotatingFileHandler(
        main_log_file,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT
    )
    file_handler.setFormatter(json_formatter)
    file_handler.setLevel(LOG_LEVEL)

    # Error log file handler
    error_log_file = LOGS_DIR / "thingdata-errors.log"
    error_handler = GzipRotatingFileHandler(
        error_log_file,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT
    )
    error_handler.setFormatter(json_formatter)
    error_handler.setLevel(logging.ERROR)

    # Development log handler (pretty-printed console output)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(standard_formatter)
    console_handler.setLevel(LOG_LEVEL)

    # Add all handlers
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)
    logger.addHandler(console_handler)

    # Development mode extras
    if os.getenv('ENVIRONMENT') == 'development':
        # Add debug log file
        debug_log_file = LOGS_DIR / "thingdata-debug.log"
        debug_handler = GzipRotatingFileHandler(
            debug_log_file,
            maxBytes=MAX_BYTES,
            backupCount=BACKUP_COUNT
        )
        debug_handler.setFormatter(json_formatter)
        debug_handler.setLevel(logging.DEBUG)
        logger.addHandler(debug_handler)

        # SQL query logging
        sql_log_file = LOGS_DIR / "thingdata-sql.log"
        sql_handler = GzipRotatingFileHandler(
            sql_log_file,
            maxBytes=MAX_BYTES,
            backupCount=BACKUP_COUNT
        )
        sql_handler.setFormatter(json_formatter)
        sql_handler.setLevel(logging.DEBUG)
        
        sql_logger = logging.getLogger('sqlalchemy.engine')
        sql_logger.setLevel(logging.DEBUG)
        sql_logger.addHandler(sql_handler)

    return logger

class RequestCorrelationMiddleware:
    """Middleware to add correlation IDs to requests and log entries."""
    
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        correlation_id = f"req-{datetime.utcnow().timestamp()}"
        logger = setup_logger(__name__, correlation_id)
        
        logger.info(f"Request received: {scope['method']} {scope['path']}")
        
        try:
            await self.app(scope, receive, send)
            logger.info(f"Request completed: {scope['method']} {scope['path']}")
        except Exception as e:
            logger.error(f"Request failed: {scope['method']} {scope['path']}", exc_info=True)
            raise
