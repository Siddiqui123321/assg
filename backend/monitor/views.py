from django.shortcuts import render
from django.db import transaction
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from .models import Host, Snapshot, Process
from .serializers import IngestSerializer

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ingest(request):
    s = IngestSerializer(data=request.data)
    s.is_valid(raise_exception=True)
    data = s.validated_data

    host = request.user
    if host.hostname != data['hostname']:
        return Response({'detail': 'Hostname does not match API key'}, status=400)

    with transaction.atomic():
        snap = Snapshot.objects.create(
            host=host,
            captured_at=data['captured_at'],
            process_count=len(data['processes']),
        )
        Process.objects.bulk_create([
            Process(
                snapshot=snap,
                pid=p['pid'],
                ppid=p['ppid'],
                name=p['name'][:255],
                cpu_percent=p['cpu_percent'],
                memory_mb=p['memory_mb'],
                cmdline=p.get('cmdline', '')[:8192]
            ) for p in data['processes']
        ], batch_size=1000)

    return Response({'snapshot_id': snap.id, 'stored': True, 'count': snap.process_count})

@api_view(['GET'])
@permission_classes([AllowAny])
def hosts(request):
    latest = Snapshot.objects.select_related('host').order_by('host__hostname', '-captured_at')
    seen = set()
    out = []
    for s in latest:
        h = s.host.hostname
        if h in seen:
            continue
        seen.add(h)
        out.append({'hostname': h, 'last_seen': s.captured_at})
    return Response(out)

@api_view(['GET'])
@permission_classes([AllowAny])
def latest_snapshot(request):
    hostname = request.query_params.get('hostname')
    if not hostname:
        return Response({'detail': 'hostname is required'}, status=400)
    try:
        host = Host.objects.get(hostname=hostname)
    except Host.DoesNotExist:
        return Response({'detail': 'unknown host'}, status=404)
    snap = host.snapshots.order_by('-captured_at').first()
    if not snap:
        return Response({'detail': 'no snapshots'}, status=404)
    return Response({'snapshot_id': snap.id, 'captured_at': snap.captured_at, 'process_count': snap.process_count})

@api_view(['GET'])
@permission_classes([AllowAny])
def snapshot_processes(request, snapshot_id: int):
    try:
        snap = Snapshot.objects.get(id=snapshot_id)
    except Snapshot.DoesNotExist:
        return Response({'detail': 'snapshot not found'}, status=404)
    procs = snap.processes.values('pid','ppid','name','cpu_percent','memory_mb','cmdline')
    return Response(list(procs))

from django.views.decorators.clickjacking import xframe_options_exempt

@xframe_options_exempt
def index(request):
    return render(request, 'index.html')