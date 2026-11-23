from django.db import IntegrityError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Application, Job
from .permissions import IsCandidate, IsRecruiterOrReadOnly
from .serializers import (
    ApplicationSerializer,
    ApplicationStatusUpdateSerializer,
    JobSerializer,
)


class JobViewSet(viewsets.ModelViewSet):
    queryset = Job.objects.select_related("recruiter").filter(is_active=True)
    serializer_class = JobSerializer
    permission_classes = [IsRecruiterOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["location", "job_type", "experience_years"]
    search_fields = ["title", "company_name", "skills", "description"]
    ordering_fields = ["created_at", "salary_lpa"]

    def perform_create(self, serializer):
        serializer.save(recruiter=self.request.user)


class ApplyJobView(generics.CreateAPIView):
    serializer_class = ApplicationSerializer
    permission_classes = [IsCandidate]

    def perform_create(self, serializer):
        try:
            serializer.save(candidate=self.request.user)
        except IntegrityError as exc:
            raise ValidationError(
                {"detail": "Aapne is job ke liye pehle se apply kar diya hai."}
            ) from exc


class MyApplicationsListView(generics.ListAPIView):
    serializer_class = ApplicationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Application.objects.select_related("job", "candidate")
        if getattr(user, "role", None) == "RECRUITER":
            return qs.filter(job__recruiter=user)
        return qs.filter(candidate=user)


class UpdateApplicationStatusView(generics.UpdateAPIView):
    serializer_class = ApplicationStatusUpdateSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["put", "patch"]

    def get_queryset(self):
        return Application.objects.select_related("job").filter(job__recruiter=self.request.user)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data, status=status.HTTP_200_OK)