"""Beads CLI backend stub — full implementation added in T05/T06.

This module satisfies the deferred-import registration wired in T01 via
``backlog_core.backend_protocol.create_backend``.  The :class:`BeadsBackend`
class will route backlog operations to the ``bd`` CLI subprocess once T05/T06
lands.

Instantiating :class:`BeadsBackend` before T05/T06 lands will raise
:exc:`NotImplementedError` on every method call.
"""

from __future__ import annotations


class BeadsBackend:
    """Routes backlog operations to the ``bd`` CLI subprocess.

    .. note::
        Stub registered in T01.  Full implementation added in T05/T06.
        All method calls on this stub raise :exc:`NotImplementedError`.
    """
