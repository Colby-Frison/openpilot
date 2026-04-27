"""
Contracts for safe helper paths in ``system.athena.athenad``.

Avoids websocket/network long-poll threads; focuses on queue/cache and path
validation logic that can run deterministically on desktop.

Maps: R6.
"""

from __future__ import annotations

import json
import queue
import time
from pathlib import Path

from openpilot.system.athena import athenad


def test_strip_zst_extension_behavior():
  assert athenad.strip_zst_extension('a.b.zst') == 'a.b'
  assert athenad.strip_zst_extension('a.b') == 'a.b'


def test_upload_file_and_item_from_dict_roundtrip():
  f = athenad.UploadFile.from_dict({'fn': 'x', 'url': 'u', 'headers': {'k': 'v'}, 'allow_cellular': True})
  assert f.fn == 'x' and f.allow_cellular is True

  i = athenad.UploadItem.from_dict({
    'path': '/tmp/x', 'url': 'u', 'headers': {}, 'created_at': 1, 'id': 'abc',
    'retry_count': 2, 'current': False, 'progress': 0.5, 'allow_cellular': False,
  })
  assert i.id == 'abc' and i.retry_count == 2


def test_upload_queue_cache_filters_cancelled_ids(monkeypatch):
  q = queue.Queue()
  item = athenad.UploadItem(path='/tmp/f', url='u', headers={}, created_at=1, id='keep')
  gone = athenad.UploadItem(path='/tmp/g', url='u', headers={}, created_at=1, id='drop')
  q.put(item)
  q.put(gone)

  class _Params:
    def __init__(self):
      self.saved = None
    def put(self, _k, v):
      self.saved = v

  p = _Params()
  monkeypatch.setattr(athenad, 'Params', lambda: p)
  monkeypatch.setattr(athenad, 'cancelled_uploads', {'drop'})

  athenad.UploadQueueCache.cache(q)
  payload = json.loads(p.saved)
  assert len(payload) == 1
  assert payload[0]['id'] == 'keep'


def test_list_data_directory_respects_prefix(monkeypatch, tmp_path):
  root = tmp_path / 'log'
  (root / 'a').mkdir(parents=True)
  (root / 'a' / '1.txt').write_text('x')
  (root / 'b').mkdir(parents=True)
  (root / 'b' / '2.txt').write_text('x')
  monkeypatch.setattr(athenad.Paths, 'log_root', lambda: str(root))

  out = athenad.listDataDirectory('a/')
  assert out == ['a/1.txt']


def test_upload_files_to_urls_enqueues_existing_file(monkeypatch, tmp_path):
  root = tmp_path / 'log'
  root.mkdir()
  (root / 'f').write_text('x')

  monkeypatch.setattr(athenad.Paths, 'log_root', lambda: str(root))
  monkeypatch.setattr(athenad, 'upload_queue', queue.Queue())
  monkeypatch.setattr(athenad, 'cancelled_uploads', set())
  monkeypatch.setattr(athenad.UploadQueueCache, 'cache', lambda _q: None)

  resp = athenad.uploadFilesToUrls([{'fn': 'f', 'url': 'https://x', 'headers': {}}])
  assert resp['enqueued'] == 1
  assert len(resp['items']) == 1


def test_cancel_upload_success_and_not_found(monkeypatch):
  q = queue.Queue()
  q.put(athenad.UploadItem(path='/tmp/f', url='u', headers={}, created_at=int(time.time()*1000), id='abc'))
  monkeypatch.setattr(athenad, 'upload_queue', q)
  monkeypatch.setattr(athenad, 'cancelled_uploads', set())

  ok = athenad.cancelUpload('abc')
  assert ok['success'] == 1
  missing = athenad.cancelUpload('zzz')
  assert missing['success'] == 0
