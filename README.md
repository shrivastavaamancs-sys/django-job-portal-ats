# Job Portal ATS (Django & DRF)

A full-stack recruitment and candidate screening web application built with **Django**, **Django REST Framework**, and **PostgreSQL**. It provides web CRUD workflows for job descriptions and candidates, resume text extraction and skill/experience matching, JWT-secured REST APIs with Swagger documentation, and invite-token access control.

## Key Features

- **Job Description & Candidate CRUD:** Create, edit, delete, and list job descriptions (`/jd/`) and candidate profiles (`/upload-resume/`, `/candidate/<id>/edit/`, `/candidate/<id>/delete/`).
- **Resume Parsing & Skill Ranking:** Extracts text from `.pdf` and `.docx` resumes and scores/ranks candidates against required skills and minimum experience (`/result-filter/`).
- **Invite Token Access Control:** Protects web workflows via `AccessToken` (`role`, `can_edit`, `is_active`) and `InviteTokenMiddleware`, supporting view-only (`GET`) vs. edit access and instant token revocation.
- **REST API & OpenAPI Docs:** JWT authentication (`SimpleJWT`), filtering, search, pagination, schema generation (`drf-spectacular`), and interactive Swagger UI at `/api/docs/`.

## Tech Stack

- **Backend:** Python, Django, Django REST Framework, SimpleJWT, `drf-spectacular`, `django-filter`
- **Database:** PostgreSQL
- **Document Parsing:** `pypdf`, `python-docx`
- **Frontend:** Django Templates, HTML, CSS

## Project Structure

```text
job_portal/
├── accounts/           # Custom user model & registration view
├── config/             # Project settings, root URLs, WSGI/ASGI
├── jobs/               # Models, dashboard/CRUD views, middleware, matcher, DRF views
│   └── templates/jobs/ # HTML templates
├── manage.py
└── requirements.txt
```

## Local Setup

### 1. Clone the Repository & Create Virtual Environment

```bash
git clone [https://github.com/shrivastavaamancs-sys/django-job-portal-ats.git](https://github.com/shrivastavaamancs-sys/django-job-portal-ats.git)
cd django-job-portal-ats
python -m venv venv
```

Activate the virtual environment (Windows PowerShell):

```powershell
.\venv\Scripts\Activate.ps1
```

### 2. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 3. Configure Environment Variables (`.env`)

Create a `.env` file in the project root (do not commit `.env` to Git):

```env
SECRET_KEY=replace-with-a-strong-secret-key
DEBUG=True
DB_NAME=job_portal_db
DB_USER=postgres
DB_PASSWORD=your_postgres_password
DB_HOST=127.0.0.1
DB_PORT=5433
```

Make sure PostgreSQL is running and the database (`job_portal_db`) exists before running migrations.

### 4. Run Migrations & Create Superuser

```powershell
python manage.py check
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### 5. Start the Development Server

```powershell
python manage.py runserver
```

Open `http://127.0.0.1:8000/` in your browser.

## Key Endpoints

- **Web Workflows:** `/jd/`, `/upload-resume/`, `/result-filter/`
- **Django Admin:** `/admin/`
- **JWT Auth:** `/api/auth/register/`, `/api/auth/login/`, `/api/auth/refresh/`
- **API & Swagger Docs:** `/api/`, `/api/schema/`, `/api/docs/`
