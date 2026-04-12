from __future__ import annotations

from io import BytesIO

import segno


def make_qr_svg(data: str) -> str:
    qr = segno.make(data, error="m")
    output = BytesIO()
    qr.save(output, kind="svg", scale=6, border=2, dark="#2b2418", light=None)
    return output.getvalue().decode("utf-8")


def make_qr_png(data: str) -> bytes:
    qr = segno.make(data, error="m")
    output = BytesIO()
    qr.save(output, kind="png", scale=6, border=2, dark="#2b2418", light=None)
    return output.getvalue()
