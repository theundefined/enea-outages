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

# Get a list of available regions
regions = client.get_available_regions()
print(f"Available regions: {regions}")

# Get all planned outages for the "Poznań" region
planned_outages = client.get_outages_for_region("Poznań", outage_type=OutageType.PLANNED)
print(f"Found {len(planned_outages)} planned outages in Poznań.")

# Get all unplanned outages for a specific address in "Szczecin"
unplanned_outages = client.get_outages_for_address(
    address="Wojska Polskiego",
    region="Szczecin",
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
# List all available regions
enea-outages --list-regions

# Get unplanned outages for a specific region
enea-outages --region "Poznań" --type unplanned

# Get planned outages for a specific address in a region
enea-outages --region "Szczecin" --address "Wojska Polskiego" --type planned
```

---

*This project was developed with the assistance of AI tools (Google Gemini). While the code has been reviewed, please use it with standard caution.*