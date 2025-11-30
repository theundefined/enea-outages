from __future__ import annotations

import re
from datetime import datetime
from typing import Tuple

import httpx
from bs4 import BeautifulSoup

from .models import Outage, OutageType


class EneaOutagesClient:
    """Synchronous client for Enea Operator power outages."""

    BASE_URL = "https://wylaczenia-eneaoperator.pl/index.php"
    MONTH_MAP = {
        "stycznia": 1,
        "lutego": 2,
        "marca": 3,
        "kwietnia": 4,
        "maja": 5,
        "czerwca": 6,
        "lipca": 7,
        "sierpnia": 8,
        "września": 9,
        "października": 10,
        "listopada": 11,
        "grudnia": 12,
    }

    def _parse_date_formats(self, date_info: str) -> Tuple[datetime | None, datetime | None]:
        """
        Parses different date formats and returns a tuple of (start_time, end_time).
        """
        # Planned outage format: "8 grudnia 2025 r. w godz. 08:00 - 16:00"
        planned_match = re.search(
            r"(\d{1,2})\s+(\w+)\s+(\d{4})\s+r\.\s+w\s+godz\.\s+(\d{1,2}):(\d{2})\s+-\s+(\d{1,2}):(\d{2})", date_info
        )
        if planned_match:
            day, month_name, year, start_hour, start_min, end_hour, end_min = planned_match.groups()
            month = self.MONTH_MAP.get(month_name.lower())
            if not month:
                raise ValueError(f"Unknown month name: {month_name}")

            start_time = datetime(int(year), month, int(day), int(start_hour), int(start_min))
            end_time = datetime(int(year), month, int(day), int(end_hour), int(end_min))
            return start_time, end_time

        # Unplanned outage format: "19 listopada 2025 r. do godziny 12:30"
        unplanned_match = re.search(r"(\d{1,2})\s+(\w+)\s+(\d{4})\s+r\.\s+do\s+godziny\s+(\d{1,2}):(\d{2})", date_info)
        if unplanned_match:
            day, month_name, year, hour, minute = unplanned_match.groups()
            month = self.MONTH_MAP.get(month_name.lower())
            if not month:
                raise ValueError(f"Unknown month name: {month_name}")

            # For unplanned, we only have an end time. Start time is unknown.
            end_time = datetime(int(year), month, int(day), int(hour), int(minute))
            return None, end_time

        raise ValueError(f"Could not parse date information: {date_info}")

    def _parse_outage_block(self, block: BeautifulSoup) -> Outage:
        """Parses a single outage HTML block into an Outage object."""
        region_tag = block.find("h4", {"class": "title_"})
        description_tag = block.find("p", {"class": "description"})
        date_info_tag = block.find("p", {"class": "bold subtext"})

        region = region_tag.get_text(strip=True) if region_tag else "Nieznany obszar"
        description = description_tag.get_text(strip=True) if description_tag else "Brak opisu"
        date_info_str = date_info_tag.get_text(strip=True) if date_info_tag else ""

        start_time, end_time = self._parse_date_formats(date_info_str)

        return Outage(region=region, description=description, start_time=start_time, end_time=end_time)

    def _fetch_raw_html(self, region: str, outage_type: OutageType) -> str:
        """Fetches the raw HTML content for a given region and outage type."""
        params = {"page": outage_type.value, "oddzial": region}
        response = httpx.get(self.BASE_URL, params=params)
        response.raise_for_status()
        return response.text

    def get_outages_for_region(
        self, region: str = "Poznań", outage_type: OutageType = OutageType.UNPLANNED
    ) -> list[Outage]:
        """
        Retrieves power outages for a specified region and type.

        Args:
            region: The name of the Enea Operator branch (e.g., "Poznań").
            outage_type: The type of outage to fetch (PLANNED or UNPLANNED).

        Returns:
            A list of Outage objects.
        """
        html = self._fetch_raw_html(region, outage_type)
        soup = BeautifulSoup(html, "html.parser")
        outage_blocks = soup.find_all("div", {"class": "unpl block info"})

        outages: list[Outage] = []
        for block in outage_blocks:
            try:
                outages.append(self._parse_outage_block(block))
            except (ValueError, AttributeError) as e:
                print(f"Error parsing outage block: {e}")
        return outages

    def get_outages_for_address(
        self, address: str, region: str = "Poznań", outage_type: OutageType = OutageType.UNPLANNED
    ) -> list[Outage]:
        """
        Retrieves power outages affecting a specific address.

        Args:
            address: The specific street or address to check.
            region: The name of the Enea Operator branch.
            outage_type: The type of outage to fetch.

        Returns:
            A list of Outage objects relevant to the given address.
        """
        all_outages = self.get_outages_for_region(region, outage_type)
        return [o for o in all_outages if address.lower() in o.description.lower()]

    def get_available_regions(self) -> list[str]:
        """
        Retrieves the list of available regions (oddziały) from the Enea website.

        Returns:
            A list of available region names.
        """
        # The list of regions is the same for all page types, so we can hardcode one.
        html = self._fetch_raw_html(region="Poznań", outage_type=OutageType.PLANNED)
        soup = BeautifulSoup(html, "html.parser")

        region_select = soup.find("select", {"id": "oddzial"})
        if not region_select:
            return []

        return [
            option["value"]
            for option in region_select.find_all("option")
            if option.has_attr("value") and option["value"]
        ]


class AsyncEneaOutagesClient(EneaOutagesClient):
    """Asynchronous client for Enea Operator power outages."""

    async def _fetch_raw_html(self, region: str, outage_type: OutageType) -> str:
        """Fetches the raw HTML content asynchronously."""
        async with httpx.AsyncClient() as client:
            params = {"page": outage_type.value, "oddzial": region}
            response = await client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            return response.text

    async def get_outages_for_region(
        self, region: str = "Poznań", outage_type: OutageType = OutageType.UNPLANNED
    ) -> list[Outage]:
        """Retrieves power outages for a specified region and type asynchronously."""
        html = await self._fetch_raw_html(region, outage_type)
        soup = BeautifulSoup(html, "html.parser")
        outage_blocks = soup.find_all("div", {"class": "unpl block info"})

        outages: list[Outage] = []
        for block in outage_blocks:
            try:
                outages.append(self._parse_outage_block(block))
            except (ValueError, AttributeError) as e:
                print(f"Error parsing outage block: {e}")
        return outages

    async def get_outages_for_address(
        self, address: str, region: str = "Poznań", outage_type: OutageType = OutageType.UNPLANNED
    ) -> list[Outage]:
        """Retrieves power outages affecting a specific address asynchronously."""
        all_outages = await self.get_outages_for_region(region, outage_type)
        return [o for o in all_outages if address.lower() in o.description.lower()]

    async def get_available_regions(self) -> list[str]:
        """Retrieves the list of available regions asynchronously."""
        # The list of regions is the same for all page types, so we can hardcode one.
        html = await self._fetch_raw_html(region="Poznań", outage_type=OutageType.PLANNED)
        soup = BeautifulSoup(html, "html.parser")

        region_select = soup.find("select", {"id": "oddzial"})
        if not region_select:
            return []

        return [
            option["value"]
            for option in region_select.find_all("option")
            if option.has_attr("value") and option["value"]
        ]
