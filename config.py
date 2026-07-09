"""
Configuration module for the Agentic AI Code Analyzer.

Centralizes all configuration, LLM initialization, and logging setup.
"""

import os
import logging
from dataclasses import dataclass, field
from dotenv import load_dotenv
from langchain_groq import ChatGroq

# ──────────────────────────────────────────────
# Environment
# ──────────────────────────────────────────────

load_dotenv()

# ──────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

logging.basicConfig(
    level=logging.WARNING,
    format=LOG_FORMAT,
    handlers=[
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger("code_analyzer")

# Suppress noisy third-party loggers
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("groq").setLevel(logging.ERROR)
logging.getLogger("httpcore").setLevel(logging.ERROR)

# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────

AVAILABLE_MODELS = {
    "llama-3.1-8b-instant": "LLaMA 3.1 8B (Fast)",
    "llama-3.3-70b-versatile": "LLaMA 3.3 70B (Powerful)",
    "gemma2-9b-it": "Gemma 2 9B",
    "mixtral-8x7b-32768": "Mixtral 8x7B",
}

DEFAULT_MODEL = "llama-3.1-8b-instant"


@dataclass
class AppConfig:
    """Application configuration with sensible defaults."""

    model_name: str = DEFAULT_MODEL
    temperature: float = 0.0
    max_tokens: int = 4096
    api_key: str = field(default_factory=lambda: os.getenv("GROQ_API_KEY", ""))

    def validate(self) -> tuple[bool, str]:
        """Validate the configuration. Returns (is_valid, error_message)."""
        if not self.api_key:
            return False, (
                "GROQ_API_KEY is not set. Please add it to your `.env` file "
                "or set it as an environment variable."
            )
        if self.model_name not in AVAILABLE_MODELS:
            return False, f"Unknown model: {self.model_name}"
        if not (0.0 <= self.temperature <= 2.0):
            return False, "Temperature must be between 0.0 and 2.0"
        return True, ""


def get_llm(config: AppConfig | None = None) -> ChatGroq:
    """
    Initialize and return a configured ChatGroq LLM instance.

    Args:
        config: Application configuration. Uses defaults if None.

    Returns:
        Configured ChatGroq instance.

    Raises:
        ValueError: If configuration is invalid.
    """
    if config is None:
        config = AppConfig()

    is_valid, error = config.validate()
    if not is_valid:
        raise ValueError(error)

    logger.info(
        "Initializing LLM: model=%s, temperature=%.1f, max_tokens=%d",
        config.model_name,
        config.temperature,
        config.max_tokens,
    )

    return ChatGroq(
        model=config.model_name,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        api_key=config.api_key,
    )
