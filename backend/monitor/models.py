from django.db import models

class Host(models.Model):
    hostname = models.CharField(max_length=255, unique=True)
    api_key = models.CharField(max_length=128, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.hostname

class Snapshot(models.Model):
    host = models.ForeignKey(Host, on_delete=models.CASCADE, related_name='snapshots')
    captured_at = models.DateTimeField()
    process_count = models.PositiveIntegerField(default=0)

    class Meta:
        indexes = [
            models.Index(fields=['host', '-captured_at']),
        ]

class Process(models.Model):
    snapshot = models.ForeignKey(Snapshot, on_delete=models.CASCADE, related_name='processes')
    pid = models.IntegerField()
    ppid = models.IntegerField()
    name = models.CharField(max_length=255)
    cpu_percent = models.FloatField()
    memory_mb = models.FloatField()
    cmdline = models.TextField(blank=True, default='')

    class Meta:
        indexes = [
            models.Index(fields=['snapshot', 'ppid']),
            models.Index(fields=['snapshot', 'pid']),
        ]