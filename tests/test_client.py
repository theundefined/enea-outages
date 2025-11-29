import pytest
from datetime import datetime
from bs4 import BeautifulSoup
import httpx
from pytest_httpx import HTTPXMock

from enea_outages.client import EneaOutagesClient, AsyncEneaOutagesClient

# Sample HTML block for testing
SAMPLE_HTML_BLOCK = """
<div class="unpl block info">
    <h4 class="title_">Test Area</h4>
    <p class="bold subtext">
        29 listopada 2025 r.  do godziny 14:30
    </p>
    <p class="description">Test description with street Test Street.</p>
</div>
"""

# Sample HTML content of the whole page
SAMPLE_HTML_PAGE = f"""
<html>
    <body>
        <div class="unpl_cont" id="unplhash">
            {SAMPLE_HTML_BLOCK}
        </div>
    </body>
</html>
"""

# Sample HTML with region selector
SAMPLE_HTML_PAGE_WITH_REGIONS = """
<html>
    <body>
        <select id="oddzial" name="oddzial">
            <option value="">wybierz oddział</option>
            <option value="Zielona Góra">Oddział Zielona Góra</option>
            <option value="Poznań" selected="selected">Oddział Poznań</option>
            <option value="Bydgoszcz">Oddział Bydgoszcz</option>
        </select>
    </body>
</html>
"""


@pytest.fixture
def sync_client():
    return EneaOutagesClient()


@pytest.fixture
def async_client():
    return AsyncEneaOutagesClient()


def test_parse_end_time_success(sync_client: EneaOutagesClient):
    date_str = "29 listopada 2025 r.  do godziny 14:30"
    expected_datetime = datetime(2025, 11, 29, 14, 30)
    assert sync_client._parse_end_time(date_str) == expected_datetime


def test_parse_end_time_invalid_month(sync_client: EneaOutagesClient):
    date_str = "29 nieznanego 2025 r. do godziny 14:30"
    with pytest.raises(ValueError, match="Unknown month name"):
        sync_client._parse_end_time(date_str)


def test_parse_end_time_invalid_format(sync_client: EneaOutagesClient):
    date_str = "Invalid date format"
    with pytest.raises(ValueError, match="Could not parse date information"):
        sync_client._parse_end_time(date_str)


def test_parse_outage_block(sync_client: EneaOutagesClient):
    soup = BeautifulSoup(SAMPLE_HTML_BLOCK, "html.parser")
    block = soup.find("div")
    outage = sync_client._parse_outage_block(block)

    assert outage.region == "Test Area"
    assert outage.description == "Test description with street Test Street."
    assert outage.end_time == datetime(2025, 11, 29, 14, 30)


def test_get_available_regions_sync(sync_client: EneaOutagesClient, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        method="GET",
        text=SAMPLE_HTML_PAGE_WITH_REGIONS,
        status_code=200,
    )
    regions = sync_client.get_available_regions()
    assert regions == ["Zielona Góra", "Poznań", "Bydgoszcz"]

@pytest.mark.asyncio
async def test_get_available_regions_async(async_client: AsyncEneaOutagesClient, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        method="GET",
        text=SAMPLE_HTML_PAGE_WITH_REGIONS,
        status_code=200,
    )
    regions = await async_client.get_available_regions()
    assert regions == ["Zielona Góra", "Poznań", "Bydgoszcz"]


def test_get_outages_for_region_sync(sync_client: EneaOutagesClient, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{EneaOutagesClient.BASE_URL}?page=awarie&oddzial=Pozna%C5%84",
        method="GET",
        text=SAMPLE_HTML_PAGE,
        status_code=200,
    )

    outages = sync_client.get_outages_for_region("Poznań")
    assert len(outages) == 1
    assert outages[0].region == "Test Area"


@pytest.mark.asyncio
async def test_get_outages_for_region_async(async_client: AsyncEneaOutagesClient, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{AsyncEneaOutagesClient.BASE_URL}?page=awarie&oddzial=Pozna%C5%84",
        method="GET",
        text=SAMPLE_HTML_PAGE,
        status_code=200,
    )

    outages = await async_client.get_outages_for_region("Poznań")
    assert len(outages) == 1
    assert outages[0].region == "Test Area"


def test_get_outages_for_address_sync(sync_client: EneaOutagesClient, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{EneaOutagesClient.BASE_URL}?page=awarie&oddzial=Pozna%C5%84",
        method="GET",
        text=SAMPLE_HTML_PAGE,
        status_code=200,
    )
    httpx_mock.add_response(
        url=f"{EneaOutagesClient.BASE_URL}?page=awarie&oddzial=Pozna%C5%84",
        method="GET",
        text=SAMPLE_HTML_PAGE,
        status_code=200,
    )

    outages = sync_client.get_outages_for_address("Test Street", "Poznań")
    assert len(outages) == 1
    assert "Test Street" in outages[0].description

    outages_no_match = sync_client.get_outages_for_address("NonExistent Street", "Poznań")
    assert len(outages_no_match) == 0


@pytest.mark.asyncio
async def test_get_outages_for_address_async(async_client: AsyncEneaOutagesClient, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{AsyncEneaOutagesClient.BASE_URL}?page=awarie&oddzial=Pozna%C5%84",
        method="GET",
        text=SAMPLE_HTML_PAGE,
        status_code=200,
    )
    httpx_mock.add_response(
        url=f"{AsyncEneaOutagesClient.BASE_URL}?page=awarie&oddzial=Pozna%C5%84",
        method="GET",
        text=SAMPLE_HTML_PAGE,
        status_code=200,
    )

    outages = await async_client.get_outages_for_address("Test Street", "Poznań")
    assert len(outages) == 1
    assert "Test Street" in outages[0].description

    outages_no_match = await async_client.get_outages_for_address("NonExistent Street", "Poznań")
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
