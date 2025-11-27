# Docker Development Setup - Checklist

This checklist helps you verify everything is set up correctly.

## ✅ Pre-Setup Requirements

- [ ] Docker is installed (`docker --version`)
- [ ] Docker Compose is installed (`docker-compose --version`)
- [ ] At least 2 GB disk space available
- [ ] Git is available (`git --version`)
- [ ] You're in the `/app` directory

Check:

```bash
docker --version
docker-compose --version
df -h | grep -E "/$|/home|/var"  # Check disk space
cd /app && pwd
```

## ✅ Files Created

Verify all files exist in `/app/docker/`:

- [ ] `docker-compose.dev-simple.yml` (fast setup)
- [ ] `docker-compose.dev.yml` (full setup)
- [ ] `start-dev-container.sh` (startup script)
- [ ] `QUICK-START.md` (quick reference)
- [ ] `README.md` (overview)
- [ ] `DEV-CONTAINER-GUIDE.md` (detailed guide)
- [ ] `SETUP-GUIDE.txt` (visual guide)
- [ ] `ARCHITECTURE.txt` (technical details)
- [ ] `CHECKLIST.md` (this file)

Check:

```bash
cd /app/docker && ls -1 *.yml *.sh *.md *.txt
```

## ✅ Startup Process

### Step 1: Start Container

```bash
cd /app
bash docker/start-dev-container.sh
```

- [ ] Script runs without errors
- [ ] Menu appears
- [ ] Can select option 1 or 2

### Step 2: Choose Setup

```
Choose option [1-6]: 1
```

- [ ] Option 1 selected (simple setup)
- [ ] Container starts
- [ ] See "Container started!" message
- [ ] Port 8088 accessible

### Step 3: Container Setup

```
... (wait 2-3 minutes first run)
```

- [ ] Docker image pulls successfully
- [ ] Setup script runs
- [ ] No errors during installation
- [ ] See "Setup complete!" message

### Step 4: Access Container

```bash
docker exec -it autoarr-dev /bin/bash
```

- [ ] Shell opens inside container
- [ ] Prompt shows (root or similar)
- [ ] Can run `poetry --version`
- [ ] Can run `pnpm --version`
- [ ] Can run `node --version`

## ✅ Backend Setup

Inside the container, run:

```bash
poetry run python -m uvicorn autoarr.api.main:app --host 0.0.0.0 --port 8088 --reload
```

- [ ] Server starts without errors
- [ ] See "Uvicorn running on..."
- [ ] Port 8088 is available
- [ ] No import errors

### Test Backend

```bash
# In another terminal (outside container):
curl http://localhost:8088/health
```

- [ ] Returns 200 OK status
- [ ] See JSON response
- [ ] Backend is responding

### Test API Docs

- [ ] Open http://localhost:8088/docs in browser
- [ ] Swagger UI loads
- [ ] Can see API endpoints

## ✅ Frontend Setup

Inside another container shell:

```bash
cd autoarr/ui
pnpm dev
```

- [ ] Vite dev server starts
- [ ] See "ready in XXms"
- [ ] Port 3000 is ready
- [ ] No build errors

### Test Frontend

- [ ] Open http://localhost:3000 in browser
- [ ] React app loads
- [ ] Page shows without errors
- [ ] No console errors

## ✅ Live Reload Verification

### Backend Reload

1. Backend server running on 8088
2. Edit a file in `/app/autoarr/api/`
3. Save the file
4. Check backend logs
5. [ ] See "Reloading..." message
6. [ ] Server restarts (~2 seconds)
7. [ ] Try API again, see new changes

### Frontend Reload

1. Frontend server running on 3000
2. Edit a file in `/app/autoarr/ui/src/`
3. Save the file
4. Check browser
5. [ ] Page updates without full refresh
6. [ ] State preserved (if applicable)
7. [ ] Component reflects changes

## ✅ Testing

### Run Python Tests

```bash
poetry run pytest tests/unit/
```

- [ ] Tests run without errors
- [ ] Tests complete successfully
- [ ] See test summary

### Run Frontend Tests

```bash
cd autoarr/ui
pnpm test
```

- [ ] Tests run
- [ ] See test results

### Run All Tests

```bash
poetry run test
```

- [ ] Full test suite runs
- [ ] See coverage report
- [ ] Coverage shows reasonable percentage

## ✅ Code Formatting

### Format Python

```bash
poetry run format
```

- [ ] No errors
- [ ] Files formatted

### Format Frontend

```bash
cd autoarr/ui && pnpm run format
```

- [ ] No errors
- [ ] Files formatted

## ✅ Troubleshooting

If any step fails, check:

- [ ] Read QUICK-START.md
- [ ] Read README.md troubleshooting section
- [ ] Read DEV-CONTAINER-GUIDE.md
- [ ] Check `docker logs -f autoarr-dev`
- [ ] Verify `.env` file exists (if needed)
- [ ] Check disk space (`df -h`)
- [ ] Check Docker is running (`docker ps`)
- [ ] Try stopping and restarting (`docker-compose down && docker-compose up -d`)

## ✅ Optional: Full Setup

If you want Redis and PostgreSQL:

### Stop Current Container

```bash
cd docker && docker-compose down
```

### Start Full Setup

```bash
bash start-dev-container.sh
# Choose option 2
```

- [ ] All services start (autoarr, redis, postgres)
- [ ] See all containers in `docker ps`
- [ ] Same API/UI work as before

### Test Redis Connection

```bash
docker exec autoarr-dev redis-cli ping
```

- [ ] Returns "PONG"

### Test PostgreSQL Connection

```bash
docker exec autoarr-postgres psql -U autoarr -c "SELECT 1"
```

- [ ] Returns 1
- [ ] Database is accessible

## ✅ Daily Usage

After everything works:

1. [ ] Read the QUICK-START.md daily reference
2. [ ] Keep container running between sessions
3. [ ] Use `docker exec -it autoarr-dev /bin/bash` to access
4. [ ] Edit code in your editor
5. [ ] See changes instantly
6. [ ] Run tests as needed
7. [ ] Format code before committing

## ✅ Maintenance

### Regular Tasks

- [ ] Update dependencies: `poetry install`
- [ ] Check for updates: `poetry update`
- [ ] Clean cache: `docker system prune`

### If Issues Arise

- [ ] Check logs: `docker logs -f autoarr-dev`
- [ ] Rebuild: `docker-compose down -v && docker-compose up -d`
- [ ] Check docs in `/app/docs/`

## ✅ Success Criteria

You're done when:

✅ Container starts and stays running
✅ Backend serves on http://localhost:8088
✅ Frontend loads on http://localhost:3000
✅ API Docs available at http://localhost:8088/docs
✅ Code changes reload automatically
✅ Tests run successfully
✅ Code formats without errors
✅ You can edit and see changes instantly

## 🎯 Final Step

```bash
# Make sure you're in the right directory
cd /app

# Start the container
bash docker/start-dev-container.sh

# Follow the prompts
```

When everything works, you're ready to develop! 🚀

## 📞 Need Help?

1. **Quick answers:** QUICK-START.md
2. **Detailed guide:** DEV-CONTAINER-GUIDE.md
3. **Technical details:** ARCHITECTURE.txt
4. **General troubleshooting:** README.md

---

**Status:** Ready for development
**Last Updated:** 2025-01-23
**Next Step:** Run `bash docker/start-dev-container.sh`
