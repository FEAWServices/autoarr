# AutoArr Troubleshooting Guide

Common issues and solutions for AutoArr.

## Table of Contents

- [Connection Issues](#connection-issues)
- [Configuration Problems](#configuration-problems)
- [Performance Issues](#performance-issues)
- [Error Messages](#error-messages)
- [Debugging](#debugging)

## Connection Issues

### Cannot Connect to SABnzbd/Sonarr/Radarr

**Symptoms**: Service shows as "unhealthy" in `/health` endpoint.

**Solutions**:

1. **Check service is running**:

   ```bash
   # Test SABnzbd
   curl http://localhost:8080/api?mode=version&apikey=YOUR_KEY

   # Test Sonarr
   curl http://localhost:8989/api/v3/system/status?apikey=YOUR_KEY
   ```

2. **Verify API key**:

   - Navigate to service settings
   - Copy API key exactly (no extra spaces)
   - Update `.env` file

3. **Check network connectivity**:

   ```bash
   # Ping the service
   ping localhost

   # Test port is open
   telnet localhost 8080
   ```

4. **Check Docker networking** (if using Docker):

   ```bash
   # List networks
   docker network ls

   # Inspect network
   docker network inspect autoarr_default
   ```

### Circuit Breaker is Open

**Symptoms**: Requests fail with "Circuit breaker is open" error.

**Solutions**:

1. **Wait for timeout**: Circuit breaker automatically closes after configured timeout (default: 60 seconds)

2. **Check service health**:

   ```bash
   curl http://localhost:8000/health/sabnzbd
   ```

3. **Reset circuit breaker**: Restart AutoArr

   ```bash
   docker restart autoarr
   ```

4. **Adjust threshold**:
   ```bash
   # In .env
   CIRCUIT_BREAKER_THRESHOLD=10  # Increase threshold
   ```

## Configuration Problems

### Settings Not Persisting

**Solutions**:

1. **Check database connection**:

   ```bash
   # View logs
   docker logs autoarr | grep -i database
   ```

2. **Verify database file permissions**:

   ```bash
   ls -la /app/data/autoarr.db
   ```

3. **Use PostgreSQL** for production:
   ```bash
   DATABASE_URL=postgresql://user:pass@localhost:5432/autoarr
   ```

### Configuration Audit Fails

**Solutions**:

1. **Enable debug logging**:

   ```bash
   LOG_LEVEL=DEBUG
   ```

2. **Check API permissions**: Ensure API keys have admin access

3. **Verify web search** (if enabled):
   ```bash
   # Disable web search temporarily
   curl -X POST http://localhost:8000/api/v1/config/audit \
     -d '{"services": ["sabnzbd"], "include_web_search": false}'
   ```

## Performance Issues

### Slow API Responses

**Solutions**:

1. **Enable caching**:

   ```bash
   REDIS_URL=redis://localhost:6379
   ```

2. **Increase timeouts**:

   ```bash
   DEFAULT_TOOL_TIMEOUT=60.0
   ```

3. **Reduce parallel calls**:

   ```bash
   MAX_PARALLEL_CALLS=5
   ```

4. **Check database indices**:
   ```sql
   -- View table sizes
   SELECT name, COUNT(*) FROM sqlite_master WHERE type='index';
   ```

### High Memory Usage

**Solutions**:

1. **Limit connection pool**:

   ```bash
   CONNECTION_POOL_SIZE=5
   ```

2. **Reduce cache TTL**:

   ```bash
   CACHE_TTL=60  # 1 minute
   ```

3. **Monitor with Prometheus**:
   ```bash
   curl http://localhost:8000/metrics
   ```

## Error Messages

### "Service unavailable"

**Cause**: External service is down or unreachable.

**Solutions**:

1. Check service status
2. Verify network connectivity
3. Check firewall rules

### "Invalid API key"

**Cause**: API key is incorrect or expired.

**Solutions**:

1. Regenerate API key in service settings
2. Update `.env` file
3. Restart AutoArr

### "Database locked"

**Cause**: SQLite database is locked by another process.

**Solutions**:

1. Ensure only one AutoArr instance is running
2. Check for zombie processes
3. Delete `.db-wal` and `.db-shm` files (if safe)
4. Switch to PostgreSQL for production

### "Rate limit exceeded"

**Cause**: Too many requests to API.

**Solutions**:

1. Wait for rate limit window to reset
2. Reduce request frequency
3. Check for infinite loops in custom scripts

## Debugging

### Enable Debug Logging

```bash
# In .env
LOG_LEVEL=DEBUG
```

### View Logs

```bash
# Docker logs
docker logs -f autoarr

# Specific component
docker logs autoarr 2>&1 | grep -i "configuration"
```

### Check Health Endpoints

```bash
# Overall health
curl http://localhost:8000/health

# Service-specific health
curl http://localhost:8000/health/sabnzbd

# Circuit breaker status
curl http://localhost:8000/health/circuit-breaker/sabnzbd
```

### Test MCP Tools Directly

```bash
# List tools
curl http://localhost:8000/api/v1/mcp/tools

# Call tool
curl -X POST http://localhost:8000/api/v1/mcp/call \
  -H "Content-Type: application/json" \
  -d '{
    "server": "sabnzbd",
    "tool": "get_queue",
    "params": {}
  }'
```

### Database Inspection

```bash
# Connect to SQLite database
sqlite3 /app/data/autoarr.db

# List tables
.tables

# View schema
.schema activity_log

# Query data
SELECT * FROM activity_log ORDER BY timestamp DESC LIMIT 10;
```

### Network Debugging

```bash
# Test DNS resolution
nslookup sonarr

# Trace route
traceroute sonarr

# Check listening ports
netstat -tlnp | grep 8000
```

### Performance Profiling

```bash
# Enable profiling
ENABLE_PROFILING=true

# View metrics
curl http://localhost:8000/metrics

# Use Grafana dashboard
open http://localhost:3000
```

---

Still having issues? Check our [FAQ](FAQ.md) or [open an issue](https://github.com/autoarr/autoarr/issues).
