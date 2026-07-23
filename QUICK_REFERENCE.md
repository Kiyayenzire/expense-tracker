# ETA Expense Tracker - Quick Reference Guide

## ⚡ Super Quick Start (5 Minutes)

```bash
# 1. Start everything
docker compose -f docker-compose.dev.yml up --build

# 2. Open browser
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000/api/

# 3. Create admin user (in another terminal)
docker compose exec backend python manage.py createsuperuser

# 4. Login at http://localhost:5173
# Use admin credentials you just created
```

---

## 🔧 Common Development Commands

### Running Tests
```bash
# All tests
docker compose exec backend pytest tests/ -v

# Just unit tests
docker compose exec backend pytest tests/unit/ -v

# Just integration tests
docker compose exec backend pytest tests/integration/ -v

# Just e2e tests
docker compose exec backend pytest tests/e2e/ -v

# Specific test file
docker compose exec backend pytest tests/unit/test_services.py -v

# Specific test
docker compose exec backend pytest tests/unit/test_services.py::TestCurrencyService -v

# With coverage
docker compose exec backend pytest tests/ --cov=expenses
```

### Database Operations
```bash
# Create migrations
docker compose exec backend python manage.py makemigrations

# Apply migrations
docker compose exec backend python manage.py migrate

# Reset database (⚠️ DELETES ALL DATA)
docker compose exec backend python manage.py flush

# Django shell
docker compose exec backend python manage.py shell

# Dump data
docker compose exec backend python manage.py dumpdata > backup.json

# Load data
docker compose exec backend python manage.py loaddata backup.json

# Create sample data
docker compose exec backend python manage.py seed_data
```

### Backend Development
```bash
# View logs
docker compose logs -f backend

# Rebuild backend image
docker compose build backend

# Restart backend service
docker compose restart backend

# Run linting
docker compose exec backend flake8 expenses/

# Format code
docker compose exec backend black expenses/

# Type checking
docker compose exec backend mypy expenses/
```

### Frontend Development
```bash
# View logs
docker compose logs -f frontend

# Rebuild frontend image
docker compose build frontend

# Restart frontend service
docker compose restart frontend

# Access Vite dev server
# Already running at http://localhost:5173
```

### Database Inspection
```bash
# Connect to PostgreSQL
docker compose exec db psql -U etauser -d eta

# SQL Commands inside psql:
# \l              - List all databases
# \d              - List all tables
# SELECT * FROM expenses_expenseentry;
# \q              - Quit

# Or connect directly
docker compose exec db psql -U etauser -d eta -c "SELECT COUNT(*) FROM expenses_expenseentry;"
```

### Redis Operations
```bash
# Connect to Redis
docker compose exec redis redis-cli

# Commands:
# PING              - Test connection
# KEYS *            - List all keys
# GET key_name      - Get value
# FLUSHDB          - Clear database (⚠️)
# INFO             - Server info
```

### Celery Operations
```bash
# View Celery logs
docker compose logs -f celery_worker

# View Celery Beat logs
docker compose logs -f celery_beat

# Check Celery tasks status
docker compose exec backend python manage.py shell
>>> from celery.app.control import Inspect
>>> inspect = Inspect()
>>> inspect.active()  # Active tasks
>>> inspect.scheduled()  # Scheduled tasks

# Manually trigger currency rate update
docker compose exec backend python manage.py shell
>>> from expenses.tasks import update_currency_rates
>>> update_currency_rates.delay()
```

---

## 📁 File Locations

### Important Files
| File | Purpose |
|------|---------|
| `backend/expenses/services/` | Core business logic |
| `backend/expenses/views.py` | API endpoints |
| `backend/expenses/models.py` | Database models |
| `frontend/src/components/Dashboard.jsx` | Main UI component |
| `docker-compose.dev.yml` | Development setup |
| `docker-compose.prod.yml` | Production setup |
| `backend/requirements/base.txt` | Python dependencies |
| `frontend/package.json` | Node dependencies |

