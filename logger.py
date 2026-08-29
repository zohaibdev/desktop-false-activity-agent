"""
Logging module for the AI Desktop Automation Agent.
Provides both console and file logging with timestamps.
"""

import logging
import os
import sys
from datetime import datetime
from typing import Optional
from logging.handlers import RotatingFileHandler


class AgentLogger:
    """
    Custom logger for the automation agent.
    Supports both console and file logging with rotation.
    """
    
    _instance: Optional['AgentLogger'] = None
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern to ensure single logger instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(
        self,
        name: str = "AutomationAgent",
        log_level: str = "INFO",
        log_to_file: bool = True,
        log_to_console: bool = True,
        log_file_path: str = "agent_log.txt",
        max_log_size: int = 10 * 1024 * 1024
    ):
        """
        Initialize the logger.
        
        Args:
            name: Logger name
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
            log_to_file: Whether to log to file
            log_to_console: Whether to log to console
            log_file_path: Path to log file
            max_log_size: Maximum log file size before rotation
        """
        if self._initialized:
            return
        
        self._initialized = True
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        self.logger.handlers = []  # Clear existing handlers
        
        # Log format
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        if log_to_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # File handler with rotation
        if log_to_file:
            try:
                file_handler = RotatingFileHandler(
                    log_file_path,
                    maxBytes=max_log_size,
                    backupCount=3,
                    encoding='utf-8'
                )
                file_handler.setFormatter(formatter)
                self.logger.addHandler(file_handler)
            except Exception as e:
                self.logger.warning(f"Could not create file handler: {e}")
    
    def debug(self, message: str) -> None:
        """Log debug message."""
        self.logger.debug(message)
    
    def info(self, message: str) -> None:
        """Log info message."""
        self.logger.info(message)
    
    def warning(self, message: str) -> None:
        """Log warning message."""
        self.logger.warning(message)
    
    def error(self, message: str) -> None:
        """Log error message."""
        self.logger.error(message)
    
    def action(self, action_type: str, details: str = "") -> None:
        """Log an action performed by the agent."""
        msg = f"ACTION: {action_type}"
        if details:
            msg += f" | {details}"
        self.logger.info(msg)
    
    def decision(self, decision: str, reason: str = "") -> None:
        """Log a decision made by the AI engine."""
        msg = f"DECISION: {decision}"
        if reason:
            msg += f" | Reason: {reason}"
        self.logger.info(msg)
    
    def state(self, state: str) -> None:
        """Log agent state change."""
        self.logger.info(f"STATE: {state}")
    
    def separator(self) -> None:
        """Log a visual separator."""
        self.logger.info("-" * 60)


# Global logger instance
_logger: Optional[AgentLogger] = None


def get_logger() -> AgentLogger:
    """Get or create the global logger instance."""
    global _logger
    if _logger is None:
        _logger = AgentLogger()
    return _logger


def init_logger(
    log_level: str = "INFO",
    log_to_file: bool = True,
    log_to_console: bool = True,
    log_file_path: str = "agent_log.txt"
) -> AgentLogger:
    """
    Initialize the global logger with custom settings.
    
    Args:
        log_level: Logging level
        log_to_file: Whether to log to file
        log_to_console: Whether to log to console
        log_file_path: Path to log file
    
    Returns:
        Configured AgentLogger instance
    """
    global _logger
    _logger = AgentLogger(
        log_level=log_level,
        log_to_file=log_to_file,
        log_to_console=log_to_console,
        log_file_path=log_file_path
    )
    return _logger
