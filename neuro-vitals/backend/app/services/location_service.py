"""
Location Service – resolves the client's GPS or IP-based
geolocation for outbreak mapping.

Migrated from hackathon_project1/location_service.py.
"""

import logging
import httpx
from fastapi import Request

logger = logging.getLogger(__name__)

async def reverse_geocode(lat: float, lon: float) -> dict:
    """Reverse geocode coordinates via Nominatim."""
    try:
        async with httpx.AsyncClient() as client:
            # Note: User-Agent is required by Nominatim
            headers = {"User-Agent": "Neuro-Vitals-App/1.0"}
            resp = await client.get(
                f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}",
                headers=headers,
                timeout=5.0
            )
            if resp.status_code == 200:
                data = resp.json()
                addr = data.get("address", {})
                return {
                    "city": addr.get("city") or addr.get("town") or addr.get("village") or "Unknown",
                    "region": addr.get("state") or addr.get("county") or "Unknown",
                    "country": addr.get("country") or "Unknown",
                    "exact_location": data.get("display_name") or "Unknown"
                }
    except Exception as exc:
        logger.warning("Reverse geocode failed: %s", exc)
    return {}


async def get_client_location(
    request: Request,
    gps_latitude: float | None = None,
    gps_longitude: float | None = None,
    city: str | None = None,
    country: str | None = None,
    exact_location: str | None = None
) -> dict:
    """Return a location dict with lat/lng/city/region/country/source/exact_location."""
    try:
        # Prefer browser GPS when available
        if gps_latitude and gps_longitude:
            logger.info("GPS coordinates received: %s, %s", gps_latitude, gps_longitude)
            
            # Resolve address on backend to save frontend time
            addr = await reverse_geocode(gps_latitude, gps_longitude)
            
            return {
                "latitude": float(gps_latitude),
                "longitude": float(gps_longitude),
                "city": addr.get("city") or city or "Unknown",
                "region": addr.get("region") or "Unknown",
                "country": addr.get("country") or country or "Unknown",
                "ip": request.client.host,
                "source": "gps",
                "exact_location": exact_location or addr.get("exact_location") or f"{city}, {country}"
            }

        # Fallback: IP geolocation
        client_ip = request.client.host
        logger.info("No GPS – using IP geolocation for %s", client_ip)

        if client_ip in ("127.0.0.1", "::1"):
            try:
                async with httpx.AsyncClient() as client:
                    ip_resp = await client.get("https://api.ipify.org?format=json")
                    if ip_resp.status_code == 200:
                        client_ip = ip_resp.json()["ip"]
            except Exception:
                pass

        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://ip-api.com/json/{client_ip}")
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    return {
                        "latitude": data.get("lat"),
                        "longitude": data.get("lon"),
                        "city": data.get("city"),
                        "region": data.get("regionName"),
                        "country": data.get("country"),
                        "ip": client_ip,
                        "source": "ip_geolocation",
                        "exact_location": data.get("city") + ", " + data.get("country")
                    }
    except Exception as exc:
        logger.error("Location error: %s", exc)

    return {
        "latitude": None,
        "longitude": None,
        "city": None,
        "region": None,
        "country": None,
        "ip": request.client.host,
        "source": "unknown",
        "exact_location": "Unknown"
    }
