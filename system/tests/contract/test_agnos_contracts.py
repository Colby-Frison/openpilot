"""
Desktop-safe contracts for helper functions in ``system.hardware.tici.agnos``.

No flashing/network actions; tests only deterministic path/hash orchestration.

Maps: R8.
"""

from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

from openpilot.system.hardware.tici import agnos


def test_slot_suffix_and_partition_path_helpers():
  assert agnos.slot_number_to_suffix(0) == '_a'
  assert agnos.slot_number_to_suffix(1) == '_b'
  with pytest.raises(AssertionError):
    agnos.slot_number_to_suffix(2)

  p = {'name': 'boot'}
  assert agnos.get_partition_path(0, p).endswith('boot_a')
  assert agnos.get_partition_path(1, {'name': 'persist', 'has_ab': False}).endswith('persist')


def test_verify_partition_type_guards():
  assert agnos.verify_partition(0, {'name': 'x', 'full_check': False, 'size': 'bad', 'hash_raw': 'h'}) is False
  assert agnos.verify_partition(0, {'name': 'x', 'full_check': False, 'size': 4, 'hash_raw': 123}) is False


def test_verify_partition_full_check_uses_raw_hash(monkeypatch):
  monkeypatch.setattr(agnos, 'get_partition_path', lambda *_a, **_k: '/tmp/p')
  monkeypatch.setattr(agnos, 'get_raw_hash', lambda _p, _s: 'abcd')
  part = {'name': 'x', 'full_check': True, 'size': 4, 'hash_raw': 'ABCD'}
  assert agnos.verify_partition(0, part) is True


def test_verify_partition_non_full_reads_hash_tail(monkeypatch, tmp_path):
  img = tmp_path / 'img'
  raw = b'ABCD'
  digest = 'f' * 64
  img.write_bytes(raw + digest.encode())
  monkeypatch.setattr(agnos, 'get_partition_path', lambda *_a, **_k: str(img))
  part = {'name': 'x', 'full_check': False, 'size': len(raw), 'hash_raw': digest}
  assert agnos.verify_partition(0, part) is True


def test_clear_partition_hash_writes_zero_tail(monkeypatch, tmp_path):
  img = tmp_path / 'img'
  img.write_bytes(b'ABCD' + b'x' * 64)
  monkeypatch.setattr(agnos, 'get_partition_path', lambda *_a, **_k: str(img))
  monkeypatch.setattr(agnos.os, 'sync', lambda: None)
  agnos.clear_partition_hash(0, {'name': 'x', 'size': 4})
  assert img.read_bytes()[4:68] == b'\x00' * 64


def test_flash_partition_non_full_writes_hash_footer(monkeypatch, tmp_path):
  img = tmp_path / 'img'
  img.write_bytes(b'')
  monkeypatch.setattr(agnos, 'get_partition_path', lambda *_a, **_k: str(img))
  monkeypatch.setattr(agnos, 'verify_partition', lambda *_a, **_k: False)
  calls = {'clear': 0, 'comp': 0}
  monkeypatch.setattr(agnos, 'clear_partition_hash', lambda *_a, **_k: calls.__setitem__('clear', calls['clear'] + 1))
  monkeypatch.setattr(agnos, 'extract_compressed_image', lambda *_a, **_k: calls.__setitem__('comp', calls['comp'] + 1))

  part = {'name': 'x', 'size': 4, 'full_check': False, 'hash_raw': 'a' * 64}
  agnos.flash_partition(0, part, cloudlog=type('C', (), {'info': lambda *a, **k: None})(), standalone=True)

  assert calls['clear'] == 1 and calls['comp'] == 1
  data = img.read_bytes()
  assert data[4:] == ('a' * 64).encode()


def test_verify_agnos_update_aggregates_all(monkeypatch):
  seen = []
  monkeypatch.setattr(agnos, 'verify_partition', lambda slot, part: seen.append(part['name']) or True)
  monkeypatch.setattr(agnos, 'open', lambda *_a, **_k: io.StringIO('[]'), raising=False)
  monkeypatch.setattr(agnos.json, 'load', lambda _f: [{'name': 'a'}, {'name': 'b'}])
  assert agnos.verify_agnos_update('dummy.json', 0) is True
  assert seen == ['a', 'b']