---

## 🐛 Debugging Tips

### Backend Debugging
```python
# In Django shell
docker compose exec backend python manage.py shell

# Import models
from expenses.models import ExpenseEntry, Category
from accounts.models import User

# Query data
user = User.objects.first()
expenses = ExpenseEntry.objects.filter(user=user)

# Test services
from expenses.services.currency_service import CurrencyService
rate = CurrencyService.get_latest_rate('EUR', 'USD')

from expenses.services.summary_service import SummaryService
summary = SummaryService(user).get_daily_summary()
```

### Frontend Debugging
```javascript
// Browser console (F12)
fetch('/api/expenses/', {
  headers: {'Authorization': 'Token YOUR_TOKEN'}
})
.then(r => r.json())
.then(d => console.log(d))

// Check local storage
localStorage.getItem('token')
localStorage.getItem('user')
```

### Docker Debugging
```bash
# View all running containers
docker ps

# View all containers (including stopped)
docker ps -a

# View container logs
docker compose logs backend

# Follow logs in real-time
docker compose logs -f backend

# View last 50 lines
docker compose logs --tail 50 backend

# Execute command in container
docker compose exec backend bash

# Check container resource usage
docker stats

# Inspect container
docker inspect eta-backend-1
```

---

## 🔑 Environment Variables

### Development (.env.dev)
```env
# Django
DJANGO_SECRET_KEY=dev-insecure-secret-key-do-not-use-in-production
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Database
DATABASE_URL=postgresql://etauser:etapass@db:5432/eta

# Redis
REDIS_URL=redis://redis:6379/0

# Celery
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# API Keys
FIXER_API_KEY=test  # Use free exchangerate.host in dev
```

### Production (.env.prod)
```env
# Generate with: python -c "import secrets; print(secrets.token_urlsafe(50))"
DJANGO_SECRET_KEY=<generate-new>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database (Use managed service on DigitalOcean)
DATABASE_URL=postgresql://user:pass@host:5432/database

# Use real API keys
FIXER_API_KEY=your-api-key
```

---

## 📊 Testing Strategy

### Unit Tests
```bash
# Test a service
docker compose exec backend pytest tests/unit/test_services.py::TestCurrencyService -v

# Test a model
docker compose exec backend pytest tests/unit/test_example.py::TestUserModel -v
```

### Integration Tests
```bash
# Test API endpoint
docker compose exec backend pytest tests/integration/test_example.py::TestExpenseEntryAPIContract::test_list_expenses_authenticated -v

# Test full workflow
docker compose exec backend pytest tests/integration/test_example.py::TestExpenseEntryAPIContract -v
```

### E2E Tests
```bash
# Test complete user flow
docker compose exec backend pytest tests/e2e/test_example.py::TestUserExpenseWorkflow -v
```

### Coverage Report
```bash
# Generate coverage report
docker compose exec backend pytest tests/ --cov=expenses --cov-report=html

# View report
open htmlcov/index.html  # macOS
# or open in browser: file://path/to/htmlcov/index.html
```

---

## 🚀 Deployment Checklist

### Pre-Deployment
```bash
# 1. Run all tests
docker compose exec backend pytest tests/ -v
# Should show: 91 passed

# 2. Check code style
docker compose exec backend flake8 expenses/

# 3. Build production images
docker build -f backend/Dockerfile -t eta-backend:latest backend/
docker build -f frontend/Dockerfile -t eta-frontend:latest frontend/

# 4. Test production compose file
docker compose -f docker-compose.prod.yml build

# 5. Create production .env
cp .env.prod.example .env.prod
# Edit with production values
```

### Deployment
```bash
# 1. Push images to registry
docker push eta-backend:latest
docker push eta-frontend:latest

# 2. Pull on server
docker pull eta-backend:latest
docker pull eta-frontend:latest

# 3. Start services
docker compose -f docker-compose.prod.yml up -d

# 4. Check status
docker compose -f docker-compose.prod.yml ps

# 5. View logs
docker compose -f docker-compose.prod.yml logs -f
```

