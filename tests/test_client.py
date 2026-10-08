from datetime import datetime

import httpx
import pytest
from bs4 import BeautifulSoup
from pytest_httpx import HTTPXMock

from enea_outages.client import EneaOutagesClient
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


def test_get_available_departments_sync(sync_client: EneaOutagesClient, httpx_mock: HTTPXMock):
    httpx_mock.add_response(text=SAMPLE_HTML_PAGE_WITH_REGIONS)
    departments = sync_client.get_available_departments()
    assert departments == ["Zielona Góra", "Poznań"]


def test_get_outages_for_department_unplanned_sync(sync_client: EneaOutagesClient, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{EneaOutagesClient.BASE_URL}?page={OutageType.UNPLANNED.value}&oddzial=Pozna%C5%84",
        text=f"<html><body>{SAMPLE_UNPLANNED_BLOCK}</body></html>",
    )
    outages = sync_client.get_outages_for_department("Poznań", OutageType.UNPLANNED)
    assert len(outages) == 1
    assert outages[0].region == "Test Unplanned Area"
    assert outages[0].start_time is None
    assert outages[0].end_time == datetime(2025, 11, 29, 14, 30)


def test_get_outages_for_department_planned_sync(sync_client: EneaOutagesClient, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{EneaOutagesClient.BASE_URL}?page={OutageType.PLANNED.value}&oddzial=Pozna%C5%84",
        text=f"<html><body>{SAMPLE_PLANNED_BLOCK}</body></html>",
    )
    outages = sync_client.get_outages_for_department("Poznań", OutageType.PLANNED)
    assert len(outages) == 1
    assert outages[0].region == "Test Planned Area"
    assert outages[0].start_time == datetime(2025, 12, 8, 8, 0)
    assert outages[0].end_time == datetime(2025, 12, 8, 16, 0)


def test_get_outages_for_department_with_area_city_street_sync(sync_client: EneaOutagesClient, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        method="POST",
        url=EneaOutagesClient.BASE_URL,
        match_content=b"page=awarie&oddzial=Pozna%C5%84&rejon=12&unpl_city=Komorniki&unpl_street=Kwiatowa",
        text=f"<html><body>{SAMPLE_UNPLANNED_BLOCK}</body></html>",
    )
    outages = sync_client.get_outages_for_department(
        "Poznań", OutageType.UNPLANNED, area="12", city="Komorniki", street="Kwiatowa"
    )
    assert len(outages) == 1
    assert outages[0].region == "Test Unplanned Area"


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


def test_http_error_sync(sync_client: EneaOutagesClient, httpx_mock: HTTPXMock):
    httpx_mock.add_response(status_code=500)
    with pytest.raises(httpx.HTTPStatusError):
        sync_client.get_outages_for_department("Poznań")


# --- Edge Case Tests ---


def test_parse_date_format_unknown_month_planned(sync_client: EneaOutagesClient):
    date_str = "8 marsjanina 2025 r. w godz. 08:00 - 16:00"
    with pytest.raises(ValueError, match="Unknown month name"):
        sync_client._parse_date_formats(date_str)


def test_parse_date_format_unknown_month_unplanned(sync_client: EneaOutagesClient):
    date_str = "19 marsjanina 2025 r. do godziny 12:30"
    with pytest.raises(ValueError, match="Unknown month name"):
        sync_client._parse_date_formats(date_str)


def test_get_outages_for_department_skips_unparseable_block(
    sync_client: EneaOutagesClient, httpx_mock: HTTPXMock, caplog: pytest.LogCaptureFixture
):
    unparseable_block = """
    <div class="unpl block info">
        <h4 class="title_">Broken Block</h4>
        <p class="bold subtext">not a date at all</p>
        <p class="description">Broken description.</p>
    </div>
    """
    httpx_mock.add_response(
        text=f"<html><body>{unparseable_block}{SAMPLE_UNPLANNED_BLOCK}</body></html>",
    )
    with caplog.at_level("WARNING"):
        outages = sync_client.get_outages_for_department("Poznań", OutageType.UNPLANNED)

    assert len(outages) == 1
    assert outages[0].region == "Test Unplanned Area"
    assert "Error parsing outage block" in caplog.text


