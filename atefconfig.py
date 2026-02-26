"""
ATEF Configuration Management System
Handles configuration loading, validation, and environment management with robust error handling.
"""

import os
import sys
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from pathlib import Path
import logging
from enum import Enum

# Firebase imports
import firebase_admin
from firebase_admin import credentials, firestore, auth
from google.cloud.firestore_v1 import Client as FirestoreClient

# Third-party imports
import yaml
from pydantic import BaseModel, Field, validator
import dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


class TradingMode(str, Enum):
    """Trading operation modes"""
    BACKTEST = "backtest"
    PAPER = "paper"
    LIVE = "live"


class ExchangeType(str, Enum):
    """Supported exchange types"""
    BINANCE = "binance"
    COINBASE = "coinbase"
    KRAKEN = "kraken"
    FTX = "ftx"


@dataclass
class ExchangeConfig:
    """Exchange configuration"""
    name: str
    api_key: str = ""
    api_secret: str = ""
    passphrase: str = ""
    enabled: bool = False
    timeout: int = 30000
    sandbox: bool = True
    type: ExchangeType = ExchangeType.BINANCE
    rate_limit: int = 10
    max_retries: int = 3
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        if not self.name:
            raise ValueError("Exchange name cannot be empty")
        if self.timeout < 1000:
            raise ValueError(f"Timeout too low: {self.timeout}ms")
        if self.rate_limit < 1:
            raise ValueError(f"Rate limit too low: {self.rate_limit}")


@dataclass
class StrategyConfig:
    """Strategy configuration"""
    name: str
    version: str = "1.0.0"
    enabled: bool = True
    parameters: Dict[str, Any] = field(default_factory=dict)
    entry_conditions: List[str] = field(default_factory=list)
    exit_conditions: List[str] = field(default_factory=list)
    risk_per_trade: float = 0.02
    max_open_positions: int = 5
    
    def __post_init__(self):
        """Validate strategy configuration"""
        if self.risk_per_trade <= 0 or self.risk_per_trade > 0.1:
            raise ValueError(f"Risk per trade must be between 0 and 0.1, got {self.risk_per_trade}")
        if self.max_open_positions < 1:
            raise ValueError(f"Max open positions must be positive, got {self.max_open_positions}")


@dataclass
class RiskConfig:
    """Risk management configuration"""
    max_daily_loss: float = 0.05
    max_portfolio_risk: float = 0.2
    max_position_size: float = 0.1
    stop_loss_enabled: bool = True
    trailing_stop_enabled: bool = False
    max_leverage: float = 3.0
    blacklist: List[str] = field(default_factory=list)
    whitelist: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate risk configuration"""
        if self.max_daily_loss <= 0 or self.max_daily_loss > 0.5:
            raise ValueError(f"Max daily loss must be between 0 and 0.5, got {self.max_daily_loss}")
        if self.max_leverage < 1 or self.max_leverage > 100:
            raise ValueError(f"Max leverage must be between 1 and 100, got {self.max_leverage}")


@dataclass
class FirebaseConfig:
    """Firebase configuration