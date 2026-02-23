from datetime import datetime
from typing import Any, Dict


class ConnectorError(Exception):
    pass


def _masked(config: Dict[str, Any]) -> Dict[str, Any]:
    hidden = {}
    for key, value in config.items():
        if any(s in key.lower() for s in ["pass", "token", "secret", "key"]):
            hidden[key] = "***"
        else:
            hidden[key] = value
    return hidden


def fetch_provider_data(provider: str, config: Dict[str, Any]) -> Dict[str, Any]:
    provider = provider.lower()
    if provider not in SUPPORTED_PROVIDERS:
        raise ConnectorError(f"Provider '{provider}' wird noch nicht unterstützt")

    return {
        "provider": provider,
        "synced_at": datetime.utcnow().isoformat(),
        "status": "demo",
        "hint": "Connector-Skeleton aktiv. Hier echte API-Implementierung ergänzen.",
        "config_preview": _masked(config),
    }


SUPPORTED_PROVIDERS = {
    "webuntis": "Stundenpläne / Schulinfos",
    "imap": "E-Mail Abruf",
    "caldav": "Kalenderdaten",
    "immich": "Bilder & Alben",
    "tesla": "Fahrzeugstatus Tesla",
    "cupra": "Fahrzeugstatus Cupra",
    "proxmox": "Server / Cluster Daten",
    "weather": "Wetterinformationen",
}
