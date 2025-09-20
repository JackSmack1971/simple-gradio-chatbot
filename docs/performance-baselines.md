# Performance Baseline Metrics

## Overview

This document establishes performance expectations and monitoring baselines for the Personal AI Chatbot. All metrics are based on research of similar implementations and component benchmarks.

## Response Time Targets

### End-to-End Response Times

| Scenario | Target | Acceptable | Unacceptable |
|----------|--------|------------|--------------|
| Simple query (10 words) | <3 seconds | <8 seconds | >15 seconds |
| Complex query (50 words) | <8 seconds | <15 seconds | >30 seconds |
| Streaming start delay | <1 second | <2 seconds | >5 seconds |
| UI interaction feedback | <100ms | <500ms | >1 second |

### Component Breakdown

**OpenRouter API Response Times**:
- Token generation: 10-50ms per token (streaming)
- First token latency: 500-2000ms
- Complete response (100 tokens): 2-8 seconds
- Rate limit check: <200ms

**Gradio Interface Times**:
- Page load: <500ms
- Message send: <100ms
- History load: <200ms (JSON), <50ms (SQLite)
- UI rendering: <50ms per update

**File Storage Operations**:
- JSON save (small conversation): <50ms
- JSON load (small conversation): <20ms
- SQLite query: <10ms
- Backup creation: <100ms

## Memory Usage Benchmarks

### Baseline Memory Footprint

**Application Startup**:
- Gradio + dependencies: 80-120MB
- Python interpreter: 20-40MB
- Total initial: 100-160MB

**Per Conversation Session**:
- JSON storage: 1-5MB per 100 messages
- SQLite storage: 2-8MB per 100 messages
- In-memory history: 0.5-2MB per 100 messages

### Memory Growth Patterns

**Gradio Memory Issues**:
- Base session: 100-200MB
- After 1 hour continuous use: 500MB-1GB
- After 24 hours: 2-7GB (known memory leak)
- Per concurrent user: +50-100MB

**OpenRouter Client**:
- Per request overhead: <10MB
- Streaming buffer: <50MB
- Connection pooling: <20MB

### Memory Monitoring Thresholds

| Component | Warning | Critical | Action |
|-----------|---------|----------|--------|
| Total RAM | >500MB | >1GB | Restart application |
| Gradio session | >300MB | >1GB | Clear session state |
| File cache | >100MB | >500MB | Clear old conversations |
| Python heap | >200MB | >500MB | Force garbage collection |

## UI Responsiveness Metrics

### Interaction Benchmarks

**Chat Interface**:
- Typing lag: <10ms
- Message send delay: <50ms
- Scroll performance: 60fps
- Streaming text update: <50ms per chunk

**Loading States**:
- Initial load: <1 second
- Conversation switch: <200ms
- Settings save: <100ms

### Streaming Performance

**Text Streaming**:
- Chunk size: 1-5 tokens
- Update frequency: 50-200ms
- CPU usage: <50% during streaming
- Memory per stream: <10MB

## API Performance Considerations

### OpenRouter Rate Limits

**Free Tier**:
- Requests per minute: 20
- Requests per day: 50 (no credits), 1000 (10+ credits)
- Burst capacity: Limited
- Retry delay: 60 seconds on 429

**Paid Tier**:
- Requests per minute: 100-1000+ (based on credits)
- Daily limits: 10,000+ (based on credits)
- Burst capacity: Higher
- Retry delay: 10-30 seconds on 429

### Error Recovery Times

| Error Type | Retry Delay | Max Retries | Timeout |
|------------|-------------|-------------|---------|
| Rate limit (429) | 60 seconds | 3 | 300 seconds |
| Timeout (408) | 5 seconds | 3 | 60 seconds |
| Server error (5xx) | 10 seconds | 3 | 120 seconds |
| Network error | 2 seconds | 5 | 30 seconds |

## Storage Performance Metrics

### File-based Storage

**JSON Operations**:
- Read small file (<1MB): <20ms
- Write small file: <50ms
- Read large file (10MB): <200ms
- Write large file: <500ms

**SQLite Operations**:
- Connection open: <5ms
- Simple query: <1ms
- Complex query: <10ms
- Bulk insert (100 rows): <50ms

### Data Integrity Benchmarks

**Backup Performance**:
- Incremental backup: <100ms
- Full backup (1MB): <500ms
- Recovery time: <2 seconds
- Corruption detection: <50ms

## Scaling Expectations

### Single User Limits

**Conversation Scale**:
- Max messages per conversation: 1000
- Max conversations: 100
- Max message length: 4000 characters
- Total storage: <500MB

