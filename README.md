# Enea Outages Python Library

A simple Python library to get information about power outages from the Enea Operator website.

## Installation

```bash
pip install enea-outages
```

## Usage (Python)

```python
from enea_outages.client import EneaOutagesClient
from enea_outages.models import OutageType

# Initialize the synchronous client
client = EneaOutagesClient()

# Get a list of available departments
departments = client.get_available_departments()
print(f"Available departments: {departments}")

# Get the available areas (rejony/sub-districts) for a given department
areas = client.get_available_areas("Poznań")
print(f"Available areas for Poznań: {areas}")  # e.g. {"12": "Opalenica", ...}

# Get all planned outages for the "Poznań" department
planned_outages = client.get_outages_for_department("Poznań", outage_type=OutageType.PLANNED)
print(f"Found {len(planned_outages)} planned outages in Poznań.")

# Narrow the search down to an area (sub-district id), city and/or street
narrowed_outages = client.get_outages_for_department(
    "Poznań",
    outage_type=OutageType.PLANNED,
    area="12",  # Opalenica
    city="Poznań",
    street="Kwiatowa",
)
print(f"Found {len(narrowed_outages)} planned outages for the given location.")

# Get all unplanned outages for a specific address in "Szczecin"
unplanned_outages = client.get_outages_for_address(
    address="Wojska Polskiego",
    department="Szczecin",
    outage_type=OutageType.UNPLANNED
)
print(f"Found {len(unplanned_outages)} unplanned outages for the address.")

if unplanned_outages:
    outage = unplanned_outages[0]
    print(
        f"Example -> Area: {outage.region}, "
        f"Description: {outage.description}, "
        f"End Time: {outage.end_time}"
    )
```

## Usage (CLI)

The library also provides a command-line interface (CLI) for quick checks.

```bash
# List all available departments
enea-outages --list-departments

# List available areas (sub-districts) for a department
enea-outages --department "Poznań" --list-areas

# Get unplanned outages for a specific department
enea-outages --department "Poznań" --type unplanned

# Narrow the search down to an area (by name or numeric id), city and/or street
enea-outages --department "Poznań" --area "Opalenica" --city "Komorniki" --street "Kwiatowa"

# Get planned outages for a specific address in a department
enea-outages --department "Szczecin" --address "Wojska Polskiego" --type planned
```

---

*This project was developed with the assistance of AI tools (Google Gemini). While the code has been reviewed, please use it with standard caution.*
