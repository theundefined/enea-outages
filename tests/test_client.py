import pytest
from datetime import datetime
from bs4 import BeautifulSoup
import httpx
from pytest_httpx import HTTPXMock

from enea_outages.client import EneaOutagesClient, AsyncEneaOutagesClient
from enea_outages.models import OutageType

# --- Test Data ---

SAMPLE_UNPLANNED_BLOCK = """
<div class="unpl block info">
    <h4 class="title_">Test Unplanned Area</h4>
    <p class="bold subtext">
        29 listopada 2025 r.  do godziny 14:30
    </p>
    <p class="description">Unplanned outage description.</p>
</div>
"""

SAMPLE_PLANNED_BLOCK = """
<div class="unpl block info">
    <h4 class="title_">Test Planned Area</h4>
    <p class="bold subtext">
        8 grudnia 2025 r. w godz. 08:00 - 16:00
    </p>
    <p class="description">Planned outage description.</p>
</div>
"""

SAMPLE_HTML_PAGE_WITH_REGIONS = """
<html>
    <body>
        <select id="oddzial" name="oddzial">
            <option value="">wybierz oddział</option>
            <option value="Zielona Góra">Oddział Zielona Góra</option>
            <option value="Poznań" selected="selected">Oddział Poznań</option>
        </select>
    </body>
</html>
"""

# --- Fixtures ---


@pytest.fixture
def sync_client():
    return EneaOutagesClient()


@pytest.fixture
def async_client():
    return AsyncEneaOutagesClient()


# --- Parsing Tests ---


def test_parse_planned_date_format(sync_client: EneaOutagesClient):
    date_str = "8 grudnia 2025 r. w godz. 08:00 - 16:00"
    start_time, end_time = sync_client._parse_date_formats(date_str)
    assert start_time == datetime(2025, 12, 8, 8, 0)
    assert end_time == datetime(2025, 12, 8, 16, 0)


def test_parse_unplanned_date_format(sync_client: EneaOutagesClient):
    date_str = "29 listopada 2025 r. do godziny 14:30"
    start_time, end_time = sync_client._parse_date_formats(date_str)
    assert start_time is None
    assert end_time == datetime(2025, 11, 29, 14, 30)


def test_parse_invalid_date_format(sync_client: EneaOutagesClient):
    date_str = "Invalid date string"
    with pytest.raises(ValueError, match="Could not parse date information"):
        sync_client._parse_date_formats(date_str)


def test_parse_outage_block_planned(sync_client: EneaOutagesClient):
    soup = BeautifulSoup(SAMPLE_PLANNED_BLOCK, "html.parser")
    outage = sync_client._parse_outage_block(soup.find("div"))
    assert outage.region == "Test Planned Area"
    assert outage.start_time == datetime(2025, 12, 8, 8, 0)
    assert outage.end_time == datetime(2025, 12, 8, 16, 0)


def test_parse_outage_block_unplanned(sync_client: EneaOutagesClient):
    soup = BeautifulSoup(SAMPLE_UNPLANNED_BLOCK, "html.parser")
    outage = sync_client._parse_outage_block(soup.find("div"))
    assert outage.region == "Test Unplanned Area"
    assert outage.start_time is None
    assert outage.end_time == datetime(2025, 11, 29, 14, 30)


# --- Client Method Tests ---


def test_get_available_regions_sync(sync_client: EneaOutagesClient, httpx_mock: HTTPXMock):
    httpx_mock.add_response(text=SAMPLE_HTML_PAGE_WITH_REGIONS)
    regions = sync_client.get_available_regions()
    assert regions == ["Zielona Góra", "Poznań"]


@pytest.mark.asyncio
async def test_get_available_regions_async(async_client: AsyncEneaOutagesClient, httpx_mock: HTTPXMock):
    httpx_mock.add_response(text=SAMPLE_HTML_PAGE_WITH_REGIONS)
    regions = await async_client.get_available_regions()
    assert regions == ["Zielona Góra", "Poznań"]


def test_get_outages_for_region_unplanned_sync(sync_client: EneaOutagesClient, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{EneaOutagesClient.BASE_URL}?page={OutageType.UNPLANNED.value}&oddzial=Pozna%C5%84",
        text=f"<html><body>{SAMPLE_UNPLANNED_BLOCK}</body></html>",
    )
    outages = sync_client.get_outages_for_region("Poznań", OutageType.UNPLANNED)
    assert len(outages) == 1
    assert outages[0].region == "Test Unplanned Area"
    assert outages[0].start_time is None
    assert outages[0].end_time == datetime(2025, 11, 29, 14, 30)


def test_get_outages_for_region_planned_sync(sync_client: EneaOutagesClient, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{EneaOutagesClient.BASE_URL}?page={OutageType.PLANNED.value}&oddzial=Pozna%C5%84",
        text=f"<html><body>{SAMPLE_PLANNED_BLOCK}</body></html>",
    )
    outages = sync_client.get_outages_for_region("Poznań", OutageType.PLANNED)
    assert len(outages) == 1
    assert outages[0].region == "Test Planned Area"
    assert outages[0].start_time == datetime(2025, 12, 8, 8, 0)
    assert outages[0].end_time == datetime(2025, 12, 8, 16, 0)


@pytest.mark.asyncio
async def test_get_outages_for_region_unplanned_async(async_client: AsyncEneaOutagesClient, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{AsyncEneaOutagesClient.BASE_URL}?page={OutageType.UNPLANNED.value}&oddzial=Pozna%C5%84",
        text=f"<html><body>{SAMPLE_UNPLANNED_BLOCK}</body></html>",
    )
    outages = await async_client.get_outages_for_region("Poznań", OutageType.UNPLANNED)
    assert len(outages) == 1
    assert outages[0].start_time is None


