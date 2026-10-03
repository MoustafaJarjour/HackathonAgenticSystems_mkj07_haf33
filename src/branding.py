"""Shared AhaLab identity and the trusted offline logo asset."""
import base64
from pathlib import Path


NAME = "AhaLab"
TAGLINE = "Turn papers into playgrounds."
LOGO = Path(__file__).resolve().parent.parent / "assets" / "brand" / "ahalab-logo.png"


def logo_data_uri() -> str:
    return "data:image/png;base64," + base64.b64encode(LOGO.read_bytes()).decode("ascii")