**Session Limits**:
- Max session duration: 8 hours
- Max idle time: 2 hours
- Auto-save frequency: Every 5 messages
- Memory reset: Every 4 hours

### Performance Degradation Points

| Metric | Threshold | Impact |
|--------|-----------|--------|
| RAM usage | >1GB | UI freezing, crashes |
| Response time | >10 seconds | User frustration |
| CPU usage | >80% | Streaming lag, UI unresponsiveness |
| Disk I/O | >100MB/s | Slow saves, UI blocking |
| Network latency | >2 seconds | Timeout errors |

## Monitoring Recommendations

### Key Metrics to Track

```python
# Performance monitoring class
class PerformanceMonitor:
    def __init__(self):
        self.metrics = {
            'response_times': [],
            'memory_usage': [],
            'api_calls': [],
            'errors': []
        }

    def record_response_time(self, operation: str, duration: float):
        """Record operation response time"""
        self.metrics['response_times'].append({
            'operation': operation,
            'duration': duration,
            'timestamp': time.time()
        })

    def record_memory_usage(self):
        """Record current memory usage"""
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        self.metrics['memory_usage'].append({
            'memory_mb': memory_mb,
            'timestamp': time.time()
        })

    def record_api_call(self, endpoint: str, success: bool, duration: float):
        """Record API call metrics"""
        self.metrics['api_calls'].append({
            'endpoint': endpoint,
            'success': success,
            'duration': duration,
            'timestamp': time.time()
        })

    def get_performance_report(self) -> dict:
        """Generate performance report"""
        return {
            'avg_response_time': self._calculate_average('response_times', 'duration'),
            'max_memory_usage': max((m['memory_mb'] for m in self.metrics['memory_usage']), default=0),
            'api_success_rate': self._calculate_success_rate(),
            'error_rate': len(self.metrics['errors']) / max(len(self.metrics['api_calls']), 1)
        }
```

### Alert Thresholds

**Immediate Alerts**:
- Response time > 15 seconds
- Memory usage > 1GB
- API error rate > 20%
- CPU usage > 90%

**Warning Alerts**:
- Response time > 8 seconds
- Memory usage > 500MB
- API error rate > 5%
- CPU usage > 70%

### Logging Configuration

```python
# logging_config.py
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'performance': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s - duration=%(duration)s'
        }
    },
    'handlers': {
        'performance_file': {
            'class': 'logging.FileHandler',
            'filename': 'performance.log',
            'formatter': 'performance'
        }
    },
    'loggers': {
        'performance': {
            'handlers': ['performance_file'],
            'level': 'INFO',
            'propagate': False
        }
    }
}
```

## Benchmarking Methodology

### Test Scenarios

1. **Cold Start**: First request after application start
2. **Warm Cache**: Subsequent requests with loaded conversation
3. **Large Conversation**: 500+ messages loaded
4. **High Frequency**: 10 requests per minute
5. **Network Degradation**: Simulate slow connections
6. **Memory Pressure**: Extended usage without restart

### Benchmark Tools

```python
# benchmark.py
import time
import psutil
import requests

def benchmark_response_time(url: str, payload: dict, iterations: int = 10) -> dict:
    """Benchmark API response times"""
    times = []

    for _ in range(iterations):
        start = time.time()
        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            duration = time.time() - start
            times.append(duration)
        except Exception as e:
            print(f"Benchmark iteration failed: {e}")
            times.append(float('inf'))

    return {
        'min': min(times),
        'max': max(times),
        'avg': sum(t for t in times if t != float('inf')) / len([t for t in times if t != float('inf')]),
        'p95': sorted([t for t in times if t != float('inf')])[int(len(times) * 0.95)]
    }

def benchmark_memory_usage(func, *args, **kwargs) -> dict:
    """Benchmark memory usage of function"""
    process = psutil.Process()
    initial_memory = process.memory_info().rss

    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()

    final_memory = process.memory_info().rss
    memory_delta = final_memory - initial_memory

    return {
        'initial_memory_mb': initial_memory / 1024 / 1024,
        'final_memory_mb': final_memory / 1024 / 1024,
        'memory_delta_mb': memory_delta / 1024 / 1024,
        'execution_time': end_time - start_time,
        'result': result
    }
```

### Continuous Monitoring

**Daily Checks**:
- Average response time trends
- Memory usage patterns
- Error rate analysis
- Storage growth rate

**Weekly Reviews**:
- Performance regression analysis
- Memory leak detection
- API usage optimization
- User experience metrics

These baselines provide a foundation for monitoring and optimizing the Personal AI Chatbot's performance, ensuring reliable operation within acceptable parameters.