@pytest.mark.asyncio
async def test_get_outages_for_region_planned_async(async_client: AsyncEneaOutagesClient, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{AsyncEneaOutagesClient.BASE_URL}?page={OutageType.PLANNED.value}&oddzial=Pozna%C5%84",
        text=f"<html><body>{SAMPLE_PLANNED_BLOCK}</body></html>",
    )
    outages = await async_client.get_outages_for_region("Poznań", OutageType.PLANNED)
    assert len(outages) == 1
    assert outages[0].start_time == datetime(2025, 12, 8, 8, 0)


def test_get_outages_for_address_unplanned_sync(sync_client: EneaOutagesClient, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{EneaOutagesClient.BASE_URL}?page={OutageType.UNPLANNED.value}&oddzial=Pozna%C5%84",
        text=f"<html><body>{SAMPLE_UNPLANNED_BLOCK}</body></html>",
        status_code=200,
    )
    httpx_mock.add_response(  # Second call for 'NonExistent'
        url=f"{EneaOutagesClient.BASE_URL}?page={OutageType.UNPLANNED.value}&oddzial=Pozna%C5%84",
        text=f"<html><body>{SAMPLE_UNPLANNED_BLOCK}</body></html>",
        status_code=200,
    )

    outages = sync_client.get_outages_for_address("Unplanned outage", "Poznań", OutageType.UNPLANNED)
    assert len(outages) == 1
    assert "Unplanned outage" in outages[0].description

    outages_no_match = sync_client.get_outages_for_address("NonExistent Street", "Poznań", OutageType.UNPLANNED)
    assert len(outages_no_match) == 0


def test_get_outages_for_address_planned_sync(sync_client: EneaOutagesClient, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{EneaOutagesClient.BASE_URL}?page={OutageType.PLANNED.value}&oddzial=Pozna%C5%84",
        text=f"<html><body>{SAMPLE_PLANNED_BLOCK}</body></html>",
        status_code=200,
    )
    httpx_mock.add_response(  # Second call for 'NonExistent'
        url=f"{EneaOutagesClient.BASE_URL}?page={OutageType.PLANNED.value}&oddzial=Pozna%C5%84",
        text=f"<html><body>{SAMPLE_PLANNED_BLOCK}</body></html>",
        status_code=200,
    )
    outages = sync_client.get_outages_for_address("Planned outage", "Poznań", OutageType.PLANNED)
    assert len(outages) == 1
    assert "Planned outage" in outages[0].description

    outages_no_match = sync_client.get_outages_for_address("NonExistent Street", "Poznań", OutageType.PLANNED)
    assert len(outages_no_match) == 0


@pytest.mark.asyncio
async def test_get_outages_for_address_unplanned_async(async_client: AsyncEneaOutagesClient, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{AsyncEneaOutagesClient.BASE_URL}?page={OutageType.UNPLANNED.value}&oddzial=Pozna%C5%84",
        text=f"<html><body>{SAMPLE_UNPLANNED_BLOCK}</body></html>",
        status_code=200,
    )
    httpx_mock.add_response(  # Second call for 'NonExistent'
        url=f"{AsyncEneaOutagesClient.BASE_URL}?page={OutageType.UNPLANNED.value}&oddzial=Pozna%C5%84",
        text=f"<html><body>{SAMPLE_UNPLANNED_BLOCK}</body></html>",
        status_code=200,
    )
    outages = await async_client.get_outages_for_address("Unplanned outage", "Poznań", OutageType.UNPLANNED)
    assert len(outages) == 1
    assert "Unplanned outage" in outages[0].description

    outages_no_match = await async_client.get_outages_for_address("NonExistent Street", "Poznań", OutageType.UNPLANNED)
    assert len(outages_no_match) == 0


@pytest.mark.asyncio
async def test_get_outages_for_address_planned_async(async_client: AsyncEneaOutagesClient, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{AsyncEneaOutagesClient.BASE_URL}?page={OutageType.PLANNED.value}&oddzial=Pozna%C5%84",
        text=f"<html><body>{SAMPLE_PLANNED_BLOCK}</body></html>",
        status_code=200,
    )
    httpx_mock.add_response(  # Second call for 'NonExistent'
        url=f"{AsyncEneaOutagesClient.BASE_URL}?page={OutageType.PLANNED.value}&oddzial=Pozna%C5%84",
        text=f"<html><body>{SAMPLE_PLANNED_BLOCK}</body></html>",
        status_code=200,
    )
    outages = await async_client.get_outages_for_address("Planned outage", "Poznań", OutageType.PLANNED)
    assert len(outages) == 1
    assert "Planned outage" in outages[0].description

    outages_no_match = await async_client.get_outages_for_address("NonExistent Street", "Poznań", OutageType.PLANNED)
    assert len(outages_no_match) == 0


def test_http_error_sync(sync_client: EneaOutagesClient, httpx_mock: HTTPXMock):
    httpx_mock.add_response(status_code=500)
    with pytest.raises(httpx.HTTPStatusError):
        sync_client.get_outages_for_region("Poznań")


@pytest.mark.asyncio
async def test_http_error_async(async_client: AsyncEneaOutagesClient, httpx_mock: HTTPXMock):
    httpx_mock.add_response(status_code=500)
    with pytest.raises(httpx.HTTPStatusError):
        await async_client.get_outages_for_region("Poznań")
