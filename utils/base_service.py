"""
Base service class with circuit breaker pattern and retry logic for API integrations.
Implements resilience patterns for external API calls.
"""
import time
import logging
from enum import Enum
from typing import Any, Callable, Optional
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Circuit breaker implementation for API resilience."""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN - service unavailable")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        return (
            self.last_failure_time and
            time.time() - self.last_failure_time >= self.recovery_timeout
        )
    
    def _on_success(self):
        """Handle successful call."""
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN


def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0, backoff_factor: float = 2.0):
    """Decorator for exponential backoff retry logic."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(f"Function {func.__name__} failed after {max_retries + 1} attempts: {e}")
                        raise e
                    
                    delay = base_delay * (backoff_factor ** attempt)
                    logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {delay}s...")
                    time.sleep(delay)
            
            raise last_exception
        return wrapper
    return decorator


class BaseService:
    """Base class for all API service integrations."""
    
    def __init__(self, service_name: str, api_key: Optional[str] = None):
        self.service_name = service_name
        self.api_key = api_key
        self.circuit_breaker = CircuitBreaker()
        self.logger = logging.getLogger(f"{__name__}.{service_name}")
    
    def _make_request(self, func: Callable, *args, **kwargs) -> Any:
        """Make API request with circuit breaker protection."""
        try:
            return self.circuit_breaker.call(func, *args, **kwargs)
        except Exception as e:
            self.logger.error(f"{self.service_name} API call failed: {e}")
            return self._handle_fallback(e)
    
    def _handle_fallback(self, error: Exception) -> Any:
        """Handle fallback when API is unavailable. Override in subclasses."""
        self.logger.warning(f"{self.service_name} falling back to default behavior due to: {error}")
        return None
    
    def is_available(self) -> bool:
        """Check if service is currently available."""
        return self.circuit_breaker.state != CircuitState.OPEN
    
    def get_status(self) -> dict:
        """Get current service status."""
        return {
            "service": self.service_name,
            "state": self.circuit_breaker.state.value,
            "failure_count": self.circuit_breaker.failure_count,
            "available": self.is_available()
        }