# ETA Expense Tracker - Quick Reference

## Start the app

```bash
docker compose --env-file .env.dev up -d --build
```

Open:

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000/api
- Admin: http://127.0.0.1:8000/etaalthech2026/

## Common commands

### Create a superuser

```bash
docker compose --env-file .env.dev exec backend python manage.py createsuperuser
```

### Run migrations

```bash
docker compose --env-file .env.dev exec backend python manage.py migrate
```

### Run backend tests

```bash
docker compose --env-file .env.dev exec backend pytest -q
```

Targeted test groups:

```bash
docker compose --env-file .env.dev exec backend pytest tests/unit -q
docker compose --env-file .env.dev exec backend pytest tests/integration -q
docker compose --env-file .env.dev exec backend pytest tests/e2e -q
```

### Run frontend tests

```bash
cd eta_frontend
npm test
```

### View logs

```bash
docker compose --env-file .env.dev logs -f backend
docker compose --env-file .env.dev logs -f frontend
docker compose --env-file .env.dev logs -f celery_worker
```

### Restart services

```bash
docker compose --env-file .env.dev restart backend
docker compose --env-file .env.dev restart frontend
```

### Stop the stack

```bash
docker compose --env-file .env.dev down
```

### Reset the stack completely

```bash
docker compose --env-file .env.dev down -v
```

## Important project paths

- `eta_backend/` — Django backend
- `eta_backend/accounts/` — user profiles and auth logic
- `eta_backend/expenses/` — expense logic, reports, predictions, insights
- `eta_frontend/src/` — React app source
- `docker-compose.yml` — main stack
- `docker-compose.override.yml` — dev overrides
- `docker-compose.test.yml` — test-only stack
- `.env.dev` — default local env settings
- `nginx/nginx.prod.conf` — production proxy config

## Useful Django shell snippets

```bash
docker compose --env-file .env.dev exec backend python manage.py shell
```

```python
from accounts.models import User
from expenses.models import ExpenseEntry

user = User.objects.first()
expenses = ExpenseEntry.objects.filter(user=user)
print(expenses.count())
```

## Useful frontend checks

```bash
cd eta_frontend
npm run build
```

## Notes

- The current app uses `DJANGO_ADMIN_URL=etaalthech2026`.
- Profile photos are optional and stored under the user media directory.
- Monthly income is stored on each user for budgeting recommendations.
- Payment functionality is not part of the current codebase.


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
