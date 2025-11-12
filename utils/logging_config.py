# -*- coding: utf-8 -*-
"""
Logging Configuration
پیکربندی حرفه‌ای logging برای کل پروژه
"""

import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path


def setup_logging(app=None, log_level='INFO'):
    """
    Setup comprehensive logging for the application
    
    Creates:
        - logs/app.log: General application logs (rotating)
        - logs/error.log: Error logs only
        - Console output for development
    
    Args:
        app: Flask app instance (optional)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Create logs directory
    log_dir = Path(__file__).parent.parent / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    root_logger.handlers = []
    
    # Format for logs
    detailed_formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s.%(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # 1. Console Handler (for development)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if app and app.debug else logging.INFO)
    console_handler.setFormatter(simple_formatter)
    root_logger.addHandler(console_handler)
    
    # 2. File Handler - General Logs (rotating)
    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / 'app.log',
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(file_handler)
    
    # 3. File Handler - Error Logs Only
    error_handler = logging.handlers.RotatingFileHandler(
        log_dir / 'error.log',
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(error_handler)
    
    # 4. Daily Rotating Handler (for production)
    daily_handler = logging.handlers.TimedRotatingFileHandler(
        log_dir / 'daily.log',
        when='midnight',
        interval=1,
        backupCount=30,
        encoding='utf-8'
    )
    daily_handler.setLevel(logging.INFO)
    daily_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(daily_handler)
    
    # Configure SQLAlchemy logging (reduce noise)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    
    # Configure werkzeug logging (Flask's built-in server)
    logging.getLogger('werkzeug').setLevel(logging.INFO)
    
    # Log startup message
    root_logger.info("="*60)
    root_logger.info(f"Application logging initialized - Level: {log_level}")
    root_logger.info(f"Log directory: {log_dir.absolute()}")
    root_logger.info("="*60)
    
    if app:
        app.logger.setLevel(getattr(logging, log_level.upper()))
        app.logger.info("Flask application logger configured")
    
    return root_logger


def get_logger(name):
    """
    Get a logger instance for a specific module
    
    Usage:
        from utils.logging_config import get_logger
        logger = get_logger(__name__)
        logger.info("Something happened")
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        logging.Logger instance
    """
    return logging.getLogger(name)


class RequestLogger:
    """
    Middleware for logging HTTP requests
    
    Usage:
        from utils.logging_config import RequestLogger
        app.before_request(RequestLogger.log_request)
        app.after_request(RequestLogger.log_response)
    """
    
    @staticmethod
    def log_request():
        """Log incoming request details"""
        from flask import request
        logger = logging.getLogger('request')
        
        logger.info(
            f"Request: {request.method} {request.path} "
            f"from {request.remote_addr} "
            f"- UA: {request.user_agent.string[:50]}"
        )
    
    @staticmethod
    def log_response(response):
        """Log outgoing response details"""
        from flask import request
        logger = logging.getLogger('response')
        
        logger.info(
            f"Response: {request.method} {request.path} "
            f"- Status: {response.status_code} "
            f"- Size: {response.content_length or 0} bytes"
        )
        
        return response


# Performance logging
class PerformanceLogger:
    """
    Log slow database queries and route execution times
    """
    
    @staticmethod
    def log_slow_query(query, duration):
        """Log queries that take longer than threshold"""
        threshold = 1.0  # seconds
        if duration > threshold:
            logger = logging.getLogger('performance')
            logger.warning(
                f"Slow query detected ({duration:.2f}s): {query}"
            )
    
    @staticmethod
    def log_slow_route(route, duration):
        """Log routes that take longer than threshold"""
        threshold = 2.0  # seconds
        if duration > threshold:
            logger = logging.getLogger('performance')
            logger.warning(
                f"Slow route detected ({duration:.2f}s): {route}"
            )
