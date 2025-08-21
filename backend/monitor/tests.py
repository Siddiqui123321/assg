from django.test import TestCase
from rest_framework.test import APIClient
from .models import Host, Snapshot, Process
from datetime import datetime, timezone

class IngestTests(TestCase):
    def setUp(self):
        self.host = Host.objects.create(hostname='DESKTOP-TEST', api_key='TESTKEY123')
        self.client = APIClient()
        self.client.credentials(HTTP_X_API_KEY='TESTKEY123')

    def test_ingest_and_retrieve(self):
        payload = {
            'hostname': 'DESKTOP-TEST',
            'captured_at': datetime.now(timezone.utc).isoformat(),
            'processes': [
                {'pid': 1, 'ppid': 0, 'name': 'System', 'cpu_percent': 0.0, 'memory_mb': 5.2, 'cmdline': ''},
                {'pid': 2, 'ppid': 1, 'name': 'Child', 'cpu_percent': 1.0, 'memory_mb': 10.0, 'cmdline': ''},
            ]
        }
        res = self.client.post('/api/v1/ingest', payload, format='json')
        self.assertEqual(res.status_code, 200)
        sid = res.data['snapshot_id']
        self.assertTrue(Snapshot.objects.filter(id=sid).exists())
        self.assertEqual(Process.objects.filter(snapshot_id=sid).count(), 2)

        res2 = self.client.get('/api/v1/snapshots/latest?hostname=DESKTOP-TEST')
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.data['snapshot_id'], sid)

        res3 = self.client.get(f'/api/v1/snapshots/{sid}/processes')
        self.assertEqual(res3.status_code, 200)
        self.assertEqual(len(res3.data), 2)

    def test_auth_required(self):
        c = APIClient()
        res = c.post('/api/v1/ingest', {}, format='json')
        self.assertEqual(res.status_code, 403)