import uuid

from django.conf import settings
from django.db import models

from apps.common.models import TimestampedModel, UUIDModel
from apps.tenancy.models import Organization


def generate_visitor_qr_code() -> str:
    return str(uuid.uuid4())


class PersonType(models.TextChoices):
    STUDENT = "student", "Student"
    INTERN = "internship", "Internship"
    JUNIOR = "junior", "Junior"
    SENIOR = "senior", "Senior"
    TEACHER = "teacher", "Teacher"
    MANAGER = "manager", "Manager"
    CEO = "ceo", "CEO"
    STAFF = "staff", "Staff"
    VISITOR = "visitor", "Visitor"
    # Kept for older records / security workflows
    EMPLOYEE = "employee", "Employee"
    VIP = "vip", "VIP"
    CONTRACTOR = "contractor", "Contractor"
    BLACKLIST = "blacklist", "Blacklist"
    UNKNOWN = "unknown", "Unknown"


class Person(UUIDModel, TimestampedModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="persons")
    external_id = models.CharField(max_length=64, blank=True, default="")
    full_name = models.CharField(max_length=255)
    person_type = models.CharField(max_length=20, choices=PersonType.choices, default=PersonType.STUDENT)
    email = models.EmailField(blank=True, default="")
    phone = models.CharField(max_length=32, blank=True, default="")
    department = models.CharField(max_length=128, blank=True, default="")
    shift_start = models.TimeField(null=True, blank=True, help_text="Expected clock-in time")
    shift_end = models.TimeField(null=True, blank=True, help_text="Expected clock-out time")
    is_active = models.BooleanField(default=True)
    # When True, cameras watch this person for mobile-use activity only.
    watch_mobile_activity = models.BooleanField(
        default=False,
        help_text="Strict watch: log mobile use for this person on cameras",
    )
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["full_name"]
        indexes = [models.Index(fields=["organization", "person_type", "is_active"])]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "external_id"],
                condition=~models.Q(external_id=""),
                name="identity_person_org_external_id_uniq",
            )
        ]

    def save(self, *args, **kwargs):
        if not self.external_id:
            self.external_id = f"p-{uuid.uuid4().hex[:12]}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} ({self.person_type})"


class BiometricConsent(UUIDModel, TimestampedModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="consents")
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="consents")
    consent_type = models.CharField(max_length=32, default="enrollment")
    granted_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)
    evidence_url = models.TextField(blank=True, default="")
    notes = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-granted_at"]

    @property
    def is_valid(self):
        return self.revoked_at is None


class FaceImage(UUIDModel, TimestampedModel):
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="face_images")
    image = models.ImageField(upload_to="faces/%Y/%m/", blank=True)
    image_path = models.CharField(max_length=512, blank=True, default="")
    quality_score = models.FloatField(default=0.0)
    blur_score = models.FloatField(default=0.0)
    is_primary = models.BooleanField(default=False)
    source = models.CharField(max_length=32, default="upload")  # upload | enrollment | unknown
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]


class FaceEmbedding(UUIDModel, TimestampedModel):
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="embeddings")
    face_image = models.ForeignKey(FaceImage, on_delete=models.SET_NULL, null=True, blank=True, related_name="embeddings")
    consent = models.ForeignKey(BiometricConsent, on_delete=models.SET_NULL, null=True, blank=True)
    model_name = models.CharField(max_length=128, default="insightface-sim")
    model_version = models.CharField(max_length=64, default="0.1.0")
    # Stored as JSON list of floats for portability (pgvector later)
    vector = models.JSONField(default=list)
    quality_score = models.FloatField(default=0.0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["person", "is_active"])]


class AttendanceDirection(models.TextChoices):
    IN = "in", "Clock In"
    OUT = "out", "Clock Out"


class AttendanceRecord(UUIDModel, TimestampedModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="attendance_records")
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="attendance_records")
    site = models.ForeignKey("sites.Site", on_delete=models.SET_NULL, null=True, blank=True)
    camera = models.ForeignKey("cameras.Camera", on_delete=models.SET_NULL, null=True, blank=True)
    event = models.ForeignKey("events.DetectionEvent", on_delete=models.SET_NULL, null=True, blank=True)
    direction = models.CharField(max_length=10, choices=AttendanceDirection.choices)
    recorded_at = models.DateTimeField()
    confidence = models.FloatField(default=0.0)
    is_late = models.BooleanField(default=False)
    is_overtime = models.BooleanField(default=False)
    notes = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        ordering = ["-recorded_at"]
        indexes = [models.Index(fields=["organization", "person", "-recorded_at"])]


class VisitorStatus(models.TextChoices):
    REQUESTED = "requested", "Requested"
    APPROVED = "approved", "Approved"
    DENIED = "denied", "Denied"
    CHECKED_IN = "checked_in", "Checked In"
    CHECKED_OUT = "checked_out", "Checked Out"
    CANCELLED = "cancelled", "Cancelled"
    EXPIRED = "expired", "Expired"


class VisitorRegistration(UUIDModel, TimestampedModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="visitors")
    site = models.ForeignKey("sites.Site", on_delete=models.CASCADE, related_name="visitors")
    person = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, blank=True, related_name="visitor_registrations")
    full_name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, default="")
    phone = models.CharField(max_length=32, blank=True, default="")
    host_name = models.CharField(max_length=255)
    host_email = models.EmailField(blank=True, default="")
    purpose = models.TextField(blank=True, default="")
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    status = models.CharField(max_length=20, choices=VisitorStatus.choices, default=VisitorStatus.REQUESTED)
    qr_code = models.CharField(max_length=64, unique=True, default=generate_visitor_qr_code)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="approved_visitors"
    )
    checked_in_at = models.DateTimeField(null=True, blank=True)
    checked_out_at = models.DateTimeField(null=True, blank=True)
    match_confidence = models.FloatField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]


class UnknownSighting(UUIDModel, TimestampedModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="unknown_sightings")
    camera = models.ForeignKey("cameras.Camera", on_delete=models.SET_NULL, null=True, blank=True)
    event = models.ForeignKey("events.DetectionEvent", on_delete=models.SET_NULL, null=True, blank=True)
    snapshot_path = models.CharField(max_length=512, blank=True, default="")
    embedding_vector = models.JSONField(default=list, blank=True)
    confidence = models.FloatField(default=0.0)
    track_id = models.IntegerField(null=True, blank=True)
    gallery_person = models.ForeignKey(
        Person, on_delete=models.SET_NULL, null=True, blank=True, related_name="unknown_sightings"
    )
    reviewed = models.BooleanField(default=False)
    notes = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["organization", "-created_at"])]


class PersonSighting(UUIDModel, TimestampedModel):
    """Camera recognition log for an enrolled person (with snapshot)."""

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="person_sightings")
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="sightings")
    camera = models.ForeignKey("cameras.Camera", on_delete=models.SET_NULL, null=True, blank=True)
    event = models.ForeignKey("events.DetectionEvent", on_delete=models.SET_NULL, null=True, blank=True)
    snapshot_path = models.CharField(max_length=512, blank=True, default="")
    confidence = models.FloatField(default=0.0)
    match_score = models.FloatField(default=0.0)
    notes = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["organization", "person", "-created_at"]),
            models.Index(fields=["person", "-created_at"]),
        ]

