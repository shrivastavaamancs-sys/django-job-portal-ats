from django.contrib import admin
from .models import Job, Application, CandidateProfile, JobDescription
from .models import Job, Application, CandidateProfile, JobDescription, AccessToken



@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "company_name",
        "location",
        "job_type",
        "experience_years",
        "is_active",
        "created_at",
    )
    list_filter = ("job_type", "is_active")
    search_fields = ("title", "company_name", "location")


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("id", "job", "candidate", "status", "applied_at")
    list_filter = ("status",)
    search_fields = ("job__title", "candidate__email")


@admin.register(CandidateProfile)
class CandidateProfileAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "full_name",
        "email",
        "phone",
        "qualification",
        "experience_years",
        "created_at",
    )
    search_fields = ("full_name", "email", "qualification", "skills")


@admin.register(JobDescription)
class JobDescriptionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "company_name",
        "min_experience",
        "created_at",
    )
    search_fields = ("title", "company_name", "required_skills")
    
    
    from .models import AccessToken
    
    
@admin.register(AccessToken)
class AccessTokenAdmin(admin.ModelAdmin):
  list_display = ("id", "label", "role", "token", "can_edit", "is_active", "created_at")
  list_filter = ("role", "is_active", "can_edit")
  search_fields = ("label", "role", "token")