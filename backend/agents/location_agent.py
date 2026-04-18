"""
Location Intelligence Agent
Provides reverse geocoding and nearby emergency services using OpenStreetMap APIs.
"""

import httpx
from typing import Dict, List, Optional
import asyncio


class LocationAgent:
    """Handles location-based intelligence for emergency response."""

    NOMINATIM_URL = "https://nominatim.openstreetmap.org"
    OVERPASS_URL = "https://overpass-api.de/api/interpreter"
    HEADERS = {"User-Agent": "GuardianAI-Emergency-System/1.0"}

    async def get_location_info(self, latitude: float, longitude: float) -> Dict:
        """
        Get comprehensive location information.
        
        Args:
            latitude: GPS latitude
            longitude: GPS longitude
            
        Returns:
            dict with address, coordinates, and nearby emergency services
        """
        # Run reverse geocoding and nearby services search in parallel
        address_task = self._reverse_geocode(latitude, longitude)
        services_task = self._find_nearby_services(latitude, longitude)

        address, nearby_services = await asyncio.gather(
            address_task, services_task
        )

        return {
            "address": address,
            "latitude": latitude,
            "longitude": longitude,
            "nearby_services": nearby_services,
        }

    async def _reverse_geocode(self, lat: float, lon: float) -> Optional[str]:
        """Convert coordinates to human-readable address."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.NOMINATIM_URL}/reverse",
                    params={
                        "lat": lat,
                        "lon": lon,
                        "format": "json",
                        "addressdetails": 1,
                    },
                    headers=self.HEADERS,
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("display_name", f"{lat}, {lon}")
        except Exception as e:
            print(f"[LocationAgent] Reverse geocoding failed: {e}")
        return f"{lat:.6f}, {lon:.6f}"

    async def _find_nearby_services(self, lat: float, lon: float, radius: int = 5000) -> List[Dict]:
        """Find nearby emergency services (hospitals, police, fire stations)."""
        services = []

        # Overpass QL query for emergency services within radius
        query = f"""
        [out:json][timeout:10];
        (
          node["amenity"="hospital"](around:{radius},{lat},{lon});
          node["amenity"="police"](around:{radius},{lat},{lon});
          node["amenity"="fire_station"](around:{radius},{lat},{lon});
          node["amenity"="clinic"](around:{radius},{lat},{lon});
          node["amenity"="pharmacy"](around:{radius},{lat},{lon});
        );
        out body 20;
        """

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    self.OVERPASS_URL,
                    data={"data": query},
                    headers=self.HEADERS,
                )
                if response.status_code == 200:
                    data = response.json()
                    for element in data.get("elements", []):
                        tags = element.get("tags", {})
                        service = {
                            "name": tags.get("name", "Unknown"),
                            "type": tags.get("amenity", "unknown"),
                            "latitude": element.get("lat"),
                            "longitude": element.get("lon"),
                            "phone": tags.get("phone", tags.get("contact:phone", "")),
                            "address": self._format_address(tags),
                        }
                        services.append(service)
        except Exception as e:
            print(f"[LocationAgent] Nearby services search failed: {e}")
            # Provide fallback data
            services = self._get_fallback_services(lat, lon)

        return services

    def _format_address(self, tags: Dict) -> str:
        """Format address from OSM tags."""
        parts = []
        for k in ["addr:street", "addr:housenumber", "addr:city", "addr:state"]:
            if k in tags:
                parts.append(tags[k])
        return ", ".join(parts) if parts else ""

    def _get_fallback_services(self, lat: float, lon: float) -> List[Dict]:
        """Provide generic fallback services when API is unavailable."""
        return [
            {
                "name": "Nearest Hospital",
                "type": "hospital",
                "latitude": lat + 0.01,
                "longitude": lon + 0.008,
                "phone": "108",
                "address": "Contact local emergency services",
            },
            {
                "name": "Police Station",
                "type": "police",
                "latitude": lat - 0.005,
                "longitude": lon + 0.012,
                "phone": "100",
                "address": "Contact local emergency services",
            },
            {
                "name": "Fire Station",
                "type": "fire_station",
                "latitude": lat + 0.008,
                "longitude": lon - 0.006,
                "phone": "101",
                "address": "Contact local emergency services",
            },
        ]
