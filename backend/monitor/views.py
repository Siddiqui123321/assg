from django.shortcuts import render, get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from .models import Host, Snapshot, Process
from .serializers import IngestSerializer


@api_view(["POST"])
def ingest(request):
    # Require API key in headers
    api_key = request.headers.get("X-API-KEY")
    if not api_key:
        return Response({"detail": "Missing API key"}, status=status.HTTP_403_FORBIDDEN)

    # Validate incoming payload
    serializer = IngestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    hostname = data["hostname"]

    # Validate host against API key
    host = get_object_or_404(Host, hostname=hostname, api_key=api_key)

    # Extract system info from validated serializer
    sysinfo = data["system_info"]

    # Create Snapshot entry
    snapshot = Snapshot.objects.create(
        host=host,
        captured_at=data["captured_at"],
        os=sysinfo["os"],
        processor=sysinfo.get("processor", ""),
        cores=sysinfo["cores"],
        threads=sysinfo["threads"],
        ram_gb=sysinfo["ram_gb"],
        used_ram_gb=sysinfo["used_ram_gb"],
        available_ram_gb=sysinfo["available_ram_gb"],
        storage_total_gb=sysinfo["storage_total_gb"],
        storage_used_gb=sysinfo["storage_used_gb"],
        storage_free_gb=sysinfo["storage_free_gb"],
        cpu_freq_mhz=sysinfo.get("cpu_freq_mhz"),
    )

    # Bulk insert processes
    processes = [
        Process(
            snapshot=snapshot,
            pid=p["pid"],
            ppid=p["ppid"],
            name=p["name"],
            cpu_percent=p["cpu_percent"],
            memory_mb=p["memory_mb"],
            cmdline=p.get("cmdline", ""),
        )
        for p in data["processes"]
    ]
    Process.objects.bulk_create(processes)

    # Persist process count on the snapshot for quick summaries
    snapshot.process_count = len(processes)
    snapshot.save(update_fields=["process_count"])

    return Response(
        {"snapshot_id": snapshot.id, "processes": snapshot.process_count},
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def hosts(request):
    latest = Snapshot.objects.select_related("host").order_by("host__hostname", "-captured_at")
    seen = set()
    out = []
    for s in latest:
        h = s.host.hostname
        if h in seen:
            continue
        seen.add(h)
        out.append({"hostname": h, "last_seen": s.captured_at})
    return Response(out)


@api_view(["GET"])
@permission_classes([AllowAny])
def latest_snapshot(request):
    hostname = request.query_params.get("hostname")
    if not hostname:
        return Response({"detail": "hostname is required"}, status=400)
    try:
        host = Host.objects.get(hostname=hostname)
    except Host.DoesNotExist:
        return Response({"detail": "unknown host"}, status=404)
    snap = host.snapshots.order_by("-captured_at").first()
    if not snap:
        return Response({"detail": "no snapshots"}, status=404)
    return Response(
        {
            "snapshot_id": snap.id,
            "captured_at": snap.captured_at,
            "process_count": snap.process_count,
            "system": {
                "hostname": snap.host.hostname,
                "os": snap.os,
                "processor": snap.processor,
                "cores": snap.cores,
                "threads": snap.threads,
                "ram_gb": snap.ram_gb,
                "used_ram_gb": snap.used_ram_gb,
                "available_ram_gb": snap.available_ram_gb,
                "storage_total_gb": snap.storage_total_gb,
                "storage_used_gb": snap.storage_used_gb,
                "storage_free_gb": snap.storage_free_gb,
                "cpu_freq_mhz": snap.cpu_freq_mhz,
            },
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def snapshot_processes(request, snapshot_id: int):
    try:
        snap = Snapshot.objects.get(id=snapshot_id)
    except Snapshot.DoesNotExist:
        return Response({"detail": "snapshot not found"}, status=404)
    procs = snap.processes.values(
        "pid", "ppid", "name", "cpu_percent", "memory_mb", "cmdline"
    )
    return Response(list(procs))


from django.views.decorators.clickjacking import xframe_options_exempt

@xframe_options_exempt
def index(request):
    return render(request, "index.html")
