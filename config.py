import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Base application configuration."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "phishguard-dev-secret-key-btech-2026")
    DATABASE_PATH = os.path.join(BASE_DIR, "instance", "phishguard.db")
    MODEL_DIR = os.path.join(BASE_DIR, "ml", "saved_models")
    MODEL_PATH = os.path.join(MODEL_DIR, "phishguard_rf_model.pkl")
    METRICS_PATH = os.path.join(MODEL_DIR, "model_metrics.json")
    RISK_THRESHOLD_SUSPICIOUS = 0.50
    DEBUG = False
    TESTING = False

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True
    DATABASE_PATH = os.path.join(BASE_DIR, "instance", "test_phishguard.db")
    MODEL_PATH = os.path.join(Config.MODEL_DIR, "test_model.pkl")

class ProductionConfig(Config):
    DEBUG = False

config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
