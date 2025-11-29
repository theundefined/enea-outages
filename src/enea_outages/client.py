from __future__ import annotations

import re
from datetime import datetime
from typing import Any

import httpx
from bs4 import BeautifulSoup

from .models import Outage


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

    def _parse_end_time(self, date_info: str) -> datetime:
        """Parses the date information string into a datetime object."""
        # Example: "19 listopada 2025 r.  do godziny 12:30"
        match = re.search(
            r"(\d{1,2})\s+(\w+)\s+(\d{4})\s+r\.\s+do\s+godziny\s+(\d{1,2}):(\d{1,2})", date_info
        )
        if not match:
            raise ValueError(f"Could not parse date information: {date_info}")

        day, month_name, year, hour, minute = match.groups()
        month = self.MONTH_MAP.get(month_name.lower())
        if month is None:
            raise ValueError(f"Unknown month name: {month_name}")

        return datetime(int(year), month, int(day), int(hour), int(minute))

    def _parse_outage_block(self, block: BeautifulSoup) -> Outage:
        """Parses a single outage HTML block into an Outage object."""
        region_tag = block.find("h4", {"class": "title_"})
        description_tag = block.find("p", {"class": "description"})
        date_info_tag = block.find("p", {"class": "bold subtext"})

        region = region_tag.get_text(strip=True) if region_tag else "Nieznany obszar"
        description = description_tag.get_text(strip=True) if description_tag else "Brak opisu"
        date_info_str = date_info_tag.get_text(strip=True) if date_info_tag else ""

        end_time = self._parse_end_time(date_info_str)

        return Outage(region=region, description=description, end_time=end_time)

    def _fetch_raw_html(self, region: str) -> str:
        """Fetches the raw HTML content for a given region."""
        params = {"page": "awarie", "oddzial": region}
        response = httpx.get(self.BASE_URL, params=params)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.text

    def get_outages_for_region(self, region: str = "Poznań") -> list[Outage]:
        """
        Retrieves all current power outages for a specified region.

        Args:
            region (str): The name of the Enea Operator branch (e.g., "Poznań").

        Returns:
            list[Outage]: A list of Outage objects.
        """
        html = self._fetch_raw_html(region)
        soup = BeautifulSoup(html, "html.parser")
        outage_blocks = soup.find_all("div", {"class": "unpl block info"})

        outages: list[Outage] = []
        for block in outage_blocks:
            try:
                outages.append(self._parse_outage_block(block))
            except (ValueError, AttributeError) as e:
                print(f"Error parsing outage block: {e} in block: {block}")
                # Optionally log the error or handle it differently

        return outages

    def get_outages_for_address(self, address: str, region: str = "Poznań") -> list[Outage]:
        """
        Retrieves power outages affecting a specific address within a region.

        Args:
            address (str): The specific street or address to check (e.g., "Zakopiańska").
            region (str): The name of the Enea Operator branch (e.g., "Poznań").

        Returns:
            list[Outage]: A list of Outage objects relevant to the given address.
        """
        all_outages = self.get_outages_for_region(region)
        
        # Filter locally, as Enea website does not provide specific address filtering via URL
        filtered_outages = [
            outage for outage in all_outages if address.lower() in outage.description.lower()
        ]
        return filtered_outages

    def get_available_regions(self) -> list[str]:
        """
        Retrieves the list of available regions (oddziały) from the Enea website.

        Returns:
            list[str]: A list of available region names.
        """
        # We can fetch with any valid region, or no region, to get the page with the form
        html = self._fetch_raw_html(region="Poznań")
        soup = BeautifulSoup(html, "html.parser")
        
        region_select = soup.find("select", {"id": "oddzial"})
        if not region_select:
            return []

        regions = [
            option["value"]
            for option in region_select.find_all("option")
            if option.has_attr("value") and option["value"]
        ]
        return regions


class AsyncEneaOutagesClient(EneaOutagesClient):
    """Asynchronous client for Enea Operator power outages."""

    async def _fetch_raw_html(self, region: str) -> str:
        """Fetches the raw HTML content for a given region asynchronously."""
        async with httpx.AsyncClient() as client:
            params = {"page": "awarie", "oddzial": region}
            response = await client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            return response.text

    async def get_outages_for_region(self, region: str = "Poznań") -> list[Outage]:
        """
        Retrieves all current power outages for a specified region asynchronously.

        Args:
            region (str): The name of the Enea Operator branch (e.g., "Poznań").

        Returns:
            list[Outage]: A list of Outage objects.
        """
        html = await self._fetch_raw_html(region)
        soup = BeautifulSoup(html, "html.parser")
        outage_blocks = soup.find_all("div", {"class": "unpl block info"})

        outages: list[Outage] = []
        for block in outage_blocks:
            try:
                outages.append(self._parse_outage_block(block))
            except (ValueError, AttributeError) as e:
                print(f"Error parsing outage block: {e} in block: {block}")

        return outages

    async def get_outages_for_address(self, address: str, region: str = "Poznań") -> list[Outage]:
        """
        Retrieves power outages affecting a specific address within a region asynchronously.

        Args:
            address (str): The specific street or address to check (e.g., "Zakopiańska").
            region (str): The name of the Enea Operator branch (e.g., "Poznań").

        Returns:
            list[Outage]: A list of Outage objects relevant to the given address.
        """
        all_outages = await self.get_outages_for_region(region)
        filtered_outages = [
            outage for outage in all_outages if address.lower() in outage.description.lower()
        ]
        return filtered_outages

    async def get_available_regions(self) -> list[str]:
        """
        Retrieves the list of available regions (oddziały) from the Enea website asynchronously.

        Returns:
            list[str]: A list of available region names.
        """
        # We can fetch with any valid region, or no region, to get the page with the form
        html = await self._fetch_raw_html(region="Poznań")
        soup = BeautifulSoup(html, "html.parser")
        
        region_select = soup.find("select", {"id": "oddzial"})
        if not region_select:
            return []

        regions = [
            option["value"]
            for option in region_select.find_all("option")
            if option.has_attr("value") and option["value"]
        ]
        return regions
