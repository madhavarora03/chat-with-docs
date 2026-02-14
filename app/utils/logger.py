"""
Logger Utility Module
=====================
Production-ready logging configuration for FastAPI applications.

This module provides:
- YAML-based logging configuration using Python's dictConfig
- Consistent formatting for application and Uvicorn logs
- Environment variable overrides for log levels
- Optional file logging support

Usage:
    # Initialize early in your application (before FastAPI app creation)
    from app.utils.logger import setup_logging, get_logger

    setup_logging()

    # Get a logger for your module
    logger = get_logger(__name__)
    logger.info("Application started")
"""

import logging
import logging.config
from pathlib import Path

import yaml

from app.core.config import get_settings

# =============================================================================
# CONFIGURATION
# =============================================================================

# Default path for logging config file
DEFAULT_CONFIG_PATH = "logging.yaml"


def _load_yaml_config(config_path: str) -> dict:
    """
    Load logging configuration from a YAML file.

    Args:
        config_path: Path to the YAML configuration file

    Returns:
        Dictionary containing the logging configuration

    Raises:
        FileNotFoundError: If the config file doesn't exist
        yaml.YAMLError: If the YAML is invalid
    """
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def _apply_settings_overrides(config: dict) -> dict:
    """
    Apply settings overrides to the logging configuration.

    Uses settings from app.core.config for:
        - LOG_LEVEL: Override root and application log levels
        - LOG_FILE_ENABLED: Enable/disable file logging
        - LOG_FILE_PATH: Custom path for the log file

    Args:
        config: Base logging configuration dictionary

    Returns:
        Modified configuration with settings applied
    """
    settings = get_settings()

    # Override log level from settings
    log_level = settings.LOG_LEVEL.upper()

    # Update root logger level
    if "root" in config:
        config["root"]["level"] = log_level

    # Update application logger level
    if "loggers" in config and "app" in config["loggers"]:
        config["loggers"]["app"]["level"] = log_level

    # Update uvicorn loggers if level is DEBUG
    if log_level == "DEBUG" and "loggers" in config:
        for logger_name in ["uvicorn", "uvicorn.error", "uvicorn.access"]:
            if logger_name in config["loggers"]:
                config["loggers"][logger_name]["level"] = "DEBUG"

    # Handle file logging configuration
    if settings.LOG_FILE_ENABLED:
        # Ensure logs directory exists
        log_file_path = settings.LOG_FILE_PATH
        log_dir = Path(log_file_path).parent
        log_dir.mkdir(parents=True, exist_ok=True)

        # Update file handler path
        if "handlers" in config and "file" in config["handlers"]:
            config["handlers"]["file"]["filename"] = log_file_path

        # Add file handler to relevant loggers
        for logger_key in ["root", "loggers"]:
            if logger_key == "root" and "root" in config:
                if "file" not in config["root"].get("handlers", []):
                    config["root"]["handlers"] = config["root"].get("handlers", []) + [
                        "file"
                    ]
            elif logger_key == "loggers" and "loggers" in config:
                for logger_name in ["app"]:
                    if logger_name in config["loggers"]:
                        handlers = config["loggers"][logger_name].get("handlers", [])
                        if "file" not in handlers:
                            config["loggers"][logger_name]["handlers"] = handlers + [
                                "file"
                            ]
    else:
        # Remove file handler if not enabled to avoid errors
        if "handlers" in config and "file" in config["handlers"]:
            del config["handlers"]["file"]

    return config


def setup_logging(config_path: str | None = None) -> None:
    """
    Initialize the logging system with configuration from YAML file.

    This function should be called early in your application startup,
    before creating the FastAPI app instance. It configures both
    application loggers and Uvicorn's loggers for consistent formatting.

    Args:
        config_path: Path to the logging config file, or None for default.
                    Defaults to 'logging.yaml' in project root.

    Example:
        # In main.py, before FastAPI app creation
        from app.utils.logger import setup_logging

        setup_logging()

        app = FastAPI(...)
    """
    # Determine config file path
    if config_path is None:
        config_path = DEFAULT_CONFIG_PATH

    # Resolve to absolute path relative to project root
    if not Path(config_path).is_absolute():
        # Assume config is relative to the project root (where main.py is)
        project_root = Path(__file__).parent.parent.parent
        config_path = str(project_root / config_path)

    settings = get_settings()

    try:
        # Load base configuration
        config = _load_yaml_config(config_path)

        # Apply settings overrides
        config = _apply_settings_overrides(config)

        # Apply configuration to Python's logging system
        logging.config.dictConfig(config)

        # Log successful initialization
        logger = logging.getLogger("app")
        logger.debug(f"Logging configured from: {config_path}")

    except FileNotFoundError:
        # Fall back to basic configuration if YAML file not found
        logging.basicConfig(
            level=settings.LOG_LEVEL,
            format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        logging.warning(
            f"Logging config file not found: {config_path}. Using basic config."
        )

    except Exception as e:
        # Fall back to basic configuration on any error
        logging.basicConfig(
            level=settings.LOG_LEVEL,
            format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        logging.error(f"Failed to load logging config: {e}. Using basic config.")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.

    For application code, prefix with 'app.' to use the app logger hierarchy.
    This ensures your logs use the configured handlers and formatters.

    Args:
        name: Logger name. Use __name__ for automatic module-based naming.

    Returns:
        Configured logger instance

    Example:
        # In any module
        from app.utils.logger import get_logger

        logger = get_logger(__name__)
        logger.info("Processing request")
        logger.error("Something went wrong", exc_info=True)
    """
    # If the name starts with 'app', use it directly
    # Otherwise, prefix with 'app.' for consistent hierarchy
    if name.startswith("app"):
        return logging.getLogger(name)
    return logging.getLogger(f"app.{name}")


# =============================================================================
# UVICORN INTEGRATION
# =============================================================================


def get_uvicorn_log_config() -> dict | None:
    """
    Get logging configuration for Uvicorn's log_config parameter.

    When running with Uvicorn programmatically, pass this to ensure
    Uvicorn uses the same logging configuration as the application.

    Returns:
        Dictionary suitable for uvicorn.run(log_config=...)

    Example:
        import uvicorn
        from app.utils.logger import setup_logging, get_uvicorn_log_config

        setup_logging()

        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            log_config=get_uvicorn_log_config(),
        )
    """
    # Determine config file path
    config_path = DEFAULT_CONFIG_PATH

    # Resolve to absolute path
    if not Path(config_path).is_absolute():
        project_root = Path(__file__).parent.parent.parent
        config_path = str(project_root / config_path)

    try:
        config = _load_yaml_config(config_path)
        config = _apply_settings_overrides(config)
        return config
    except Exception:
        # Return None to use Uvicorn's default config
        return None
