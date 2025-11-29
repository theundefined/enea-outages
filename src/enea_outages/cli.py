import argparse
import asyncio
from datetime import datetime

from .client import AsyncEneaOutagesClient


async def async_main():
    """Asynchronous main function to handle CLI logic."""
    parser = argparse.ArgumentParser(description="Enea Outages CLI Tool")
    parser.add_argument(
        "--list-regions",
        action="store_true",
        help="List all available regions (oddziały) and exit.",
    )
    parser.add_argument(
        "--region",
        default="Poznań",
        help="Specify the region to check for outages. Default is 'Poznań'.",
    )
    parser.add_argument(
        "--address",
        help="Specify a street address to filter outages. Requires --region.",
    )
    args = parser.parse_args()

    client = AsyncEneaOutagesClient()

    if args.list_regions:
        print("Fetching available regions...")
        try:
            regions = await client.get_available_regions()
            if regions:
                print("Available regions:")
                for region in regions:
                    print(f"- {region}")
            else:
                print("Could not retrieve regions.")
        except Exception as e:
            print(f"An error occurred: {e}")
        return

    print(f"Fetching outages for region: {args.region}...")
    try:
        if args.address:
            print(f"Filtering for address: {args.address}")
            outages = await client.get_outages_for_address(args.address, args.region)
        else:
            outages = await client.get_outages_for_region(args.region)

        if not outages:
            print("No outages found for the specified criteria.")
            return

        print(f"\nFound {len(outages)} outage notice(s):")
        for outage in outages:
            print("-" * 40)
            print(f"  Obszar: {outage.region}")
            print(f"  Opis: {outage.description}")
            print(f"  Przewidywany koniec: {outage.end_time.strftime('%Y-%m-%d %H:%M')}")
        print("-" * 40)

    except Exception as e:
        print(f"An error occurred: {e}")


def main():
    """Synchronous wrapper for the async main function."""
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")


if __name__ == "__main__":
    main()
