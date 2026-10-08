from __future__ import annotations

import logging
import re
import warnings
from datetime import datetime
from types import TracebackType
from typing import Tuple

import httpx
from bs4 import BeautifulSoup, Tag

from .models import Outage, OutageType

logger = logging.getLogger(__name__)


class EneaOutagesClient:
    """Synchronous client for Enea Operator power outages."""

    BASE_URL = "https://wylaczenia.operator.enea.pl/index.php"
    DEFAULT_TIMEOUT = 10.0
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

    def __init__(self, timeout: float = DEFAULT_TIMEOUT) -> None:
        self._client = httpx.Client(timeout=timeout)

    def close(self) -> None:
        """Closes the underlying HTTP connection pool."""
        self._client.close()

    def __enter__(self) -> EneaOutagesClient:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

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

    def _fetch_raw_html(
        self,
        department: str,
        outage_type: OutageType,
        area: str | None = None,
        city: str | None = None,
        street: str | None = None,
    ) -> str:
        """Fetches the raw HTML content for a given department, area, city and street."""
        # The site remembers the last selected area ("rejon") in the PHP session and keeps
        # applying it to later searches, so drop cookies to make every request independent.
        self._client.cookies.clear()

        payload: dict[str, str] = {"page": outage_type.value, "oddzial": department}
        if area:
            payload["rejon"] = area

        if city or street:
            # The site only applies city/street filtering on a POST submission using these
            # exact field names; as GET query params (or under other names) they're ignored.
            if city:
                payload["unpl_city"] = city
            if street:
                payload["unpl_street"] = street
            response = self._client.post(self.BASE_URL, data=payload)
        else:
            response = self._client.get(self.BASE_URL, params=payload)

        response.raise_for_status()
        return response.text

    def get_outages_for_department(
        self,
        department: str = "Poznań",
        outage_type: OutageType = OutageType.UNPLANNED,
        area: str | None = None,
        city: str | None = None,
        street: str | None = None,
    ) -> list[Outage]:
        """
        Retrieves power outages for a specified department and type.

        Args:
            department: The name of the Enea Operator branch (e.g., "Poznań").
            outage_type: The type of outage to fetch (PLANNED or UNPLANNED).
            area: Optional sub-district id (only meaningful for some departments, e.g. Poznań).
            city: Optional city/town name ("miejscowość") to narrow the search.
            street: Optional street name ("ulica") to narrow the search.

        Returns:
            A list of Outage objects.
        """
        html = self._fetch_raw_html(department, outage_type, area=area, city=city, street=street)
        soup = BeautifulSoup(html, "html.parser")
        outage_blocks = soup.find_all("div", {"class": "unpl block info"})

        outages: list[Outage] = []
        for block in outage_blocks:
            try:
                outages.append(self._parse_outage_block(block))
            except (ValueError, AttributeError) as e:
                logger.warning("Error parsing outage block: %s", e)
        return outages

    def get_outages_for_address(
        self,
        address: str,
        department: str = "Poznań",
        outage_type: OutageType = OutageType.UNPLANNED,
        *,
        region: str | None = None,
    ) -> list[Outage]:
        """
        Retrieves power outages affecting a specific address.

        Args:
            address: The specific street or address to check.
            department: The name of the Enea Operator branch.
            outage_type: The type of outage to fetch.
            region: Deprecated alias for `department`.

        Returns:
            A list of Outage objects relevant to the given address.
        """
        if region is not None:
            _warn_deprecated("region", "department")
            department = region
        all_outages = self.get_outages_for_department(department, outage_type)
        return [o for o in all_outages if address.lower() in o.description.lower()]

    def get_available_departments(self) -> list[str]:
        """
        Retrieves the list of available departments (oddziały) from the Enea website.

        Returns:
            A list of available department names.
        """
        # The list of departments is the same for all page types, so we can hardcode one.
        html = self._fetch_raw_html(department="Poznań", outage_type=OutageType.PLANNED)
        soup = BeautifulSoup(html, "html.parser")

        department_select = soup.find("select", {"id": "oddzial"})
        if not isinstance(department_select, Tag):
            return []

        return [
            option["value"]
            for option in department_select.find_all("option")
            if option.has_attr("value") and option["value"]
        ]

    def get_outages_for_region(
        self, region: str = "Poznań", outage_type: OutageType = OutageType.UNPLANNED
    ) -> list[Outage]:
        """Deprecated alias for `get_outages_for_department`."""
        _warn_deprecated("get_outages_for_region", "get_outages_for_department")
        return self.get_outages_for_department(region, outage_type)

    def get_available_regions(self) -> list[str]:
        """Deprecated alias for `get_available_departments`."""
        _warn_deprecated("get_available_regions", "get_available_departments")
        return self.get_available_departments()

    def get_available_areas(self, department: str, outage_type: OutageType = OutageType.PLANNED) -> dict[str, str]:
        """
        Retrieves the available sub-districts ("rejony") for a given department (oddział).

        The site renders a `<select id="rejon">` populated server-side based on the
        `oddzial` query param, so the returned options differ per department.

        Args:
            department: The name of the Enea Operator branch (e.g., "Poznań").
            outage_type: The page type to fetch the select from (either works).

        Returns:
            A dict mapping area id to its display name, e.g. {"12": "Opalenica"}.
        """
        html = self._fetch_raw_html(department=department, outage_type=outage_type)
        soup = BeautifulSoup(html, "html.parser")

        area_select = soup.find("select", {"id": "rejon"})
        if not isinstance(area_select, Tag):
            return {}

        return {
            option["value"]: option.get_text(strip=True)
            for option in area_select.find_all("option")
            if option.has_attr("value") and option["value"]
        }


def _warn_deprecated(old: str, new: str) -> None:
    warnings.warn(f"'{old}' is deprecated, use '{new}' instead.", DeprecationWarning, stacklevel=3)
