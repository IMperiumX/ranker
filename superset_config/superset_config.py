"""
Apache Superset Configuration for Real-Time Leaderboard Service
"""

import os

# Security
SECRET_KEY = os.environ.get("SUPERSET_SECRET_KEY", "your-superset-secret-key-change-in-production")
WTF_CSRF_ENABLED = True
WTF_CSRF_TIME_LIMIT = None

# Database Configuration
SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI",
    "postgresql://superset:superset_password@superset-db:5432/superset")

# Redis Configuration for Caching and Celery
REDIS_URL = os.environ.get("REDIS_URL", "redis://superset-redis:6379/0")

# Cache Configuration
CACHE_CONFIG = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_DEFAULT_TIMEOUT": 300,
    "CACHE_KEY_PREFIX": "superset_",
    "CACHE_REDIS_URL": REDIS_URL,
}

# Celery Configuration
class CeleryConfig:
    broker_url = REDIS_URL
    imports = ("superset.sql_lab", "superset.tasks")
    result_backend = REDIS_URL
    worker_prefetch_multiplier = 1
    task_acks_late = False
    task_annotations = {
        "sql_lab.get_sql_results": {
            "rate_limit": "100/s",
        },
        "email_reports.send": {
            "rate_limit": "1/s",
            "time_limit": 120,
            "soft_time_limit": 150,
            "bind": True,
        },
    }

CELERY_CONFIG = CeleryConfig

# Feature Flags
FEATURE_FLAGS = {
    "ALERTS_ATTACH_REPORTS": True,
    "ALLOW_ADHOC_SUBQUERY": True,
    "DASHBOARD_CROSS_FILTERS": True,
    "DASHBOARD_RBAC": True,
    "DATAPANEL_CLOSED_BY_DEFAULT": False,
    "DISABLE_DATASET_SOURCE_EDIT": False,
    "DRILL_TO_DETAIL": True,
    "DYNAMIC_PLUGINS": True,
    "ENABLE_ADVANCED_DATA_TYPES": True,
    "ENABLE_EXPLORE_DRAG_AND_DROP": True,
    "ENABLE_TEMPLATE_PROCESSING": True,
    "ESCAPE_MARKDOWN_HTML": True,
    "LISTVIEWS_DEFAULT_CARD_VIEW": True,
    "NATIVE_FILTER_DEFAULT_ROW_LIMIT": True,
    "THUMBNAILS": True,
    "VERSIONED_EXPORT": True,
}

# Security Settings
ENABLE_PROXY_FIX = True
PUBLIC_ROLE_LIKE_GAMMA = True

# Database Connections for Leaderboard Data
DATABASES_TO_EXPOSE = {
    "leaderboard_db": {
        "engine": "postgresql",
        "name": "Leaderboard Database",
        "url": "postgresql://ranker_user:password@postgres:5432/ranker",
    },
}

# Email Configuration (optional)
SMTP_HOST = os.environ.get("SMTP_HOST", "localhost")
SMTP_STARTTLS = True
SMTP_SSL = False
SMTP_USER = os.environ.get("SMTP_USER", "superset")
SMTP_PORT = 587
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SMTP_MAIL_FROM = os.environ.get("SMTP_MAIL_FROM", "superset@example.com")

# Webdriver Configuration for Screenshots
WEBDRIVER_BASEURL = "http://superset:8088/"
WEBDRIVER_BASEURL_USER_FRIENDLY = "http://localhost:8088/"

# SQL Lab Configuration
SQLLAB_CTAS_NO_LIMIT = True
SQLLAB_TIMEOUT = 300
SQLLAB_DEFAULT_DBID = None

# Dashboard Configuration
DASHBOARD_AUTO_REFRESH_MODE = "fetch"
DASHBOARD_AUTO_REFRESH_INTERVALS = [
    [0, "Don't refresh"],
    [10, "10 seconds"],
    [30, "30 seconds"],
    [60, "1 minute"],
    [300, "5 minutes"],
    [1800, "30 minutes"],
    [3600, "1 hour"],
]

# Chart Configuration
DEFAULT_FEATURE_FLAG_VALUE = True
PREVENT_UNSAFE_DB_CONNECTIONS = False

# Custom CSS/JS
EXTRA_CATEGORICAL_COLOR_SCHEMES = [
    {
        "id": "leaderboard_colors",
        "description": "Leaderboard Color Scheme",
        "label": "Leaderboard Colors",
        "colors": [
            "#1f77b4",  # Blue
            "#ff7f0e",  # Orange
            "#2ca02c",  # Green
            "#d62728",  # Red
            "#9467bd",  # Purple
            "#8c564b",  # Brown
            "#e377c2",  # Pink
            "#7f7f7f",  # Gray
            "#bcbd22",  # Olive
            "#17becf",  # Cyan
        ],
    },
]

# Row Level Security
ROW_LEVEL_SECURITY_FILTERS = {}

# Import additional configurations if available
try:
    from superset_config_local import *  # noqa
except ImportError:
    pass
