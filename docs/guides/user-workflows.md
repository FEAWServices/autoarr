# AutoArr User Guide: Common Workflows

> **Complete guide to using AutoArr for intelligent media automation**

This guide covers all the common workflows you'll use in AutoArr, from initial setup through daily operations. AutoArr is your intelligent assistant for managing SABnzbd, Sonarr, Radarr, and Plex.

---

## Table of Contents

- [Getting Started](#getting-started)
  - [First Launch](#first-launch)
  - [Initial Configuration](#initial-configuration)
- [Daily Operations](#daily-operations)
  - [Requesting Content](#requesting-content)
  - [Monitoring Downloads](#monitoring-downloads)
  - [Viewing Activity](#viewing-activity)
- [Optimization](#optimization)
  - [Running Configuration Audits](#running-configuration-audits)
  - [Applying Recommendations](#applying-recommendations)
- [Advanced Features](#advanced-features)
  - [Managing Settings](#managing-settings)
  - [Understanding Health Scores](#understanding-health-scores)
- [Troubleshooting](#troubleshooting)

---

## Getting Started

### First Launch

When you first access AutoArr, you'll see the **Welcome Screen** that introduces you to the platform and guides you through setup.

#### What You'll See

- **Hero section** with the AutoArr logo and tagline
- **Service status** showing which services are connected
- **Service cards** for SABnzbd, Sonarr, Radarr, and Plex
- **Feature overview** highlighting key capabilities

#### Understanding Service Status

Each service card displays one of three states:

- 🟢 **Connected** - Service is configured and reachable
- 🟡 **Not Reachable** - Service is configured but AutoArr can't connect
- ⚪ **Not Configured** - Service needs to be set up

---

### Initial Configuration

To unlock AutoArr's full potential, you need to connect your media services.

#### Step 1: Access Settings

Click the **"Configure Services"** button on the Welcome screen, or navigate to **Settings** from the sidebar.

#### Step 2: Configure Each Service

For each service you want to connect:

##### SABnzbd (Download Client)

1. **Enable the service** by toggling it on
2. **Enter the URL** (e.g., `http://192.168.1.100:8080/sabnzbd/`)
   - Include the full path if SABnzbd uses a base URL
3. **Add your API key**
   - Find it in SABnzbd: Config → General → Security → API Key
4. **Set timeout** (default: 30 seconds is usually fine)
5. **Click "Test Connection"** to verify
6. **Save** when the test succeeds

##### Sonarr (TV Shows)

1. **Enable the service**
2. **Enter the URL** (e.g., `http://192.168.1.100:8989`)
3. **Add your API key**
   - Find it in Sonarr: Settings → General → Security → API Key
4. **Test and save**

##### Radarr (Movies)

1. **Enable the service**
2. **Enter the URL** (e.g., `http://192.168.1.100:7878`)
3. **Add your API key**
   - Find it in Radarr: Settings → General → Security → API Key
4. **Test and save**

##### Plex (Media Server - Optional)

1. **Enable the service**
2. **Enter the URL** (e.g., `http://192.168.1.100:32400`)
3. **Add your Plex token**
   - See: [Finding Your Plex Token](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/)
4. **Test and save**

#### Step 3: Verify Connections

After configuring services, you should see:

- ✅ Green checkmarks for successfully connected services
- The Welcome screen transforms into your main dashboard
- Feature cards become interactive and functional

---

## Daily Operations

### Requesting Content

AutoArr's **Natural Language Interface** makes requesting content as easy as chatting with a friend.

#### Accessing the Chat Interface

- Click the **Home** icon (chat bubble) in the sidebar, or
- Click the **"Natural Language Requests"** feature card on the Welcome screen

#### Making a Request

1. **Type your request** in natural language in the message box

   **Examples:**
   - "Add the new Dune movie in 4K"
   - "I want to watch Breaking Bad"
   - "Download Inception"
   - "Add the latest season of The Mandalorian"

2. **Send the message** by clicking the send button or pressing Enter

3. **AutoArr will analyze your request** and:
   - Determine if it's a movie or TV show
   - Search for matching titles
   - Present options if multiple matches are found

4. **Confirm the selection** when prompted
   - Review the title, year, and other details
   - Click "Yes" to confirm or "No" to search again

5. **Track the request** in real-time
   - See when it's added to Sonarr/Radarr
   - Monitor download progress
   - Get notified when complete

#### Chat Features

- **History** - All your conversations are saved
- **Search** - Click the search icon to find past requests
- **Clear History** - Use the trash icon to start fresh
- **Status Updates** - Real-time progress for active downloads

#### Understanding Request Status

- 🔵 **Processing** - AutoArr is analyzing your request
- 🟡 **Searching** - Looking for the content
- 🟢 **Downloading** - Added to download queue
- ✅ **Completed** - Download finished
- ❌ **Failed** - Something went wrong (AutoArr will suggest next steps)

---

### Monitoring Downloads

The **Downloads** page provides real-time visibility into your download queue.

#### Accessing Download Monitoring

Navigate to **Downloads** from the sidebar (requires SABnzbd connection).

#### What You'll See

- **Active downloads** with progress bars
- **Download speed** and ETA
- **Queue position** and priority
- **Recent history** of completed/failed downloads

#### Actions You Can Take

- **Pause/Resume** individual downloads
- **Prioritize** important downloads
- **Retry failed** downloads (if automatic recovery didn't work)
- **View details** for troubleshooting

> **Note:** If SABnzbd isn't connected, you'll see a prompt to configure it with helpful setup information.

---

### Viewing Activity

The **Activity** page shows a comprehensive log of everything happening in AutoArr.

#### Accessing Activity

Click **Activity** in the sidebar to view the activity feed.

#### Types of Activities

- 📥 **Content Requests** - Movies/TV shows you've requested
- 🔄 **Download Events** - Started, completed, failed downloads
- ⚙️ **Configuration Changes** - Settings updates
- 🤖 **Automatic Actions** - Recovery attempts, optimizations
- 🔔 **System Events** - Health checks, connection status

#### Using Activity Logs

- **Real-time updates** - New activities appear instantly via WebSocket
- **Filter by type** - Focus on specific event categories
- **Search history** - Find specific events
- **Export logs** - Download for troubleshooting

---

## Optimization

### Running Configuration Audits

AutoArr uses AI to analyze your service configurations and recommend optimizations.

#### Accessing Configuration Audit

1. Navigate to **Settings** → **Configuration Audit** tab, or
2. Click the **"Configuration Audit"** feature card

#### Starting an Audit

1. **Click "Run Audit"** to begin analysis
2. **Wait for completion** (usually 30-60 seconds)
   - AutoArr checks each connected service
   - Compares settings against best practices
   - Uses AI to prioritize recommendations

3. **Review results** organized by priority:
   - 🔴 **Critical** - Issues that may cause problems
   - 🟡 **Important** - Optimizations that improve performance
   - 🟢 **Optional** - Nice-to-have improvements

#### Understanding Recommendations

Each recommendation includes:

- **Clear title** - What needs to change
- **Current vs. Recommended** - Side-by-side comparison
- **Impact explanation** - Why this matters
- **Service affected** - Which app needs the change
- **Confidence score** - How certain AutoArr is

---

### Applying Recommendations

After reviewing audit results, you can apply changes directly through AutoArr.

#### Manual Application (Recommended)

For each recommendation:

1. **Read the explanation** to understand the change
2. **Click "View Details"** for more context
3. **Apply in the service directly**
   - Use the provided instructions
   - Make changes in Sonarr/Radarr/SABnzbd settings
4. **Mark as "Applied"** in AutoArr to track progress

#### Automatic Application (Future Feature)

> **Coming Soon:** One-click application of recommendations with automatic rollback.

#### After Applying Changes

1. **Run another audit** to verify improvements
2. **Check health scores** on the dashboard
3. **Monitor** for any issues in the Activity feed

---

## Advanced Features

### Managing Settings

The Settings page is your control center for AutoArr configuration.

#### Settings Tabs

##### Services

- **Configure connections** to all services
- **Test connectivity** before saving
- **Enable/disable** services as needed
- **Update API keys** and URLs

##### Claude API (AI Features)

- **API Key** - Required for natural language requests and configuration audits
- **Model selection** - Choose which Claude model to use
- **Usage tracking** - Monitor API consumption

##### Appearance

- **Theme** - Light, dark, or auto (system)
- **Accent colors** - Customize the interface
- **Density** - Compact or comfortable layout

##### Notifications

- **Event types** - Choose what triggers notifications
- **Delivery methods** - Browser, email, webhooks
- **Quiet hours** - Pause notifications during specific times

#### Best Practices

- **Keep API keys secure** - Never share them
- **Test connections regularly** - Especially after IP changes
- **Document your settings** - Note custom configurations
- **Back up your configuration** - Export settings before major changes

---

### Understanding Health Scores

AutoArr provides health scores for each connected service and an overall system score.

#### Where to Find Health Scores

- **Dashboard** - Main overview on the Home page
- **Service cards** - Individual scores per service
- **Settings** - Detailed breakdown in Configuration Audit

#### Score Breakdown

- **90-100** 🟢 Excellent - Optimally configured
- **70-89** 🟡 Good - Minor improvements possible
- **50-69** 🟠 Fair - Several optimizations recommended
- **Below 50** 🔴 Poor - Critical issues need attention

#### Factors Affecting Scores

- **Connection stability** - Service reachability
- **Configuration quality** - Alignment with best practices
- **Download success rate** - Percentage of successful downloads
- **Response time** - API performance
- **Recent errors** - Any connection or operation failures

#### Improving Health Scores

1. **Run a configuration audit**
2. **Apply critical recommendations first**
3. **Fix connectivity issues** (wrong URLs, expired API keys)
4. **Update services** to latest versions
5. **Monitor and adjust** over time

---

## Troubleshooting

### Common Issues and Solutions

#### "Connection Failed" During Setup

**Problem:** Service won't connect when testing

**Solutions:**
1. **Verify the URL is correct**
   - Include protocol: `http://` or `https://`
   - Include port number: `:8080`, `:8989`, etc.
   - Include base URL if configured: `/sabnzbd/`

2. **Check the API key**
   - Copy-paste to avoid typos
   - Regenerate key in the service if needed

3. **Ensure service is running**
   - Access the service web UI directly
   - Check service logs for errors

4. **Verify network access**
   - Can AutoArr reach the service from its network?
   - Check firewall rules
   - Try accessing from AutoArr's container: `docker exec autoarr curl <service-url>`

#### No Natural Language Requests Working

**Problem:** Chat doesn't respond or returns errors

**Solutions:**
1. **Verify Claude API key is set**
   - Go to Settings → Claude API
   - Add a valid API key
   - Test the connection

2. **Check service connections**
   - Sonarr must be connected for TV requests
   - Radarr must be connected for movie requests
   - Go to Settings → Services and test each

3. **Review activity logs**
   - Check for specific error messages
   - Look for API rate limiting issues

#### Configuration Audit Fails

**Problem:** Audit doesn't complete or shows errors

**Solutions:**
1. **Ensure all services are connected**
   - Audit requires active connections to check settings
   - Fix any connection issues first

2. **Check Claude API status**
   - API key must be valid
   - Ensure you have API credits available

3. **Try services individually**
   - Some services may be blocking the audit
   - Check individual service logs for errors

#### Downloads Not Appearing

**Problem:** Requested content doesn't show in downloads

**Solutions:**
1. **Verify download client connection**
   - SABnzbd must be connected
   - Check that Sonarr/Radarr can reach SABnzbd

2. **Check Sonarr/Radarr indexers**
   - At least one indexer must be configured
   - Test indexers in Sonarr/Radarr settings

3. **Review quality profiles**
   - Ensure quality profiles allow the requested quality
   - Check for conflicts (e.g., requesting 4K without 4K profile)

4. **Check availability**
   - Content may not be available on your indexers
   - Try searching manually in Sonarr/Radarr

#### WebSocket Connection Issues

**Problem:** Real-time updates not working

**Solutions:**
1. **Refresh the page** - Reestablishes WebSocket connection
2. **Check browser console** for WebSocket errors
3. **Verify reverse proxy** settings if using one
   - WebSocket support must be enabled
   - Example nginx config:
     ```nginx
     location /ws {
         proxy_pass http://autoarr:8088;
         proxy_http_version 1.1;
         proxy_set_header Upgrade $http_upgrade;
         proxy_set_header Connection "upgrade";
     }
     ```
4. **Check firewall** - WebSocket port must be accessible

---

## Tips for Best Experience

### Getting the Most from AutoArr

1. **Start with configuration audit**
   - Run it immediately after setup
   - Apply critical recommendations
   - Establishes a solid foundation

2. **Use natural language liberally**
   - AutoArr understands casual language
   - "I want the new Spider-Man movie" works just as well as "Add Spider-Man: No Way Home"
   - Don't worry about being too specific

3. **Monitor activity regularly**
   - Check for patterns in failures
   - Understand what AutoArr is doing automatically
   - Catch issues early

4. **Keep services updated**
   - Update Sonarr, Radarr, SABnzbd regularly
   - Keep API keys current
   - Test connections after updates

5. **Review health scores weekly**
   - Quick indicator of system health
   - Proactive issue identification
   - Track improvements over time

### Keyboard Shortcuts

- **`/`** - Focus chat input (on chat page)
- **`Ctrl/Cmd + K`** - Quick search
- **`Ctrl/Cmd + ,`** - Open settings
- **`Esc`** - Close modals/dialogs

---

## What's Next?

### Learning More

- **[Quick Start Guide](quick-start.md)** - Initial installation and setup
- **[Troubleshooting Guide](troubleshooting.md)** - Comprehensive problem-solving
- **[API Documentation](../architecture/overview.md)** - For developers and advanced users
- **[Architecture Overview](../architecture/overview.md)** - How AutoArr works under the hood

### Getting Help

- **GitHub Issues** - Report bugs or request features
- **Community Discord** - Chat with other users
- **Documentation** - Comprehensive guides and references

### Contributing

AutoArr is open source! Contributions are welcome:

- Report bugs and suggest features
- Improve documentation
- Submit pull requests
- Share your AutoArr setup

---

## Quick Reference

### Essential URLs (Default Docker Installation)

- **AutoArr Dashboard:** http://localhost:8088
- **SABnzbd:** http://localhost:8080
- **Sonarr:** http://localhost:8989
- **Radarr:** http://localhost:7878
- **Plex:** http://localhost:32400

### Key File Locations (Docker)

- **Configuration:** `/config` (mounted volume)
- **Database:** `/data/autoarr.db`
- **Logs:** `/data/logs`
- **Cache:** `/data/cache`

### Support Resources

- **Documentation:** https://github.com/FEAWServices/autoarr/tree/main/docs
- **GitHub Issues:** https://github.com/FEAWServices/autoarr/issues
- **License:** GPL-3.0 (100% Free & Open Source)

---

**Happy Automating! 🎬📺**

*Last Updated: 2025-12-09*
