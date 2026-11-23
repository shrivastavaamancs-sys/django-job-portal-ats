from rest_framework import serializers
from .models import Job, Application

class JobSerializer(serializers.ModelSerializer):
    recruiter_email = serializers.ReadOnlyField(source="recruiter.email")
    applicants_count = serializers.IntegerField(source="applications.count", read_only=True)

    class Meta:
        model = Job
        fields = [
            "id", "recruiter_email", "title", "company_name", "location",
            "job_type", "experience_years", "salary_lpa", "description",
            "is_active", "applicants_count", "created_at"
        ]


class ApplicationSerializer(serializers.ModelSerializer):
    candidate_email = serializers.ReadOnlyField(source="candidate.email")
    job_title = serializers.ReadOnlyField(source="job.title")

    class Meta:
        model = Application
        fields = [
            "id", "job", "job_title", "candidate_email",
            "resume", "cover_note", "status", "applied_at"
        ]
        read_only_fields = ["status", "applied_at"]

    def validate(self, attrs):
        user = self.context["request"].user
        job = attrs.get("job")
        if not job.is_active:
            raise serializers.ValidationError("Yeh job ab active nahi hai.")
        if Application.objects.filter(job=job, candidate=user).exists():
            raise serializers.ValidationError("Aap is job ke liye pehle hi apply kar chuke hain.")
        return attrs


class ApplicationStatusUpdateSerializer(serializers.ModelSerializer):
    ALLOWED_TRANSITIONS = {
        "APPLIED": ["SHORTLISTED", "REJECTED"],
        "SHORTLISTED": ["INTERVIEW", "REJECTED"],
        "INTERVIEW": ["SELECTED", "REJECTED"],
        "SELECTED": [],
        "REJECTED": [],
    }

    class Meta:
        model = Application
        fields = ["status"]

    def validate_status(self, new_status):
        current_status = self.instance.status
        if new_status not in self.ALLOWED_TRANSITIONS.get(current_status, []):
            raise serializers.ValidationError(
                f"Status ko '{current_status}' se seedha '{new_status}' mein nahi badal sakte."
            )
        return new_status