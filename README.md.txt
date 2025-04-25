# 💸 Full-Stack Expense Tracker

A full-featured personal and business expense tracker built with Django, Django REST Framework, PostgreSQL, and React (Vite). The app supports user authentication, custom roles (admin/user), reporting, graphs, currency conversion, 2FA, and much more.

---

## 📦 Tech Stack

### Backend:
- Python
- Django
- Django REST Framework
- PostgreSQL
- Celery + Redis
- Django-AllAuth (2FA)
- Django-Environ
- Docker + Nginx
- Gunicorn

### Frontend:
- React (Vite)
- Bootstrap
- Material UI
- Font Awesome
- Axios
- Light/Dark Theme (Silver, Orange, Green)

---

## 🚀 Features

- ✅ Custom User Model with Roles (Admin/User)
- ✅ Expense Entries per Section & Subsection
- ✅ Date Selection & History Editing
- ✅ Light/Dark Mode Toggle
- ✅ Dynamic Theme (Silver, Orange & Green)
- ✅ Multi-Currency Support (Default: EUR)
- ✅ Historical Currency Tracking
- ✅ Currency Conversion via [Fixer.io](https://fixer.io)
- ✅ Graphical Dashboard Reports (Top/Bottom spend)
- ✅ Daily, Weekly, Monthly, Quarterly, Annual Totals
- ✅ Export Reports to CSV / PDF
- ✅ Celery for background tasks
- ✅ Responsive for Mobile (PWA ready)
- ✅ Dockerized Setup
- ✅ CI/CD with GitHub Actions
- ✅ Deployed on Heroku

---

## 🛠️ Local Development Setup

### Backend (Django)

```bash
# Create and activate virtual environment
python -m venv .env
.env\Scripts\activate    # On Windows

# Install dependencies
pip install -r requirements.txt

# Setup PostgreSQL and .env file
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
