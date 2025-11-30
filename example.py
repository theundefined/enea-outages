import asyncio

from enea_outages.client import AsyncEneaOutagesClient, EneaOutagesClient
from enea_outages.models import OutageType


async def main():
    """Demonstrates the usage of the EneaOutagesClient and AsyncEneaOutagesClient."""

    print("--- Synchronous Client Example ---")
    sync_client = EneaOutagesClient()

    # Get available regions
    print("\nFetching available regions...")
    regions = sync_client.get_available_regions()
    print(f"Found {len(regions)} regions: {regions}")

    # Get all PLANNED outages for a region
    print("\nFetching all PLANNED outages for Poznań...")
    planned_outages_sync = sync_client.get_outages_for_region("Poznań", outage_type=OutageType.PLANNED)
    if planned_outages_sync:
        print(f"Found {len(planned_outages_sync)} PLANNED outage(s) in Poznań.")
        # Print details for the first one as an example
        outage = planned_outages_sync[0]
        print(f"  Example -> Obszar: {outage.region}, Początek: {outage.start_time}, Koniec: {outage.end_time}")
    else:
        print("No PLANNED outages found in Poznań.")

    # Get all UNPLANNED outages for a region
    print("\nFetching all UNPLANNED outages for Poznań...")
    unplanned_outages_sync = sync_client.get_outages_for_region("Poznań", outage_type=OutageType.UNPLANNED)
    if unplanned_outages_sync:
        print(f"Found {len(unplanned_outages_sync)} UNPLANNED outage(s) in Poznań.")
        outage = unplanned_outages_sync[0]
        print(f"  Example -> Obszar: {outage.region}, Koniec: {outage.end_time}")
    else:
        print("No UNPLANNED outages found in Poznań.")

    print("\n" + "=" * 50 + "\n")

    print("--- Asynchronous Client Example ---")
    async_client = AsyncEneaOutagesClient()

    # Get available regions
    print("\nFetching available regions (asynchronously)...")
    async_regions = await async_client.get_available_regions()
    print(f"Found {len(async_regions)} regions: {async_regions}")

    # Get all PLANNED outages for a region
    print("\nFetching all PLANNED outages for Poznań (asynchronously)...")
    async_planned_outages = await async_client.get_outages_for_region("Poznań", outage_type=OutageType.PLANNED)
    if async_planned_outages:
        print(f"Found {len(async_planned_outages)} PLANNED outage(s) in Poznań.")
    else:
        print("No PLANNED outages found in Poznań.")

    # Get all UNPLANNED outages for a region
    print("\nFetching all UNPLANNED outages for Poznań (asynchronously)...")
    async_unplanned_outages = await async_client.get_outages_for_region("Poznań", outage_type=OutageType.UNPLANNED)
    if async_unplanned_outages:
        print(f"Found {len(async_unplanned_outages)} UNPLANNED outage(s) in Poznań.")
    else:
        print("No UNPLANNED outages found in Poznań.")


if __name__ == "__main__":
    asyncio.run(main())
