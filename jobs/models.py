import os
import secrets
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


def validate_resume_file(value):
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in [".pdf", ".doc", ".docx"]:
        raise ValidationError("Sirf PDF, DOC, ya DOCX files allowed hain.")
    if value.size > 2 * 1024 * 1024:  # 2 MB limit
        raise ValidationError("Resume file size 2MB se kam hona chahiye.")


class Job(models.Model):
    class JobType(models.TextChoices):
        FULL_TIME = "FULL_TIME", "Full Time"
        INTERNSHIP = "INTERNSHIP", "Internship"
        REMOTE = "REMOTE", "Remote"

    recruiter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="posted_jobs",
    )
    title = models.CharField(max_length=200)
    company_name = models.CharField(max_length=150)
    location = models.CharField(max_length=100)
    job_type = models.CharField(
        max_length=20,
        choices=JobType.choices,
        default=JobType.FULL_TIME,
    )
    experience_years = models.PositiveIntegerField(default=0)
    salary_lpa = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    skills = models.TextField(
        blank=True,
        help_text="Comma-separated skills define karein, e.g. Java, Spring Boot, SQL, Docker",
    )
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} - {self.company_name}"


class Application(models.Model):
    class Status(models.TextChoices):
        APPLIED = "APPLIED", "Applied"
        SHORTLISTED = "SHORTLISTED", "Shortlisted"
        INTERVIEW = "INTERVIEW", "Interview"
        SELECTED = "SELECTED", "Selected"
        REJECTED = "REJECTED", "Rejected"

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="applications")
    candidate = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="applications",
    )
    resume = models.FileField(upload_to="resumes/", validators=[validate_resume_file])
    cover_note = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.APPLIED,
    )
    applied_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["job", "candidate"],
                name="unique_job_application",
            )
        ]
        ordering = ["-applied_at"]

    def __str__(self):
        return f"{self.candidate.email} -> {self.job.title} ({self.status})"


class CandidateProfile(models.Model):
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    qualification = models.CharField(max_length=200)
    experience_years = models.DecimalField(max_digits=4, decimal_places=1, default=0.0)
    skills = models.TextField(help_text="Comma-separated skills, e.g. Python, Django, SQL, Docker")
    resume = models.FileField(
        upload_to="resumes/",
        validators=[validate_resume_file],
        blank=True,
        null=True,
    )
    resume_filename = models.CharField(max_length=255, blank=True)
    resume_file_type = models.CharField(max_length=10, blank=True)
    resume_text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if self.resume:
            self.resume_filename = os.path.basename(self.resume.name)
            self.resume_file_type = os.path.splitext(self.resume_filename)[1].lower().lstrip(".")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} ({self.email})"


class JobDescription(models.Model):
    title = models.CharField(max_length=200)
    company_name = models.CharField(max_length=150, blank=True)
    min_experience = models.DecimalField(max_digits=4, decimal_places=1, default=0.0)
    required_skills = models.TextField(blank=True, help_text="e.g. Python, Django, SQL, Docker")
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.company_name})" if self.company_name else self.title


class AccessToken(models.Model):
    class Role(models.TextChoices):
        HR = "HR", "HR"
        MANAGER = "MANAGER", "Manager"
        CEO = "CEO", "CEO"

    label = models.CharField(max_length=100, help_text="Person ka naam, e.g. Rahul - HR")
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.HR,
    )
    token = models.CharField(max_length=64, unique=True, default=secrets.token_urlsafe)
    can_edit = models.BooleanField(default=False, help_text="Unchecked = sirf view/filter access")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.label} - {self.role} ({'Active' if self.is_active else 'Revoked'})"