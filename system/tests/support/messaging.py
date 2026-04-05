"""Messaging helpers for system-level pub/sub tests."""

from __future__ import annotations

from typing import Any

import cereal.messaging as messaging


def make_pub_sub(pub_services: list[str], sub_services: list[str], **sub_kw: Any):
  """
  Build a ``PubMaster`` / ``SubMaster`` pair (``SubMaster`` must not be empty).

  ``**sub_kw`` is forwarded to ``SubMaster`` (e.g. ``poll=``, ``ignore_alive=``).
  """
  return messaging.PubMaster(pub_services), messaging.SubMaster(sub_services, **sub_kw)
