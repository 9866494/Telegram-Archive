<div align="center">
  <img src="assets/Telegram-Archive.png" alt="Telegram Archive Logo" width="200"/>
</div>

# Telegram Archive

Automated Telegram backup with Docker. Performs incremental backups of messages and media on a configurable schedule.

## Features

✨ **Incremental Backups** - Only downloads new messages since last backup
📅 **Scheduled Execution** - Configurable cron schedule
🐳 **Docker Ready** - Easy deployment with Docker Compose
🗄️ **Multiple Database Support** - SQLite and PostgreSQL with SQLAlchemy
🌐 **Web Viewer** - Browse chats with Telegram-like UI (mobile-friendly)
🔐 **Restricted Viewer** - Share specific chats via `DISPLAY_CHAT_IDS`
🎵 **Voice/Audio Player** - Play audio messages in browser
📤 **Chat Export** - Export chat history to JSON
🎬 **GIF Autoplay** - Animated GIFs play when visible
📁 **Media Support** - Photos, videos, documents, stickers
🔒 **Secure** - Optional authentication, runs as non-root  

## 📸 Screenshots

<details>
<summary>Click to view Desktop and Mobile screenshots</summary>

### Desktop
![Desktop View](assets/Telegram-Archive-1.png)

### Mobile
<img src="assets/Telegram-Archive-2.png" width="300" alt="Mobile View">

</details>

## Quick Start

### 1. Get Telegram API Credentials

1. Go to https://my.telegram.org/apps
2. Create a new application
3. Note your `API_ID` and `API_HASH`

### 2. Deploy with Docker

#### Option A: Using Pre-built Docker Hub Images (Recommended)

```bash
# Clone and configure
git clone https://github.com/GeiserX/telegram-backup-automation
cd telegram-backup-automation
cp .env.example .env
# Edit .env with your credentials

# Authenticate (one-time)
./init_auth.sh  # or init_auth.bat on Windows

# Start services using Docker Hub images
docker-compose -f docker-compose.hub.yml up -d
```

#### Option B: Build from Source

```bash
# Clone and configure
git clone https://github.com/GeiserX/telegram-backup-automation
cd telegram-backup-automation
cp .env.example .env
# Edit .env with your credentials

# Authenticate (one-time)
./init_auth.sh  # or init_auth.bat on Windows

# Start services (builds images locally)
docker-compose up -d
```

## Web Viewer

Browse your backups (saved locally) at **http://localhost:8000**

Features:
- Telegram-like dark UI
- Photo/video viewer
- Voice note player
- Chat search
- Export to JSON
- Mobile-friendly layout

## Configuration

### Required

| Variable | Description |
|----------|-------------|
| `TELEGRAM_API_ID` | API ID from my.telegram.org |
| `TELEGRAM_API_HASH` | API Hash from my.telegram.org |
| `TELEGRAM_PHONE` | Phone with country code (+1234567890) |

### Database Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_TYPE` | `sqlite` | Database type: `sqlite` or `postgres-alchemy` |
| `DATABASE_TIMEOUT` | `60.0` | Database connection timeout (seconds) |
| `DATABASE_DIR` | Same as backup | Database directory location |
| `DATABASE_PATH` | Derived from above | Full database file path |

