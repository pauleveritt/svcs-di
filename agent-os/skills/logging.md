---
description:
  Logging standards for Python applications. Use this when implementing
  structured logging, configuring log levels, or adding observability.
---

# Logging Standards

## Structured Logging with structlog

Use structlog for structured, contextual logging:

```python
import structlog

log = structlog.get_logger()

def process_order(order_id: str, user_id: str) -> None:
    log.info("processing_order", order_id=order_id, user_id=user_id)

    try:
        result = validate_order(order_id)
        log.info("order_validated", order_id=order_id, items=len(result.items))
    except ValidationError as e:
        log.warning("order_validation_failed", order_id=order_id, reason=str(e))
        raise
```

### Configuration

```python
import structlog

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer()  # For development
        # structlog.processors.JSONRenderer()  # For production
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)
```

## Log Levels

Use appropriate log levels consistently:

| Level | When to Use |
|-------|-------------|
| **DEBUG** | Detailed diagnostic info for debugging |
| **INFO** | Normal operation milestones (request started, completed) |
| **WARNING** | Unexpected but recoverable situations |
| **ERROR** | Failures that prevent operation completion |
| **CRITICAL** | System-level failures requiring immediate attention |

### Examples

```python
# DEBUG - Development diagnostics
log.debug("cache_lookup", key=cache_key, hit=cache_hit)

# INFO - Normal operations
log.info("request_started", method="POST", path="/api/orders")
log.info("request_completed", method="POST", path="/api/orders", status=201, duration_ms=45)

# WARNING - Recoverable issues
log.warning("rate_limit_approaching", user_id=user_id, requests=95, limit=100)
log.warning("deprecated_endpoint_called", endpoint="/api/v1/users", replacement="/api/v2/users")

# ERROR - Operation failures
log.error("payment_failed", order_id=order_id, provider="stripe", error=str(e))

# CRITICAL - System failures
log.critical("database_connection_lost", host=db_host, retry_count=3)
```

## Context Variables and Request Tracing

Use context variables for request-scoped data:

```python
import structlog
from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar("request_id", default="")

def add_request_context(logger, method_name, event_dict):
    """Processor that adds request context to all logs."""
    if request_id := request_id_var.get():
        event_dict["request_id"] = request_id
    return event_dict

# In middleware
def middleware(request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request_id_var.set(request_id)
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id)
    return call_next(request)
```

### Binding Context

```python
log = structlog.get_logger()

# Bind context for duration of operation
log = log.bind(user_id=user_id, session_id=session_id)
log.info("user_action", action="login")  # Includes user_id and session_id
log.info("user_action", action="view_profile")  # Same context
```

## What to Log

### DO Log

- **Request boundaries**: Start and completion of requests with timing
- **Business events**: Orders placed, users registered, payments processed
- **External calls**: API calls to third parties with timing and status
- **State transitions**: Status changes in workflows
- **Security events**: Login attempts, permission denials, token refreshes
- **Performance metrics**: Slow queries, cache hit rates

### DON'T Log

- **Sensitive data**: Passwords, tokens, PII, credit card numbers
- **High-frequency noise**: Every loop iteration, every cache lookup
- **Redundant info**: Same event logged at multiple levels
- **Large payloads**: Full request/response bodies (log size/summary instead)

### Sanitization

```python
def sanitize_for_logging(data: dict) -> dict:
    """Remove sensitive fields before logging."""
    sensitive_keys = {"password", "token", "secret", "api_key", "credit_card"}
    return {
        k: "[REDACTED]" if k.lower() in sensitive_keys else v
        for k, v in data.items()
    }

log.info("user_update", data=sanitize_for_logging(user_data))
```

## Error Logging

Log errors with context but avoid duplication:

```python
# Good: Log at the boundary where you handle the error
try:
    result = process_order(order_id)
except OrderError as e:
    log.error("order_processing_failed", order_id=order_id, error=str(e))
    raise HTTPException(status_code=400, detail=str(e))

# Bad: Logging then re-raising (causes duplicate logs)
try:
    result = process_order(order_id)
except OrderError as e:
    log.error("order_processing_failed", order_id=order_id, error=str(e))
    raise  # The caller will also log this!
```

## Testing Logs

Use structlog's testing utilities:

```python
import structlog
from structlog.testing import capture_logs

def test_logs_order_processing():
    with capture_logs() as logs:
        process_order("order-123", "user-456")

    assert logs[0]["event"] == "processing_order"
    assert logs[0]["order_id"] == "order-123"
```

## Anti-Patterns

- **Print statements**: Using `print()` instead of structured logging
- **String interpolation**: Using f-strings in log messages instead of key-value pairs
- **Logging sensitive data**: Including passwords, tokens, or PII in logs
- **Log-and-raise**: Logging an error then re-raising it without handling
- **Missing context**: Logging events without identifying information
- **Inconsistent levels**: Using ERROR for warnings or DEBUG for important events
- **Excessive logging**: Logging in tight loops or high-frequency code paths
- **No correlation IDs**: Missing request/trace IDs for distributed tracing

## Related Skills

- [error-handling](error-handling.md) - Exception handling patterns
- [configuration](configuration.md) - Configuring log levels per environment
- [testing](testing/testing.md) - Testing log output