---

## 💾 Backup & Restore

### Manual Backup
```bash
# Backup database
docker compose exec db pg_dump -U etauser -d eta | gzip > eta_backup.sql.gz

# Backup volumes
docker run --rm -v eta_postgres_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/volumes_backup.tar.gz -C /data .
```

### Restore Backup
```bash
# Restore database
gunzip < eta_backup.sql.gz | docker compose exec -T db psql -U etauser -d eta

# Restore volumes
docker run --rm -v eta_postgres_data:/data -v $(pwd):/backup \
  alpine tar xzf /backup/volumes_backup.tar.gz -C /data
```

---

## 📈 Monitoring Queries

### Database Monitoring
```sql
-- Connect to database
docker compose exec db psql -U etauser -d eta

-- Count total expenses
SELECT COUNT(*) FROM expenses_expenseentry;

-- Most common categories
SELECT category_id, COUNT(*) FROM expenses_expenseentry 
GROUP BY category_id ORDER BY COUNT(*) DESC;

-- Total spending by user
SELECT user_id, SUM(amount) FROM expenses_expenseentry 
GROUP BY user_id;

-- Recent expenses
SELECT * FROM expenses_expenseentry 
ORDER BY date DESC LIMIT 10;
```

### API Health Check
```bash
# Test API is responding
curl http://localhost:8000/api/categories/

# Test with authentication
curl -H "Authorization: Token YOUR_TOKEN" \
  http://localhost:8000/api/expenses/

# Check response time
time curl http://localhost:8000/api/categories/
```

---

## 🔐 Security Checklist

### Development
- [ ] Use `.env.dev` (development secrets OK)
- [ ] `DJANGO_DEBUG=True` is OK for development
- [ ] All tests passing

### Before Deploying to Production
- [ ] Generate new `DJANGO_SECRET_KEY`
- [ ] Set `DJANGO_DEBUG=False`
- [ ] Update `DJANGO_ALLOWED_HOSTS`
- [ ] Create strong database passwords
- [ ] Setup SSL certificates
- [ ] Configure CORS for your domain only
- [ ] Setup firewall rules
- [ ] Enable database backups
- [ ] Configure error monitoring

---

## 🆘 Troubleshooting

### Container Won't Start
```bash
# View detailed error
docker compose logs backend

# Rebuild and restart
docker compose down
docker compose build --no-cache backend
docker compose up backend
```

### Database Connection Error
```bash
# Check database is running
docker compose ps db

# Check database credentials in .env
# Verify database exists
docker compose exec db psql -U etauser -d eta -c "\l"

# Recreate database
docker compose exec db dropdb -U etauser eta
docker compose exec db createdb -U etauser eta
docker compose exec backend python manage.py migrate
```

### Tests Failing
```bash
# Check test database setup
docker compose exec backend python manage.py migrate --database test_db

# Run tests with verbose output
docker compose exec backend pytest tests/ -vv

# Run specific test to debug
docker compose exec backend pytest tests/unit/test_services.py::TestCurrencyService::test_convert_amount -vv
```

### Memory Issues
```bash
# Check container memory usage
docker stats

# Limit container memory in docker-compose.yml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 512M

# Clear Docker cache
docker system prune -a
```

---

## 📚 Useful Links

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [React Documentation](https://react.dev/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [Docker Documentation](https://docs.docker.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

---

## 📞 Getting Help

1. **Check logs**: `docker compose logs -f`
2. **Run tests**: `pytest tests/ -v`
3. **Read documentation**: Check README.md and DEPLOYMENT_GUIDE.md
4. **Debug in shell**: `docker compose exec backend python manage.py shell`
5. **Search stack overflow**: Tag your question with `django`, `django-rest-framework`, `celery`

---

**Last Updated**: July 22, 2026  
**Status**: Production Ready ✅