def test_get_outages_for_department_skips_block_raising_attribute_error(
    sync_client: EneaOutagesClient,
    httpx_mock: HTTPXMock,
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
):
    httpx_mock.add_response(
        text=f"<html><body>{SAMPLE_UNPLANNED_BLOCK}</body></html>",
    )

    def raise_attribute_error(self, block):
        raise AttributeError("simulated malformed block")

    monkeypatch.setattr(EneaOutagesClient, "_parse_outage_block", raise_attribute_error)

    with caplog.at_level("WARNING"):
        outages = sync_client.get_outages_for_department("Poznań", OutageType.UNPLANNED)

    assert outages == []
    assert "Error parsing outage block" in caplog.text


def test_get_available_areas_sync(sync_client: EneaOutagesClient, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        text=(
            "<html><body>"
            '<select id="rejon" name="rejon">'
            '<option value="7">Poznań</option>'
            '<option value="12">Opalenica</option>'
            "</select>"
            "</body></html>"
        )
    )
    areas = sync_client.get_available_areas("Poznań")
    assert areas == {"7": "Poznań", "12": "Opalenica"}


def test_get_available_areas_no_select_tag(sync_client: EneaOutagesClient, httpx_mock: HTTPXMock):
    httpx_mock.add_response(text="<html><body><p>No rejon selector here.</p></body></html>")
    areas = sync_client.get_available_areas("Szczecin")
    assert areas == {}


def test_get_available_departments_no_select_tag(sync_client: EneaOutagesClient, httpx_mock: HTTPXMock):
    httpx_mock.add_response(text="<html><body><p>No region selector here.</p></body></html>")
    departments = sync_client.get_available_departments()
    assert departments == []


# --- Backward Compatibility Tests ---


def test_get_outages_for_region_is_deprecated_alias(sync_client: EneaOutagesClient, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{EneaOutagesClient.BASE_URL}?page={OutageType.PLANNED.value}&oddzial=Pozna%C5%84",
        text=f"<html><body>{SAMPLE_PLANNED_BLOCK}</body></html>",
    )
    with pytest.warns(DeprecationWarning, match="get_outages_for_department"):
        outages = sync_client.get_outages_for_region(region="Poznań", outage_type=OutageType.PLANNED)
    assert len(outages) == 1
    assert outages[0].region == "Test Planned Area"


def test_get_available_regions_is_deprecated_alias(sync_client: EneaOutagesClient, httpx_mock: HTTPXMock):
    httpx_mock.add_response(text=SAMPLE_HTML_PAGE_WITH_REGIONS)
    with pytest.warns(DeprecationWarning, match="get_available_departments"):
        regions = sync_client.get_available_regions()
    assert regions == ["Zielona Góra", "Poznań"]


def test_get_outages_for_address_accepts_deprecated_region_kwarg(sync_client: EneaOutagesClient, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{EneaOutagesClient.BASE_URL}?page={OutageType.UNPLANNED.value}&oddzial=Szczecin",
        text=f"<html><body>{SAMPLE_UNPLANNED_BLOCK}</body></html>",
    )
    with pytest.warns(DeprecationWarning, match="department"):
        outages = sync_client.get_outages_for_address("unplanned", region="Szczecin")
    assert len(outages) == 1


def test_session_cookies_do_not_leak_between_requests(sync_client: EneaOutagesClient, httpx_mock: HTTPXMock):
    # The site stores the selected area in the session; a later search must not inherit it.
    httpx_mock.add_response(
        headers={"Set-Cookie": "PHPSESSID=abc; Path=/"},
        text=f"<html><body>{SAMPLE_UNPLANNED_BLOCK}</body></html>",
    )
    httpx_mock.add_response(text=f"<html><body>{SAMPLE_UNPLANNED_BLOCK}</body></html>")

    sync_client.get_outages_for_department("Poznań", area="8")
    sync_client.get_outages_for_department("Poznań", city="Poznań")

    second_request = httpx_mock.get_requests()[1]
    assert "cookie" not in second_request.headers