**PostgreSQL (when DB_TYPE=postgres-alchemy):**
| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_HOST` | `postgres` | PostgreSQL server host |
| `POSTGRES_PORT` | `5432` | PostgreSQL server port |
| `POSTGRES_DB` | `telegram_backup` | Database name |
| `POSTGRES_USER` | `telegram` | Database user |
| `POSTGRES_PASSWORD` | *Required* | Database password |
| `POSTGRES_POOL_SIZE` | `5` | Connection pool size |

### Optional Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `SCHEDULE` | `0 */6 * * *` | Cron schedule (every 6 hours) |
| `BACKUP_PATH` | `/data/backups` | Backup storage path |
| `DOWNLOAD_MEDIA` | `true` | Download media files |
| `MAX_MEDIA_SIZE_MB` | `100` | Max media file size |
| `CHAT_TYPES` | `private,groups,channels` | Types to backup |
| `LOG_LEVEL` | `INFO` | Logging level |
| `VIEWER_USERNAME` | - | Web viewer username |
| `VIEWER_PASSWORD` | - | Web viewer password |
| `VIEWER_TIMEZONE` | `Europe/Madrid` | Display timezone for viewer |
| `DISPLAY_CHAT_IDS` | - | Restrict viewer to specific chats |
| `SYNC_DELETIONS_EDITS` | `false` | Sync deletions/edits from Telegram |
| `BATCH_SIZE` | `100` | Messages per batch for processing |
| `GLOBAL_INCLUDE_CHAT_IDS` | - | Whitelist chats globally |
| `GLOBAL_EXCLUDE_CHAT_IDS` | - | Blacklist chats globally |
| `PRIVATE_INCLUDE_CHAT_IDS` | - | Whitelist private chats |
| `PRIVATE_EXCLUDE_CHAT_IDS` | - | Blacklist private chats |
| `GROUPS_INCLUDE_CHAT_IDS` | - | Whitelist group chats |
| `GROUPS_EXCLUDE_CHAT_IDS` | - | Blacklist group chats |
| `CHANNELS_INCLUDE_CHAT_IDS` | - | Whitelist channels |
| `CHANNELS_EXCLUDE_CHAT_IDS` | - | Blacklist channels |

## CLI Commands

```bash
# View statistics
docker-compose exec telegram-backup python -m src.export_backup stats

# List chats
docker-compose exec telegram-backup python -m src.export_backup list-chats

# Export to JSON
docker-compose exec telegram-backup python -m src.export_backup export -o backup.json

# Export date range
docker-compose exec telegram-backup python -m src.export_backup export -o backup.json -s 2024-01-01 -e 2024-12-31

# Manual backup run
docker-compose exec telegram-backup python -m src.telegram_backup

# Test database adapters
docker-compose exec telegram-backup python -m src.db_adapters.postgres_adapter
docker-compose exec telegram-backup python -m src.db_adapters.sqlite_adapter
```

## Docker Hub Images

Pre-built Docker images are available on Docker Hub:

- **Backup Service**: `awful/telegram-archive-backup`
- **Viewer Service**: `awful/telegram-archive-viewer`

### Using Docker Hub Images

Use the provided `docker-compose.hub.yml` file:

```bash
docker-compose -f docker-compose.hub.yml up -d
```

### Publishing Images

To publish new versions to Docker Hub:

```bash
# Login to Docker Hub first
docker login

# Publish latest versions
./publish-docker.sh

# Publish with specific version tag
./publish-docker.sh v1.0.0
```

This will:
1. Build separate images for backup and viewer services
2. Tag them as `awful/telegram-archive-backup:VERSION` and `awful/telegram-archive-viewer:VERSION`
3. Push both images to Docker Hub

### Image Variants

- **latest**: Most recent stable release
- **vX.Y.Z**: Versioned releases for reproducible deployments

## Database Migration

The project supports both SQLite and PostgreSQL databases through SQLAlchemy adapters.

### Switching between databases:

**SQLite (default):**
```bash
# No additional setup required
# Uses: sqlite (default) or sqlite-alchemy
DB_TYPE=sqlite
```

**PostgreSQL:**
```bash
# 1. Start PostgreSQL service
docker-compose up -d postgres

# 2. Set environment variables
DB_TYPE=postgres-alchemy
POSTGRES_PASSWORD=your_password

# 3. Restart services
docker-compose restart telegram-backup telegram-viewer
```

### Migration from SQLite to PostgreSQL:

```bash
# 1. Export existing data
docker-compose exec telegram-backup python -m src.export_backup export -o backup.json

# 2. Switch to PostgreSQL
# Edit .env: DB_TYPE=postgres-alchemy, set POSTGRES_PASSWORD

# 3. Restart with new database
docker-compose down
docker-compose up -d postgres telegram-backup telegram-viewer
```

## Data Storage

```
data/
├── session/
│   └── telegram_backup.session
└── backups/
    ├── telegram_backup.db
    └── media/
        └── {chat_id}/
            └── {files}
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Failed to authorize" | Run `./init_auth.sh` again |
| "Permission denied" | `chmod -R 755 data/` |

## Limitations

- Secret chats not supported (API limitation)
- Edit history not tracked (only latest version stored; enable `SYNC_DELETIONS_EDITS` to update edits)
- Deleted messages before first backup cannot be recovered

## License

GPL-3.0. See [LICENSE](LICENSE) for details.

Built with [Telethon](https://github.com/LonamiWebs/Telethon).
