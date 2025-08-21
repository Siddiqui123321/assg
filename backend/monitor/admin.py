from django.contrib import admin
from .models import Host, Snapshot, Process

@admin.register(Host)
class HostAdmin(admin.ModelAdmin):
    list_display = ('hostname','api_key','created_at')

@admin.register(Snapshot)
class SnapshotAdmin(admin.ModelAdmin):
    list_display = ('id','host','captured_at','process_count')
    list_filter = ('host',)

@admin.register(Process)
class ProcessAdmin(admin.ModelAdmin):
    list_display = ('snapshot','pid','ppid','name','cpu_percent','memory_mb')
    list_filter = ('snapshot',)