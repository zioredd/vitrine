"""Shared API helpers."""
from rest_framework.response import Response


def envelope(data, status=200):
    """Wrap payload in the standard {data: ...} response envelope."""
    return Response({"data": data}, status=status)
