"""
Application Settings - Loaded from environment variables / .env file.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import os


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # -----------------------------------------------------------------------
    # Application
    # -----------------------------------------------------------------------
    APP_NAME: str = "Blockchain Evidence Preservation System"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production-use-a-long-random-string"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    ALLOWED_HOSTS: List[str] = ["*"]

    # -----------------------------------------------------------------------
    # Database
    # -----------------------------------------------------------------------
    DATABASE_URL: str = "postgresql+asyncpg://beps_user:beps_pass@localhost:5432/beps_db"
    DB_ECHO: bool = False

    # -----------------------------------------------------------------------
    # JWT
    # -----------------------------------------------------------------------
    JWT_SECRET_KEY: str = "jwt-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # -----------------------------------------------------------------------
    # Blockchain
    # -----------------------------------------------------------------------
    BLOCKCHAIN_RPC_URL: str = "http://localhost:8545"  # Hardhat / Ganache / Infura
    BLOCKCHAIN_PRIVATE_KEY: str = ""  # Deployer/operator wallet private key
    EVIDENCE_REGISTRY_CONTRACT_ADDRESS: str = "0x0000000000000000000000000000000000000000"
    CUSTODY_CONTRACT_ADDRESS: str = "0x0000000000000000000000000000000000000000"
    BLOCKCHAIN_CHAIN_ID: int = 1337  # Default: Hardhat local

    # -----------------------------------------------------------------------
    # Storage
    # -----------------------------------------------------------------------
    EVIDENCE_STORAGE_PATH: str = "/app/evidence_storage"
    MAX_FILE_SIZE_MB: int = 500

    # -----------------------------------------------------------------------
    # IPFS
    # -----------------------------------------------------------------------
    IPFS_ENABLED: bool = False
    IPFS_API_URL: str = "http://localhost:5001"

    # -----------------------------------------------------------------------
    # Security
    # -----------------------------------------------------------------------
    BCRYPT_ROUNDS: int = 12
    PASSWORD_MIN_LENGTH: int = 12


settings = Settings()
