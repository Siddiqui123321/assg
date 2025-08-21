from django.contrib import admin
from .models import Host, Snapshot, Process


@admin.register(Host)
class HostAdmin(admin.ModelAdmin):
    list_display = ("hostname", "api_key")
    search_fields = ("hostname", "api_key")


@admin.register(Snapshot)
class SnapshotAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "host",
        "captured_at",
        "os",
        "processor",
        "cores",
        "threads",
        "ram_gb",
        "used_ram_gb",
        "available_ram_gb",
        "storage_total_gb",
        "storage_used_gb",
        "storage_free_gb",
        "cpu_freq_mhz",
        "process_count",
    )
    list_filter = ("host", "os")
    search_fields = ("host__hostname",)
    date_hierarchy = "captured_at"


@admin.register(Process)
class ProcessAdmin(admin.ModelAdmin):
    list_display = ("snapshot", "pid", "ppid", "name", "cpu_percent", "memory_mb")
    list_filter = ("snapshot",)
    search_fields = ("name", "pid", "ppid")
