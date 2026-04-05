from django.db import models

class ActiveRecordManager(models.Manager):
    """Global DB Query interceptor to hide soft-deleted rows by default."""
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)
