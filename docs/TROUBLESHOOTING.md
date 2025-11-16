# AutoArr Troubleshooting Guide

**Version:** 1.0.0
**Last Updated:** 2025-01-08

---

## Table of Contents

1. [Connection Issues](#connection-issues)
2. [Configuration Issues](#configuration-issues)
3. [Performance Issues](#performance-issues)
4. [LLM Issues](#llm-issues)
5. [Docker Issues](#docker-issues)
6. [Database Issues](#database-issues)
7. [UI Issues](#ui-issues)
8. [Diagnostic Tools](#diagnostic-tools)
9. [Getting Help](#getting-help)

---

## Connection Issues

### Cannot Connect to SABnzbd/Sonarr/Radarr

**Symptoms:**

- Error: "Service 'sabnzbd' is not connected"
- Health check shows service as unhealthy
- API requests fail with connection errors

**Diagnosis:**

```bash
# 1. Check if AutoArr can reach the service
curl http://your-sabnzbd-host:8080/api?mode=version&apikey=YOUR_API_KEY

# 2. Check AutoArr logs
docker logs autoarr | grep -i "sabnzbd"

# 3. Check MCP connection status
curl http://localhost:8000/health/sabnzbd
```

**Solutions:**

1. **Verify Service is Running**

   ```bash
   # Check if SABnzbd is accessible
   curl http://sabnzbd:8080
   ```

2. **Check API URL Configuration**

   ```bash
   # Verify environment variables
   docker exec autoarr env | grep SABNZBD

   # URLs should NOT have trailing slashes
   # Correct: http://sabnzbd:8080
   # Wrong: http://sabnzbd:8080/
   ```

3. **Verify API Key**

   - Log into SABnzbd web interface
   - Go to Config > General
   - Compare API key with your `.env` file
   - API keys are case-sensitive

4. **Check Network Configuration**

   ```yaml
   # docker-compose.yml
   services:
     autoarr:
       networks:
         - media-network
     sabnzbd:
       networks:
         - media-network # Must be on same network

   networks:
     media-network:
       driver: bridge
   ```

5. **Test Connection from AutoArr Container**

   ```bash
   # Enter AutoArr container
   docker exec -it autoarr bash

   # Test connectivity
   curl http://sabnzbd:8080/api?mode=version&apikey=YOUR_KEY
   ```

**Prevention:**

- Use Docker service names instead of `localhost`
- Keep all services on the same Docker network
- Use environment variables for configuration
- Enable health checks in docker-compose

---

### MCP Server Errors

**Symptoms:**

- "MCP tool call failed"
- "Circuit breaker open"
- Tool calls timeout

**Diagnosis:**

```bash
# Check circuit breaker status
curl http://localhost:8000/health/circuit-breaker/sabnzbd

# Check MCP server logs
docker logs autoarr 2>&1 | grep "MCP"
```

**Solutions:**

1. **Circuit Breaker Open**

   - Wait for timeout period (default: 60 seconds)
   - Circuit breaker opens after 5 consecutive failures
   - Check underlying service health

2. **Timeout Issues**

   ```python
   # Increase timeout in settings
   # Default: 30 seconds
   MCP_TIMEOUT_SECONDS=60
   ```

3. **Process Issues**

   ```bash
   # Check if MCP server process is running
   docker exec autoarr ps aux | grep mcp_servers

   # Restart AutoArr to restart MCP servers
   docker restart autoarr
   ```

**Prevention:**

- Monitor circuit breaker states
- Set appropriate timeout values
- Implement retry logic in clients
- Use health check endpoints regularly

---

### WebSocket Disconnections

**Symptoms:**

- Real-time updates stop working
- "WebSocket disconnected" in browser console
- UI shows stale data

**Diagnosis:**

```javascript
// Browser console
const ws = new WebSocket("ws://localhost:8000/ws/test-client");
ws.onopen = () => console.log("Connected");
ws.onerror = (e) => console.error("Error:", e);
ws.onclose = () => console.log("Disconnected");
```

**Solutions:**

1. **Proxy Configuration**

   - If behind reverse proxy (nginx, Traefik), ensure WebSocket support

   ```nginx
   # nginx configuration
   location /ws/ {
       proxy_pass http://autoarr:8000;
       proxy_http_version 1.1;
       proxy_set_header Upgrade $http_upgrade;
       proxy_set_header Connection "upgrade";
       proxy_set_header Host $host;
       proxy_read_timeout 86400;
   }
   ```

2. **Firewall Issues**

   - Ensure WebSocket port is open
   - Check Docker network configuration

3. **Connection Timeout**
   - WebSocket implements heartbeat (ping every 30s)
   - Check if pings are reaching server

**Prevention:**

- Implement automatic reconnection in UI
- Use heartbeat/ping mechanism
- Configure reverse proxy correctly
- Monitor WebSocket metrics

---

## Configuration Issues

### Invalid API Keys

**Symptoms:**

- "401 Unauthorized" errors
- "Invalid API key" messages
- Service shows as disconnected

**Diagnosis:**

```bash
# Test API key directly
curl -H "X-Api-Key: YOUR_KEY" http://sabnzbd:8080/api?mode=version

# Check AutoArr config
docker exec autoarr env | grep API_KEY
```

**Solutions:**

1. **Regenerate API Key**

   - SABnzbd: Config > General > API Key
   - Sonarr/Radarr: Settings > General > API Key
   - Update `.env` file with new key
   - Restart AutoArr

2. **Environment Variable Issues**

   ```bash
   # Verify env vars are set
   docker-compose config

   # Check for trailing spaces or quotes
   # Wrong: SABNZBD_API_KEY="abc123 "
   # Correct: SABNZBD_API_KEY=abc123
   ```

3. **Encrypted Storage**
   - If using encrypted key storage, verify encryption key
   - Check database has correct encrypted values

**Prevention:**

- Store API keys securely in `.env` file
- Add `.env` to `.gitignore`
- Use Docker secrets in production
- Document API key locations

---

### Permission Errors

**Symptoms:**

- "Permission denied" errors
- Cannot write to directories
- Database access errors

**Diagnosis:**

```bash
# Check file ownership
docker exec autoarr ls -la /app/data

# Check running user
docker exec autoarr id

# Check directory permissions
docker exec autoarr stat /app/data
```

**Solutions:**

1. **File Ownership**

   ```bash
   # Fix ownership (run on host)
   sudo chown -R 1000:1000 ./data

   # Or match Docker user
   docker exec autoarr id  # Get UID/GID
   sudo chown -R UID:GID ./data
   ```

2. **Volume Permissions**

   ```yaml
   # docker-compose.yml
   volumes:
     - ./data:/app/data:rw # Ensure read-write
   ```

3. **Database Permissions**

   ```bash
   # Check SQLite file
   ls -l ./data/autoarr.db

   # Should be writable by AutoArr user
   chmod 644 ./data/autoarr.db
   ```

**Prevention:**

- Use consistent UID/GID across services
- Mount volumes with correct permissions
- Use named volumes for databases
- Run containers as non-root user

---

### Missing Environment Variables

**Symptoms:**

- "Environment variable not set" errors
- Services not initializing
- Missing configuration values

**Diagnosis:**

```bash
# Check what AutoArr sees
docker exec autoarr env | sort

# Compare with .env.example
diff .env .env.example
```

**Solutions:**

1. **Copy Environment Template**

   ```bash
   # If .env doesn't exist
   cp .env.example .env

   # Edit with your values
   nano .env
   ```

2. **Docker Compose Environment**

   ```yaml
   # Ensure env_file is specified
   services:
     autoarr:
       env_file:
         - .env
       # Or explicit environment
       environment:
         - SABNZBD_API_URL=${SABNZBD_API_URL}
   ```

3. **Required vs Optional**
   ```bash
   # Minimum required variables
   SABNZBD_API_URL=http://sabnzbd:8080
   SABNZBD_API_KEY=your-key
   SONARR_API_URL=http://sonarr:8989
   SONARR_API_KEY=your-key
   RADARR_API_URL=http://radarr:7878
   RADARR_API_KEY=your-key
   ```

**Prevention:**

- Use `.env.example` as template
- Document all required variables
- Validate environment on startup
- Provide clear error messages

---

## Performance Issues

### Slow API Responses

**Symptoms:**

- API requests take > 5 seconds
- Timeout errors
- UI feels sluggish

**Diagnosis:**

```bash
# Check API response times
time curl http://localhost:8000/api/v1/downloads/queue

# Check system resources
docker stats autoarr

# Check database size
docker exec autoarr ls -lh /app/data/autoarr.db
```

**Solutions:**

1. **Database Optimization**

   ```bash
   # Vacuum database
   docker exec autoarr sqlite3 /app/data/autoarr.db "VACUUM;"

   # Analyze tables
   docker exec autoarr sqlite3 /app/data/autoarr.db "ANALYZE;"
   ```

2. **Enable Caching**

   ```bash
   # Add Redis for caching
   REDIS_URL=redis://redis:6379/0
   ```

3. **Increase Resources**

   ```yaml
   # docker-compose.yml
   services:
     autoarr:
       deploy:
         resources:
           limits:
             cpus: "2"
             memory: 1G
           reservations:
             cpus: "0.5"
             memory: 512M
   ```

4. **Connection Pooling**
   ```bash
   # Increase pool size
   DATABASE_POOL_SIZE=20
   DATABASE_MAX_OVERFLOW=10
   ```

**Prevention:**

- Regular database maintenance
- Monitor resource usage
- Use caching layer
- Implement pagination
- Add indexes to frequent queries

---

### High Memory Usage

**Symptoms:**

- Container using > 1GB RAM
- Out of memory errors
- System slowdowns

**Diagnosis:**

```bash
# Check memory usage
docker stats autoarr --no-stream

# Check Python memory usage
docker exec autoarr python -c "import psutil; print(psutil.Process().memory_info())"

# Profile memory
docker exec autoarr python -m memory_profiler script.py
```

**Solutions:**

1. **Limit Container Memory**

   ```yaml
   services:
     autoarr:
       mem_limit: 1g
       memswap_limit: 1g
   ```

2. **Reduce Connection Pool**

   ```bash
   DATABASE_POOL_SIZE=10
   DATABASE_MAX_OVERFLOW=5
   ```

3. **Clear Cache**

   ```bash
   # Clear Redis cache
   docker exec redis redis-cli FLUSHALL

   # Clear application cache
   curl -X POST http://localhost:8000/api/v1/cache/clear
   ```

4. **Restart Regularly**
   ```yaml
   services:
     autoarr:
       restart: unless-stopped
       # Or use health checks for automatic restart
       healthcheck:
         test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
         interval: 30s
         timeout: 10s
         retries: 3
   ```

**Prevention:**

- Monitor memory usage
- Set memory limits
- Implement cleanup tasks
- Use pagination for large datasets
- Profile memory usage regularly

---

### Database Query Timeouts

**Symptoms:**

- "Database query timeout" errors
- Slow page loads
- Connection pool exhausted

**Diagnosis:**

```bash
# Enable query logging
DATABASE_ECHO=true

# Check slow queries in logs
docker logs autoarr | grep "slow query"

# Check active connections
docker exec autoarr python -c "from autoarr.api.database import get_database; print(get_database().engine.pool.status())"
```

**Solutions:**

1. **Add Indexes**

   ```sql
   -- Run migrations to add indexes
   docker exec autoarr alembic upgrade head

   -- Check current indexes
   docker exec autoarr sqlite3 /app/data/autoarr.db ".schema"
   ```

2. **Increase Timeout**

   ```bash
   DATABASE_QUERY_TIMEOUT=60
   ```

3. **Optimize Queries**

   - Use pagination
   - Add select_in loading for relationships
   - Avoid N+1 queries
   - Use database-level aggregations

4. **Connection Pool**
   ```bash
   DATABASE_POOL_SIZE=20
   DATABASE_POOL_RECYCLE=3600
   DATABASE_POOL_PRE_PING=true
   ```

**Prevention:**

- Regular VACUUM and ANALYZE
- Monitor query performance
- Use appropriate indexes
- Implement query result caching
- Set reasonable timeouts

---

## LLM Issues

### Claude API Key Errors

**Symptoms:**

- "Invalid API key" errors
- "Authentication failed" messages
- Configuration audit fails

**Diagnosis:**

```bash
# Test API key directly
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: YOUR_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-3-sonnet-20240229","messages":[{"role":"user","content":"Hello"}],"max_tokens":10}'
```

**Solutions:**

1. **Get Valid API Key**

   - Visit: https://console.anthropic.com/
   - Create new API key
   - Update `.env` file:

   ```bash
   CLAUDE_API_KEY=sk-ant-api03-...
   ```

2. **Check Key Format**

   - Should start with `sk-ant-api03-`
   - No spaces or quotes
   - Complete key without truncation

3. **Verify Account Status**
   - Check account has credits
   - Verify API key permissions
   - Check for account restrictions

**Prevention:**

- Store API key securely
- Monitor API usage and costs
- Set up billing alerts
- Use environment variables

---

### Rate Limiting

**Symptoms:**

- "Rate limit exceeded" errors
- HTTP 429 responses
- Slow configuration audits

**Diagnosis:**

```bash
# Check rate limit headers
curl -v http://localhost:8000/api/v1/config/audit

# Check Claude API usage
# Visit: https://console.anthropic.com/usage
```

**Solutions:**

1. **Implement Backoff**

   - AutoArr has built-in exponential backoff
   - Increase retry delays:

   ```bash
   LLM_RETRY_BASE_DELAY=2.0
   LLM_RETRY_MAX_DELAY=120.0
   ```

2. **Upgrade API Tier**
   - Contact Anthropic for higher Claude API limits
   - Consider enterprise plan

3. **Batch Operations**

   - Audit multiple services at once
   - Avoid frequent small requests
   - Cache LLM responses

**Prevention:**

- Monitor API usage
- Implement request queuing
- Use caching effectively
- Schedule audits during off-peak
- Set reasonable rate limits

---

### Token Limit Exceeded

**Symptoms:**

- "Context length exceeded" errors
- Truncated responses
- Incomplete recommendations

**Diagnosis:**

```bash
# Check token usage
curl http://localhost:8000/api/v1/llm/usage

# Check configuration size
docker exec autoarr python -c "
from autoarr.api.services.config_manager import ConfigurationManager
import json
config = ConfigurationManager().get_all_configs()
print(f'Config size: {len(json.dumps(config))} characters')
"
```

**Solutions:**

1. **Reduce Context Size**

   - Audit one service at a time
   - Disable web search if not needed
   - Remove unnecessary config sections

2. **Use Smaller Model** (if available)

   ```bash
   CLAUDE_MODEL=claude-3-haiku-20240307  # Smaller, faster, cheaper
   ```

3. **Chunking**
   - Split large configurations
   - Process in batches
   - Combine results

**Prevention:**

- Monitor token usage
- Optimize prompts
- Use appropriate model for task
- Implement chunking strategy

---

## Docker Issues

### Container Won't Start

**Symptoms:**

- Container exits immediately
- "Error: ..." in docker logs
- Health check failures

**Diagnosis:**

```bash
# Check container logs
docker logs autoarr

# Check container status
docker ps -a | grep autoarr

# Inspect container
docker inspect autoarr
```

**Solutions:**

1. **Check Logs**

   ```bash
   docker logs autoarr --tail 100
   ```

2. **Common Issues**

   - Missing environment variables
   - Port conflicts
   - Volume mount issues
   - Database migration failures

3. **Start in Debug Mode**

   ```yaml
   services:
     autoarr:
       environment:
         - LOG_LEVEL=DEBUG
       command: uvicorn autoarr.api.main:app --reload
   ```

4. **Interactive Debugging**

   ```bash
   # Override entrypoint
   docker run -it --entrypoint bash autoarr/autoarr:latest

   # Check what's wrong
   python -m autoarr.api.main
   ```

**Prevention:**

- Use health checks
- Implement proper error handling
- Log startup process clearly
- Validate configuration on startup

---

### Port Conflicts

**Symptoms:**

- "Port is already allocated" error
- Cannot bind to port
- Service unreachable

**Diagnosis:**

```bash
# Check what's using the port
sudo netstat -tlnp | grep 8000
# or
sudo lsof -i :8000
```

**Solutions:**

1. **Change Port**

   ```yaml
   services:
     autoarr:
       ports:
         - "8001:8000" # Map to different host port
   ```

2. **Stop Conflicting Service**

   ```bash
   # Find and stop service using port
   sudo kill $(sudo lsof -t -i:8000)
   ```

3. **Use Docker Networks**
   ```yaml
   # Services communicate via network, no port mapping needed
   services:
     autoarr:
       networks:
         - backend
       # No ports exposed to host
   ```

**Prevention:**

- Document port usage
- Use standard port ranges
- Implement port detection
- Use Docker networks internally

---

### Volume Mount Issues

**Symptoms:**

- "No such file or directory"
- Permission denied on volumes
- Data not persisting

**Diagnosis:**

```bash
# Check volume mounts
docker inspect autoarr | grep -A 10 Mounts

# Check volume contents
docker exec autoarr ls -la /app/data

# Check host directory
ls -la ./data
```

**Solutions:**

1. **Create Directories**

   ```bash
   mkdir -p ./data
   chmod 755 ./data
   ```

2. **Fix Ownership**

   ```bash
   # Get container user ID
   docker exec autoarr id

   # Fix ownership
   sudo chown -R 1000:1000 ./data
   ```

3. **Use Named Volumes**

   ```yaml
   services:
     autoarr:
       volumes:
         - autoarr-data:/app/data

   volumes:
     autoarr-data:
       driver: local
   ```

**Prevention:**

- Use named volumes for databases
- Set correct permissions
- Document volume requirements
- Use consistent UID/GID

---

## Database Issues

### Migration Failures

**Symptoms:**

- "Migration failed" errors
- Database schema mismatch
- Application won't start

**Diagnosis:**

```bash
# Check migration status
docker exec autoarr alembic current

# Check migration history
docker exec autoarr alembic history
```

**Solutions:**

1. **Run Migrations Manually**

   ```bash
   docker exec autoarr alembic upgrade head
   ```

2. **Reset Database** (WARNING: Data loss)

   ```bash
   # Backup first
   docker exec autoarr cp /app/data/autoarr.db /app/data/autoarr.db.backup

   # Remove database
   docker exec autoarr rm /app/data/autoarr.db

   # Restart container (will recreate DB)
   docker restart autoarr
   ```

3. **Fix Specific Migration**

   ```bash
   # Downgrade to previous version
   docker exec autoarr alembic downgrade -1

   # Upgrade again
   docker exec autoarr alembic upgrade head
   ```

**Prevention:**

- Backup before upgrades
- Test migrations in development
- Keep Alembic version consistent
- Document migration process

---

### Database Corruption

**Symptoms:**

- "Database disk image is malformed"
- SQLite errors
- Data inconsistencies

**Diagnosis:**

```bash
# Check database integrity
docker exec autoarr sqlite3 /app/data/autoarr.db "PRAGMA integrity_check;"
```

**Solutions:**

1. **Restore from Backup**

   ```bash
   # Stop AutoArr
   docker stop autoarr

   # Restore backup
   cp ./data/autoarr.db.backup ./data/autoarr.db

   # Start AutoArr
   docker start autoarr
   ```

2. **Repair Database**

   ```bash
   # Dump and restore
   docker exec autoarr sqlite3 /app/data/autoarr.db ".dump" | \
     docker exec -i autoarr sqlite3 /app/data/autoarr_repaired.db

   # Replace corrupted DB
   docker exec autoarr mv /app/data/autoarr.db /app/data/autoarr.db.corrupted
   docker exec autoarr mv /app/data/autoarr_repaired.db /app/data/autoarr.db
   ```

**Prevention:**

- Regular backups
- Use WAL mode (Write-Ahead Logging)
- Don't force-kill container during writes
- Use PostgreSQL for production

---

## UI Issues

### Blank Page or Loading Forever

**Symptoms:**

- UI doesn't load
- Stuck on loading screen
- Console errors

**Diagnosis:**

```javascript
// Open browser console (F12)
// Check for errors
console.log("Errors:", window.errors);

// Check API connectivity
fetch("http://localhost:8000/health")
  .then((r) => r.json())
  .then(console.log)
  .catch(console.error);
```

**Solutions:**

1. **Check Backend is Running**

   ```bash
   curl http://localhost:8000/health
   ```

2. **Clear Browser Cache**

   - Hard refresh: Ctrl+Shift+R (Ctrl+F5)
   - Clear all browser cache
   - Try incognito mode

3. **Check CORS Settings**

   ```bash
   # Add to .env
   CORS_ORIGINS=http://localhost:3000,http://localhost:5173
   ```

4. **Check Console Errors**
   - F12 → Console tab
   - Look for red errors
   - Check Network tab for failed requests

**Prevention:**

- Monitor backend health
- Implement error boundaries
- Add loading timeouts
- Show user-friendly errors

---

### Real-Time Updates Not Working

**Symptoms:**

- No live updates
- Must refresh to see changes
- WebSocket disconnected

**Diagnosis:**

```javascript
// Check WebSocket connection
const ws = new WebSocket("ws://localhost:8000/ws/test");
ws.onopen = () => console.log("WebSocket connected");
ws.onerror = (e) => console.error("WebSocket error:", e);
ws.onmessage = (e) => console.log("Message:", e.data);
```

**Solutions:**

1. **Check WebSocket Connection**

   - See [WebSocket Disconnections](#websocket-disconnections)

2. **Verify Event Subscription**

   ```javascript
   // Join appropriate room
   ws.send(
     JSON.stringify({
       type: "join_room",
       room: "config_audit",
     }),
   );
   ```

3. **Check Firewall/Proxy**
   - Ensure WebSocket port is open
   - Configure reverse proxy for WebSocket

**Prevention:**

- Implement reconnection logic
- Add connection status indicator
- Use heartbeat mechanism
- Test WebSocket in different environments

---

## Diagnostic Tools

### Health Check Script

```bash
#!/bin/bash
# health-check.sh

echo "=== AutoArr Health Check ==="
echo

# Check Docker container
echo "1. Container Status:"
docker ps -a | grep autoarr

# Check health endpoint
echo -e "\n2. Health Endpoint:"
curl -s http://localhost:8000/health | python -m json.tool

# Check MCP servers
echo -e "\n3. MCP Server Status:"
for service in sabnzbd sonarr radarr; do
    echo "  $service:"
    curl -s "http://localhost:8000/health/$service" | python -m json.tool
done

# Check logs for errors
echo -e "\n4. Recent Errors:"
docker logs autoarr --tail 20 2>&1 | grep -i error

# Check resource usage
echo -e "\n5. Resource Usage:"
docker stats autoarr --no-stream

echo -e "\n=== Health Check Complete ==="
```

### Log Analysis Script

```bash
#!/bin/bash
# analyze-logs.sh

echo "=== Log Analysis ==="

# Count error types
echo "Error Summary:"
docker logs autoarr 2>&1 | grep -i error | awk '{print $NF}' | sort | uniq -c | sort -nr

# Recent errors
echo -e "\nRecent Errors:"
docker logs autoarr --tail 50 2>&1 | grep -i error

# Connection errors
echo -e "\nConnection Errors:"
docker logs autoarr 2>&1 | grep -i "connection.*failed"

# Performance warnings
echo -e "\nPerformance Warnings:"
docker logs autoarr 2>&1 | grep -i "slow\|timeout"
```

### Configuration Validator

```bash
#!/bin/bash
# validate-config.sh

echo "=== Configuration Validation ==="

# Check required environment variables
required_vars=(
    "SABNZBD_API_URL"
    "SABNZBD_API_KEY"
    "SONARR_API_URL"
    "SONARR_API_KEY"
    "RADARR_API_URL"
    "RADARR_API_KEY"
)

missing=0
for var in "${required_vars[@]}"; do
    if ! docker exec autoarr env | grep -q "^$var="; then
        echo "❌ Missing: $var"
        missing=$((missing + 1))
    else
        echo "✅ Found: $var"
    fi
done

if [ $missing -eq 0 ]; then
    echo -e "\n✅ All required variables present"
else
    echo -e "\n❌ $missing variable(s) missing"
    exit 1
fi
```

---

## Getting Help

### Before Asking for Help

1. **Check Logs**

   ```bash
   docker logs autoarr --tail 100
   ```

2. **Run Health Check**

   ```bash
   curl http://localhost:8000/health | python -m json.tool
   ```

3. **Check Documentation**

   - [Quick Start Guide](/app/docs/QUICK-START.md)
   - [Configuration Guide](/app/docs/CONFIGURATION.md)
   - [FAQ](/app/docs/FAQ.md)

4. **Search Existing Issues**
   - https://github.com/autoarr/autoarr/issues

### Creating a Bug Report

Include:

1. **Environment Details**

   - AutoArr version: `docker exec autoarr cat /app/VERSION`
   - Docker version: `docker --version`
   - OS: `uname -a`

2. **Configuration** (sanitized)

   ```bash
   # Remove API keys before sharing
   docker exec autoarr env | grep -v API_KEY
   ```

3. **Logs**

   ```bash
   docker logs autoarr --tail 100 > autoarr.log
   ```

4. **Steps to Reproduce**

   - What you did
   - What you expected
   - What actually happened

5. **Screenshots** (if UI issue)

### Support Channels

- **GitHub Issues**: Bug reports and feature requests

  - https://github.com/autoarr/autoarr/issues

- **GitHub Discussions**: Questions and general discussion

  - https://github.com/autoarr/autoarr/discussions

- **Discord**: Real-time community support

  - https://discord.gg/autoarr

- **Documentation**: Comprehensive guides
  - https://docs.autoarr.io

---

## Appendix: Common Error Messages

| Error Message                  | Cause                  | Solution                                  |
| ------------------------------ | ---------------------- | ----------------------------------------- |
| "Service 'X' is not connected" | MCP server not running | Check service URL and API key             |
| "Circuit breaker open"         | Too many failures      | Wait 60s or restart AutoArr               |
| "Rate limit exceeded"          | Too many requests      | Wait or upgrade API tier                  |
| "Invalid API key"              | Wrong API key          | Regenerate and update `.env`              |
| "Database locked"              | Concurrent writes      | Enable WAL mode or use PostgreSQL         |
| "Port already allocated"       | Port conflict          | Change port or stop conflicting service   |
| "Permission denied"            | File permissions       | Fix ownership with `chown`                |
| "Context length exceeded"      | Input too large        | Reduce configuration size or use chunking |

---

**Last Updated:** 2025-01-08
**For updates:** Check https://github.com/autoarr/autoarr/docs/TROUBLESHOOTING.md
