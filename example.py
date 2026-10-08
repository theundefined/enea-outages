from enea_outages.client import EneaOutagesClient
from enea_outages.models import OutageType


def main():
    """Demonstrates the usage of the EneaOutagesClient."""

    print("--- Synchronous Client Example ---")
    sync_client = EneaOutagesClient()

    # Get available departments
    print("\nFetching available departments...")
    departments = sync_client.get_available_departments()
    print(f"Found {len(departments)} departments: {departments}")

    # Get all PLANNED outages for a department
    print("\nFetching all PLANNED outages for Poznań...")
    planned_outages_sync = sync_client.get_outages_for_department("Poznań", outage_type=OutageType.PLANNED)
    if planned_outages_sync:
        print(f"Found {len(planned_outages_sync)} PLANNED outage(s) in Poznań.")
        # Print details for the first one as an example
        outage = planned_outages_sync[0]
        print(f"  Example -> Obszar: {outage.region}, Początek: {outage.start_time}, Koniec: {outage.end_time}")
    else:
        print("No PLANNED outages found in Poznań.")

    # Get all UNPLANNED outages for a department
    print("\nFetching all UNPLANNED outages for Poznań...")
    unplanned_outages_sync = sync_client.get_outages_for_department("Poznań", outage_type=OutageType.UNPLANNED)
    if unplanned_outages_sync:
        print(f"Found {len(unplanned_outages_sync)} UNPLANNED outage(s) in Poznań.")
        outage = unplanned_outages_sync[0]
        print(f"  Example -> Obszar: {outage.region}, Koniec: {outage.end_time}")
    else:
        print("No UNPLANNED outages found in Poznań.")


if __name__ == "__main__":
    main()
