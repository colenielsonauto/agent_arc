"""
Abstract interface for analytics sinks.

This interface defines the contract for analytics and observability systems
(Prometheus, Datadog, LangSmith, etc.) to enable comprehensive monitoring,
metrics collection, and performance tracking.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import time


class MetricType(str, Enum):
    """Types of metrics."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class LogLevel(str, Enum):
    """Log levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Metric:
    """A single metric point."""
    name: str
    value: Union[int, float]
    metric_type: MetricType
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    unit: Optional[str] = None
    description: Optional[str] = None


@dataclass
class LogEntry:
    """A structured log entry."""
    level: LogLevel
    message: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    context: Dict[str, Any] = field(default_factory=dict)
    error: Optional[Exception] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    user_id: Optional[str] = None


@dataclass
class Trace:
    """A distributed trace."""
    trace_id: str
    spans: List["Span"] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None


@dataclass
class Span:
    """A span within a trace."""
    span_id: str
    trace_id: str
    operation_name: str
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    parent_span_id: Optional[str] = None
    tags: Dict[str, Any] = field(default_factory=dict)
    logs: List[LogEntry] = field(default_factory=list)
    status: str = "in_progress"
    
    def duration_ms(self) -> Optional[float]:
        """Calculate span duration in milliseconds."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return None


@dataclass
class EmailProcessingMetrics:
    """Metrics specific to email processing."""
    email_id: str
    user_id: str
    classification: str
    confidence: float
    processing_time_ms: float
    llm_provider: str
    llm_model: str
    tokens_used: int
    forwarded_to: str
    draft_generated: bool
    error_occurred: bool = False
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AnalyticsConfig:
    """Configuration for analytics sinks."""
    sink_type: str
    connection_params: Dict[str, Any]
    batch_size: int = 100
    flush_interval: int = 10  # seconds
    buffer_size: int = 10000
    enable_tracing: bool = True
    enable_metrics: bool = True
    enable_logs: bool = True
    sampling_rate: float = 1.0  # 1.0 = 100% sampling


class AnalyticsSinkInterface(ABC):
    """Abstract interface for analytics sinks."""
    
    def __init__(self, config: AnalyticsConfig):
        """Initialize the analytics sink with configuration."""
        self.config = config
        self._validate_config()
        self._start_time = time.time()
    
    @abstractmethod
    def _validate_config(self) -> None:
        """Validate sink-specific configuration."""
        pass
    
    @abstractmethod
    async def connect(self) -> None:
        """Connect to the analytics service."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the analytics service."""
        pass
    
    @abstractmethod
    async def log(self, entry: LogEntry) -> None:
        """
        Send a log entry.
        
        Args:
            entry: The log entry to send
        """
        pass
    
    @abstractmethod
    async def metric(self, metric: Metric) -> None:
        """
        Send a metric.
        
        Args:
            metric: The metric to send
        """
        pass
    
    @abstractmethod
    async def start_trace(self, trace: Trace) -> None:
        """
        Start a distributed trace.
        
        Args:
            trace: The trace to start
        """
        pass
    
    @abstractmethod
    async def start_span(self, span: Span) -> None:
        """
        Start a span within a trace.
        
        Args:
            span: The span to start
        """
        pass
    
    @abstractmethod
    async def end_span(self, span_id: str, status: str = "success") -> None:
        """
        End a span.
        
        Args:
            span_id: The span ID
            status: The final status of the span
        """
        pass
    
    @abstractmethod
    async def track_email_processing(
        self,
        metrics: EmailProcessingMetrics
    ) -> None:
        """
        Track email processing metrics.
        
        Args:
            metrics: The email processing metrics
        """
        pass
    
    @abstractmethod
    async def query_metrics(
        self,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        labels: Optional[Dict[str, str]] = None
    ) -> List[Metric]:
        """
        Query historical metrics.
        
        Args:
            metric_name: Name of the metric
            start_time: Start of the time range
            end_time: End of the time range
            labels: Optional label filters
            
        Returns:
            List of metrics matching the query
        """
        pass
    
    @abstractmethod
    async def get_dashboard_stats(
        self,
        time_range_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get dashboard statistics.
        
        Args:
            time_range_hours: Hours to look back
            
        Returns:
            Dictionary of statistics for dashboards
        """
        pass
    
    # Convenience methods with default implementations
    
    async def increment_counter(
        self,
        name: str,
        value: int = 1,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Increment a counter metric."""
        await self.metric(Metric(
            name=name,
            value=value,
            metric_type=MetricType.COUNTER,
            labels=labels or {}
        ))
    
    async def set_gauge(
        self,
        name: str,
        value: Union[int, float],
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Set a gauge metric."""
        await self.metric(Metric(
            name=name,
            value=value,
            metric_type=MetricType.GAUGE,
            labels=labels or {}
        ))
    
    async def record_histogram(
        self,
        name: str,
        value: Union[int, float],
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a histogram metric."""
        await self.metric(Metric(
            name=name,
            value=value,
            metric_type=MetricType.HISTOGRAM,
            labels=labels or {}
        ))
    
    async def log_info(
        self,
        message: str,
        **context
    ) -> None:
        """Log an info message."""
        await self.log(LogEntry(
            level=LogLevel.INFO,
            message=message,
            context=context
        ))
    
    async def log_error(
        self,
        message: str,
        error: Optional[Exception] = None,
        **context
    ) -> None:
        """Log an error message."""
        await self.log(LogEntry(
            level=LogLevel.ERROR,
            message=message,
            error=error,
            context=context
        ))
    
    async def track_llm_call(
        self,
        provider: str,
        model: str,
        operation: str,
        tokens: int,
        duration_ms: float,
        success: bool = True,
        error: Optional[str] = None
    ) -> None:
        """Track LLM API call metrics."""
        labels = {
            "provider": provider,
            "model": model,
            "operation": operation,
            "success": str(success).lower()
        }
        
        await self.increment_counter("llm_calls_total", labels=labels)
        await self.increment_counter("llm_tokens_total", value=tokens, labels=labels)
        await self.record_histogram("llm_call_duration_ms", duration_ms, labels=labels)
        
        if not success and error:
            await self.log_error(
                f"LLM call failed: {error}",
                provider=provider,
                model=model,
                operation=operation
            )
    
    async def health_check(self) -> bool:
        """Check if the analytics sink is working."""
        try:
            await self.connect()
            await self.log_info("Analytics health check")
            await self.disconnect()
            return True
        except Exception:
            return False 