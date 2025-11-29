import asyncio

from enea_outages.client import AsyncEneaOutagesClient, EneaOutagesClient


async def main():
    """Demonstrates the usage of the EneaOutagesClient and AsyncEneaOutagesClient."""

    # --- Synchronous Client Example ---
    print("--- Synchronous Client Example ---")
    sync_client = EneaOutagesClient()

    # Get available regions
    print("\nFetching available regions (synchronously)...")
    regions = sync_client.get_available_regions()
    print(f"Found {len(regions)} regions: {regions}")

    # Get all outages for a region
    print("\nFetching all outages for Poznań (synchronously)...")
    all_outages_sync = sync_client.get_outages_for_region("Poznań")
    if all_outages_sync:
        print(f"Found {len(all_outages_sync)} outage(s) in Poznań.")
        # print(f"  Obszar: {all_outages_sync[0].region}, Opis: {all_outages_sync[0].description}, Koniec: {all_outages_sync[0].end_time}")
    else:
        print("No outages found in Poznań.")

    # Get outages for a specific address
    street_to_check = "Zakopiańska"
    print(f"\nFetching outages for street '{street_to_check}' in Poznań (synchronously)...")
    address_outages_sync = sync_client.get_outages_for_address(street_to_check, "Poznań")
    if address_outages_sync:
        print(f"Found {len(address_outages_sync)} outage(s) for {street_to_check}:")
        for outage in address_outages_sync:
            print(f"  Obszar: {outage.region}, Opis: {outage.description}, Koniec: {outage.end_time}")
    else:
        print(f"No outages found for {street_to_check}.")

    # --- Asynchronous Client Example ---
    print("\n--- Asynchronous Client Example ---")
    async_client = AsyncEneaOutagesClient()
    
    # Get available regions
    print("\nFetching available regions (asynchronously)...")
    async_regions = await async_client.get_available_regions()
    print(f"Found {len(async_regions)} regions: {async_regions}")


    # Get all outages for a region
    print("\nFetching all outages for Poznań (asynchronously)...")
    all_outages_async = await async_client.get_outages_for_region("Poznań")
    if all_outages_async:
        print(f"Found {len(all_outages_async)} outage(s) in Poznań.")
        # print(f"  Obszar: {all_outages_async[0].region}, Opis: {all_outages_async[0].description}, Koniec: {all_outages_async[0].end_time}")

    else:
        print("No outages found in Poznań.")

    # Get outages for a specific address
    print(f"\nFetching outages for street '{street_to_check}' in Poznań (asynchronously)...")
    address_outages_async = await async_client.get_outages_for_address(street_to_check, "Poznań")
    if address_outages_async:
        print(f"Found {len(address_outages_async)} outage(s) for {street_to_check}:")
        for outage in address_outages_async:
            print(f"  Obszar: {outage.region}, Opis: {outage.description}, Koniec: {outage.end_time}")
    else:
        print(f"No outages found for {street_to_check}.")


if __name__ == "__main__":
    asyncio.run(main())
