from django.test import TestCase
from rest_framework.test import APIClient
from .models import Host, Snapshot, Process
from datetime import datetime, timezone


class MonitorApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def _base_payload(self, hostname='DESKTOP-TEST'):
        return {
            'hostname': hostname,
            'captured_at': datetime.now(timezone.utc).isoformat(),
            'system_info': {
                'os': 'Windows',
                'processor': 'x86_64',
                'cores': 4,
                'threads': 8,
                'ram_gb': 16.0,
                'used_ram_gb': 6.0,
                'available_ram_gb': 10.0,
                'storage_total_gb': 256.0,
                'storage_used_gb': 120.0,
                'storage_free_gb': 136.0,
                'cpu_freq_mhz': 2400.0,
            },
            'processes': [
                {'pid': 1, 'ppid': 0, 'name': 'System', 'cpu_percent': 0.0, 'memory_mb': 5.2, 'cmdline': ''},
                {'pid': 2, 'ppid': 1, 'name': 'Child', 'cpu_percent': 1.0, 'memory_mb': 10.0, 'cmdline': ''},
            ],
        }

    def test_ingest_auto_creates_host_and_stores_snapshot(self):
        # No host exists yet; provide API key header → auto-create host
        self.client.credentials(HTTP_X_API_KEY='TESTKEY123')
        payload = self._base_payload('AUTO-HOST')
        res = self.client.post('/api/v1/ingest', payload, format='json')
        self.assertEqual(res.status_code, 201)
        sid = res.data['snapshot_id']

        # Host should be created and linked
        h = Host.objects.get(hostname='AUTO-HOST')
        self.assertEqual(h.api_key, 'TESTKEY123')
        self.assertTrue(Snapshot.objects.filter(id=sid, host=h).exists())
        self.assertEqual(Process.objects.filter(snapshot_id=sid).count(), 2)

    def test_ingest_requires_api_key(self):
        res = self.client.post('/api/v1/ingest', {}, format='json')
        self.assertEqual(res.status_code, 403)

    def test_ingest_rejects_wrong_key_for_existing_host(self):
        Host.objects.create(hostname='LOCKED', api_key='GOODKEY')
        self.client.credentials(HTTP_X_API_KEY='BADKEY')
        payload = self._base_payload('LOCKED')
        res = self.client.post('/api/v1/ingest', payload, format='json')
        self.assertEqual(res.status_code, 403)

    def test_latest_and_processes_and_hosts_endpoints(self):
        # Seed one snapshot
        self.client.credentials(HTTP_X_API_KEY='K1')
        payload = self._base_payload('H1')
        res = self.client.post('/api/v1/ingest', payload, format='json')
        self.assertEqual(res.status_code, 201)
        sid = res.data['snapshot_id']

        # latest snapshot contains system and process_count
        res2 = self.client.get('/api/v1/snapshots/latest', {'hostname': 'H1'})
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.data['snapshot_id'], sid)
        self.assertIn('system', res2.data)
        self.assertEqual(res2.data['process_count'], 2)
        self.assertEqual(res2.data['system']['hostname'], 'H1')

        # processes list matches count
        res3 = self.client.get(f'/api/v1/snapshots/{sid}/processes')
        self.assertEqual(res3.status_code, 200)
        self.assertEqual(len(res3.data), 2)

        # hosts lists H1 at least once
        res4 = self.client.get('/api/v1/hosts')
        self.assertEqual(res4.status_code, 200)
        hostnames = [h['hostname'] for h in res4.data]
        self.assertIn('H1', hostnames)