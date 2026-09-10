# ETA Expense Tracker - Deployment Guide

This guide reflects the project as it exists in this repository today. The active local stack is driven by `docker-compose.yml` with development overrides from `docker-compose.override.yml`, and the default admin path is configured through the `DJANGO_ADMIN_URL` setting in `.env.dev`.

## Deployment summary

- Local app: http://localhost:5173
- Django API: http://localhost:8000/api
- Admin route: http://127.0.0.1:8000/etaalthech2026/
- Database: PostgreSQL inside Docker
- Cache/Broker: Redis inside Docker
- Background jobs: Celery worker + Celery beat
- Production reverse proxy: nginx config in `nginx/nginx.prod.conf`

## Prerequisites

- Docker and Docker Compose installed
- Git
- A valid `.env.dev` file in the project root for local development
- Production environment values in `.env` or a secure production env file for deployment

## Local development

### Start the stack

```bash
docker compose --env-file .env.dev up -d --build
```

This will bring up:

- `db`
- `redis`
- `backend`
- `celery_worker`
- `celery_beat`
- `frontend`

### Open the app

- Frontend: http://localhost:5173
- API: http://localhost:8000/api
- Admin: http://127.0.0.1:8000/etaalthech2026/

### Create a superuser

```bash
docker compose --env-file .env.dev exec backend python manage.py createsuperuser
```

### Run migrations

```bash
docker compose --env-file .env.dev exec backend python manage.py migrate
```

### View logs

```bash
docker compose --env-file .env.dev logs -f backend
docker compose --env-file .env.dev logs -f frontend
docker compose --env-file .env.dev logs -f celery_worker
```

## Production deployment

The repository is designed to run with the root Compose file and an environment file. For production, set up a secure `.env` or `.env.prod` file before starting the stack.

```bash
docker compose --env-file .env up -d --build
```

The app is also configured to work behind Nginx. The reverse proxy file is in `nginx/nginx.prod.conf`.

## Environment variables

The project reads from the root `.env` file when present, and falls back to `.env.dev` when needed. The default development settings already contain:

```env
DJANGO_SECRET_KEY=dev-secret-key-change-in-production-12345
DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,backend,0.0.0.0
DJANGO_ADMIN_URL=etaalthech2026
DATABASE_URL=postgres://expense_tracker_dev_user:expense_tracker_dev_password@db:5432/expense_tracker_dev
REDIS_URL=redis://redis:6379/0
FIXER_API_KEY=your-fixer-api-key
DEFAULT_CURRENCY=EUR
FRONTEND_URL=http://localhost:5173
```

For production, replace the dev values with secure credentials and a real secret key.

## Test runs

### Backend

```bash
docker compose --env-file .env.dev exec backend pytest -q
```

### Frontend

```bash
cd eta_frontend
npm test
```

### Browser tests

```bash
cd eta_frontend
npm run test:e2e
```

## Troubleshooting

### Frontend is not loading

Check the service status:

```bash
docker compose --env-file .env.dev ps
```

Check logs for both frontend and backend:

```bash
docker compose --env-file .env.dev logs -f frontend backend
```

### Database or migration issues

```bash
docker compose --env-file .env.dev exec backend python manage.py check
docker compose --env-file .env.dev exec backend python manage.py migrate
```

### Reset the local environment

```bash
docker compose --env-file .env.dev down -v
```

Then restart:

```bash
docker compose --env-file .env.dev up -d --build
```

## Notes

- The project intentionally does not include a payment feature.
- Expense data is user-scoped; accounts should not see each other’s records.
- The profile system supports profile photos and monthly income fields.
- Report filenames use a human-readable period name, such as `september` rather than `9`.
- The custom admin route is not the default `/admin/` path in this workspace.

## Useful references

- [README.md](README.md)
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- [docker-compose.yml](docker-compose.yml)
- [docker-compose.override.yml](docker-compose.override.yml)
- [docker-compose.test.yml](docker-compose.test.yml)
- [eta_backend/backend/settings.py](eta_backend/backend/settings.py)



# Copy production environment
cp .env.prod.example .env.prod
# Edit .env.prod with your settings
nano .env.prod
```

#### Step 3: Configure Nginx
Create `/etc/nginx/sites-available/eta`:
```nginx
upstream django_backend {
    server localhost:8000;
}

