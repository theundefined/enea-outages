import argparse

from .client import EneaOutagesClient
from .models import OutageType


def run_cli_logic():
    """Main function to handle CLI logic."""
    parser = argparse.ArgumentParser(description="Enea Outages CLI Tool")
    parser.add_argument(
        "--type",
        choices=[t.name.lower() for t in OutageType],
        default=OutageType.UNPLANNED.name.lower(),
        help="Specify the type of outage to fetch. Default is 'unplanned'.",
    )
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

    outage_type = OutageType[args.type.upper()]
    client = EneaOutagesClient()

    if args.list_regions:
        print("Fetching available regions...")
        try:
            regions = client.get_available_regions()
            if regions:
                print("Available regions:")
                for region in regions:
                    print(f"- {region}")
            else:
                print("Could not retrieve regions.")
        except Exception as e:
            print(f"An error occurred: {e}")
        return

    print(f"Fetching {args.type} outages for region: {args.region}...")
    try:
        if args.address:
            print(f"Filtering for address: {args.address}")
            outages = client.get_outages_for_address(args.address, args.region, outage_type)
        else:
            outages = client.get_outages_for_region(args.region, outage_type)

        if not outages:
            print("No outages found for the specified criteria.")
            return

        print(f"\nFound {len(outages)} outage notice(s):")
        for outage in outages:
            print("-" * 40)
            print(f"  Obszar: {outage.region}")
            print(f"  Opis: {outage.description}")
            if outage.start_time:
                print(f"  Początek: {outage.start_time.strftime('%Y-%m-%d %H:%M')}")
            if outage.end_time:
                print(f"  Koniec:   {outage.end_time.strftime('%Y-%m-%d %H:%M')}")
        print("-" * 40)

    except Exception as e:
        print(f"An error occurred: {e}")


def main():
    """Main entry point for the CLI."""
    try:
        run_cli_logic()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")


if __name__ == "__main__":
    main()
