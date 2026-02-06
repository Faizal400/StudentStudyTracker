from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone
"""
Each Subject can have many Modules & belongs to a user
Each Module can have many sub-modules, but only one (parent) subject
Each Sub-Module belongs to only one Module
"""

class Subject(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Module(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="modules")
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.subject.name}\\{self.name}"

class SubModule(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="submodules")
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.module.subject.name}\\{self.module.name}\\{self.name}"

class StudySession(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="study_sessions"
    )

    # Keep history even if user deletes a subject later
    subject = models.ForeignKey(
        "Subject",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sessions"
    )

    # Optional for later (safe to include now)
    module = models.ForeignKey(
        "Module",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sessions"
    )

    submodule = models.ForeignKey(
        "SubModule",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sessions"
    )

    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True, blank=True)

    # This is the MVP field you’ll use first
    duration_seconds = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["subject", "created_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(ended_at__isnull=True) | models.Q(ended_at__gte=models.F("started_at")),
                name="ended_at_gte_started_at_or_null",
            )
        ]

    @property
    def duration_minutes(self) -> int:
        return self.duration_seconds // 60  # whole minutes

    def __str__(self) -> str:
        subj = self.subject.name if self.subject else "No subject"
        return f"{subj} ({self.duration_minutes} mins)"
