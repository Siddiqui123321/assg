from rest_framework import serializers

class ProcessIngestSerializer(serializers.Serializer):
    pid = serializers.IntegerField()
    ppid = serializers.IntegerField()
    name = serializers.CharField(max_length=255)
    cpu_percent = serializers.FloatField()
    memory_mb = serializers.FloatField()
    cmdline = serializers.CharField(allow_blank=True, required=False, max_length=8192)

class IngestSerializer(serializers.Serializer):
    hostname = serializers.CharField(max_length=255)
    captured_at = serializers.DateTimeField()
    processes = ProcessIngestSerializer(many=True)