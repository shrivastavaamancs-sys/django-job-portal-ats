Job Portal ATS (Django & DRF) ek full-stack recruitment and candidate screening web application hai jisme CRUD workflows, resume text extraction + keyword/skill matching, JWT-backed REST APIs, aur invite token-based access control shamil hain.

Key Features
JD & Candidate Management: Job descriptions aur candidate profiles create, edit, delete, aur list karne ke liye web workflows (/jd/, /upload-resume/, /candidate/<id>/edit/, /candidate/<id>/delete/).

Resume Parsing & Skill Filtering: Uploaded .pdf aur .docx resumes se text extract karke required skills aur minimum experience ke basis par candidates score aur rank karne ka filter (/result-filter/).

Role-Based Invite Token Middleware: AccessToken (HR, Manager, CEO, can_edit, is_active) ke zariye protected routes par view-only ya edit access control aur token revocation.

REST API & Swagger Docs: Django REST Framework + SimpleJWT authentication, filtering/search/pagination, aur /api/docs/ par interactive API documentation.

Tech Stack
Backend: Python, Django, Django REST Framework (DRF), SimpleJWT, drf-spectacular

Database & Parsing: PostgreSQL, pypdf, python-docx

Frontend: Django Templates, HTML/CSS
