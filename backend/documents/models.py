from django.db import models


class Document(models.Model):
    class Status(models.TextChoices):
        UPLOADED = "UPLOADED", "Uploaded"
        PROCESSING = "PROCESSING", "Processing"
        REVIEW_REQUIRED = "REVIEW_REQUIRED", "Review required"
        APPROVED = "APPROVED", "Approved"
        AUTOMATED = "AUTOMATED", "Automated"
        FAILED = "FAILED", "Failed"

    original_filename = models.CharField(max_length=255)
    file = models.FileField(upload_to="documents/%Y/%m/%d")
    raw_text = models.TextField(blank=True)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.UPLOADED, db_index=True)
    erp_reference = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.original_filename


class ExtractedShipmentData(models.Model):
    document = models.OneToOneField(Document, related_name="extraction", on_delete=models.CASCADE)
    customer = models.CharField(max_length=255, blank=True)
    container_number = models.CharField(max_length=32, blank=True)
    origin = models.CharField(max_length=255, blank=True)
    destination = models.CharField(max_length=255, blank=True)
    weight_kg = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    delivery_date = models.DateField(null=True, blank=True)
    confidence = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    is_valid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ProcessingJob(models.Model):
    class JobType(models.TextChoices):
        EXTRACTION = "EXTRACTION", "Extraction"
        AUTOMATION = "AUTOMATION", "Automation"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        RUNNING = "RUNNING", "Running"
        SUCCESS = "SUCCESS", "Success"
        FAILED = "FAILED", "Failed"

    document = models.ForeignKey(Document, related_name="jobs", on_delete=models.CASCADE)
    job_type = models.CharField(max_length=16, choices=JobType.choices)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING, db_index=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
