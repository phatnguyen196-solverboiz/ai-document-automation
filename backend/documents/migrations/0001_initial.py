from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="Document",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("original_filename", models.CharField(max_length=255)),
                ("file", models.FileField(upload_to="documents/%Y/%m/%d")),
                ("raw_text", models.TextField(blank=True)),
                ("status", models.CharField(choices=[("UPLOADED", "Uploaded"), ("PROCESSING", "Processing"), ("REVIEW_REQUIRED", "Review required"), ("APPROVED", "Approved"), ("AUTOMATED", "Automated"), ("FAILED", "Failed")], db_index=True, default="UPLOADED", max_length=24)),
                ("erp_reference", models.CharField(blank=True, max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="ExtractedShipmentData",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("customer", models.CharField(blank=True, max_length=255)),
                ("container_number", models.CharField(blank=True, max_length=32)),
                ("origin", models.CharField(blank=True, max_length=255)),
                ("destination", models.CharField(blank=True, max_length=255)),
                ("weight_kg", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("delivery_date", models.DateField(blank=True, null=True)),
                ("confidence", models.DecimalField(blank=True, decimal_places=4, max_digits=5, null=True)),
                ("is_valid", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("document", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="extraction", to="documents.document")),
            ],
        ),
        migrations.CreateModel(
            name="ProcessingJob",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("job_type", models.CharField(choices=[("EXTRACTION", "Extraction"), ("AUTOMATION", "Automation")], max_length=16)),
                ("status", models.CharField(choices=[("PENDING", "Pending"), ("RUNNING", "Running"), ("SUCCESS", "Success"), ("FAILED", "Failed")], db_index=True, default="PENDING", max_length=16)),
                ("error_message", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                ("document", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="jobs", to="documents.document")),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
