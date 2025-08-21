from django.db import models


class Host(models.Model):
    hostname = models.CharField(max_length=255, unique=True)
    api_key = models.CharField(max_length=255, unique=True)  # one API key per host

    def __str__(self):
        return self.hostname
    
    @property
    def is_authenticated(self):
        return True

class Snapshot(models.Model):
    host = models.ForeignKey(Host, on_delete=models.CASCADE, related_name="snapshots")
    captured_at = models.DateTimeField()

    # --- System Info ---
    os = models.CharField(max_length=255)
    processor = models.CharField(max_length=255, blank=True, null=True)
    cores = models.IntegerField()
    threads = models.IntegerField()
    ram_gb = models.FloatField()
    used_ram_gb = models.FloatField()
    available_ram_gb = models.FloatField()
    storage_total_gb = models.FloatField()
    storage_used_gb = models.FloatField()
    storage_free_gb = models.FloatField()
    cpu_freq_mhz = models.FloatField(blank=True, null=True)

    # --- Meta ---
    process_count = models.IntegerField(default=0)

    def __str__(self):
        return f"Snapshot {self.id} of {self.host.hostname} at {self.captured_at}"


class Process(models.Model):
    snapshot = models.ForeignKey(Snapshot, on_delete=models.CASCADE, related_name="processes")
    pid = models.IntegerField()
    ppid = models.IntegerField()
    name = models.CharField(max_length=255)
    cpu_percent = models.FloatField()
    memory_mb = models.FloatField()
    cmdline = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} (PID {self.pid})"
