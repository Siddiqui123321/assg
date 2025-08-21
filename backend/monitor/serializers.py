from rest_framework import serializers


class ProcessIngestSerializer(serializers.Serializer):
    pid = serializers.IntegerField()
    ppid = serializers.IntegerField()
    name = serializers.CharField(max_length=255, allow_blank=False)
    cpu_percent = serializers.FloatField()
    memory_mb = serializers.FloatField()
    cmdline = serializers.CharField(allow_blank=True, required=False, max_length=8192)


class SystemInfoSerializer(serializers.Serializer):
    os = serializers.CharField(max_length=255)
    processor = serializers.CharField(max_length=255, allow_blank=True, required=False)
    cores = serializers.IntegerField()
    threads = serializers.IntegerField()
    ram_gb = serializers.FloatField()
    used_ram_gb = serializers.FloatField()
    available_ram_gb = serializers.FloatField()
    storage_total_gb = serializers.FloatField()
    storage_used_gb = serializers.FloatField()
    storage_free_gb = serializers.FloatField()
    cpu_freq_mhz = serializers.FloatField(required=False, allow_null=True)


class IngestSerializer(serializers.Serializer):
    hostname = serializers.CharField(max_length=255)
    captured_at = serializers.DateTimeField()
    system_info = SystemInfoSerializer()
    processes = ProcessIngestSerializer(many=True)