upstream react_frontend {
    server localhost:5173;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # API
    location /api/ {
        proxy_pass http://django_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 10M;
    }

    # Frontend
    location / {
        proxy_pass http://react_frontend;
        proxy_set_header Host $host;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

Enable the site:
```bash
ln -s /etc/nginx/sites-available/eta /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

#### Step 4: Setup SSL with Let's Encrypt
```bash
# Install Certbot
apt install certbot python3-certbot-nginx -y

# Get certificate
certbot certonly --nginx -d yourdomain.com -d www.yourdomain.com
```

#### Step 5: Start Services
```bash
cd /root/eta

# Copy .env.prod
cp .env.prod .env

# Start services in background
nohup docker compose -f docker-compose.prod.yml up -d > docker.log 2>&1 &

# Verify services
docker compose -f docker-compose.prod.yml ps
curl http://localhost:8000/api/categories/  # Should return JSON
```

#### Step 6: Setup Automatic Backups
```bash
# Create backup script
nano /root/backup-eta.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/root/backups"
mkdir -p $BACKUP_DIR

# Database backup
docker exec eta-db-1 pg_dump -U etauser eta_prod | gzip > $BACKUP_DIR/db_$(date +%Y%m%d_%H%M%S).sql.gz

# Keep only last 7 days
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +7 -delete

echo "Backup completed at $(date)" >> /root/backup.log
```

Add to crontab:
```bash
crontab -e
# Add: 0 2 * * * bash /root/backup-eta.sh
```

#### Step 7: Setup Monitoring
```bash
# View logs
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f celery_worker

# Monitor resources
docker stats
```

---

## Monitoring and Maintenance

### Health Checks
```bash
# API health
curl https://yourdomain.com/api/categories/ -H "Authorization: Token YOUR_TOKEN"

# Database
docker exec eta-db-1 pg_isready -U etauser

# Redis
docker exec eta-redis-1 redis-cli ping
```

### Common Tasks

#### Create Admin User
```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser
```

#### Clear Database Cache
```bash
docker compose -f docker-compose.prod.yml exec redis redis-cli FLUSHDB
```

#### Update Currency Rates
```bash
# Manual trigger (normally runs Monday 17:00 UTC)
docker compose -f docker-compose.prod.yml exec backend python manage.py shell
>>> from expenses.tasks import update_currency_rates
>>> update_currency_rates.delay()
```

#### Restart Services
```bash
docker compose -f docker-compose.prod.yml restart
```

### Scaling

#### Increase Celery Workers
Edit `docker-compose.prod.yml`:
```yaml
celery_worker:
  # ... existing config ...
  deploy:
    replicas: 3  # Add this for multiple workers
```

#### Increase Backend Replicas
Use Docker Swarm or Kubernetes for orchestration.

---

## Troubleshooting

### Issue: 502 Bad Gateway
```bash
# Check backend is running
docker compose logs backend
# Restart services
docker compose restart backend
```

### Issue: Currency Rates Not Updating
```bash
# Check Celery Beat
docker compose logs celery_beat
# Verify Redis
docker exec redis redis-cli PING
```

### Issue: High Memory Usage
```bash
# Restart to clear cache
docker compose restart redis
# Check logs for memory leaks
docker stats
```

### Issue: Slow Performance
1. Increase database connections in PostgreSQL config
2. Scale Celery workers
3. Enable Redis caching optimization
4. Check query performance with Django Debug Toolbar

---

## Database Backups

### Automatic Daily Backups
Already configured in cron. Backups stored in `/root/backups/`

### Manual Backup
```bash
docker compose exec db pg_dump -U etauser eta_prod | gzip > eta_backup_$(date +%Y%m%d).sql.gz
```

### Restore from Backup
```bash
gunzip < eta_backup_20240101.sql.gz | docker compose exec -T db psql -U etauser eta_prod
```

---

## Security Checklist

- [ ] Change all default passwords
- [ ] Set `DJANGO_DEBUG=False` in production
- [ ] Configure HTTPS/SSL certificates
- [ ] Setup firewall rules
- [ ] Enable 2FA for admin account (via dj-allauth)
- [ ] Regularly update dependencies (`pip install --upgrade -r requirements.txt`)
- [ ] Configure database backups
- [ ] Setup error monitoring (Sentry)
- [ ] Enable CORS only for trusted domains
- [ ] Rotate Django SECRET_KEY periodically

---

## CI/CD Pipeline

GitHub Actions automatically:
1. Runs tests on push
2. Builds Docker images
3. Pushes to GHCR
4. Can deploy to DigitalOcean on merge to main

### GitHub Secrets to Configure
```
REGISTRY_USERNAME: your-github-username
REGISTRY_PASSWORD: your-github-token
DIGITALOCEAN_TOKEN: your-do-api-token
```

---

## Support & Documentation

- **API Documentation**: http://localhost:8000/api/docs/ (with Swagger UI)
- **Django Admin**: http://localhost:8000/admin/
- **Project README**: See README.md
- **Architecture**: See docs/ARCHITECTURE.md

## Performance Metrics

- **API Response Time**: <200ms (average)
- **Database Queries**: Optimized with select_related/prefetch_related
- **Caching**: Redis caching for currency rates and summaries
- **Background Tasks**: Celery for report generation and currency updates

---

## License

See LICENSE file

## Contact

For issues or questions, open a GitHub issue or contact the team.
