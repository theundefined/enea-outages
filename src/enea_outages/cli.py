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
        "--list-departments",
        action="store_true",
        help="List all available departments (oddziały) and exit.",
    )
    parser.add_argument(
        "--list-areas",
        action="store_true",
        help="List available sub-districts (rejony) for --department and exit.",
    )
    parser.add_argument(
        "--department",
        default="Poznań",
        help="Specify the department to check for outages. Default is 'Poznań'.",
    )
    parser.add_argument(
        "--area",
        help="Specify a sub-district id or name for --department (see --list-areas).",
    )
    parser.add_argument(
        "--city",
        help="Specify a city/town ('miejscowość') to narrow the search.",
    )
    parser.add_argument(
        "--street",
        help="Specify a street ('ulica') to narrow the search.",
    )
    parser.add_argument(
        "--address",
        help="Specify a street address to filter outages. Requires --department.",
    )
    args = parser.parse_args()

    outage_type = OutageType[args.type.upper()]

    with EneaOutagesClient() as client:
        if args.list_departments:
            print("Fetching available departments...")
            try:
                departments = client.get_available_departments()
                if departments:
                    print("Available departments:")
                    for department in departments:
                        print(f"- {department}")
                else:
                    print("Could not retrieve departments.")
            except Exception as e:
                print(f"An error occurred: {e}")
            return

        if args.list_areas:
            print(f"Fetching available areas for department: {args.department}...")
            try:
                areas = client.get_available_areas(args.department)
                if areas:
                    print("Available areas:")
                    for area_id, name in areas.items():
                        print(f"- {area_id}: {name}")
                else:
                    print("Could not retrieve areas for this department.")
            except Exception as e:
                print(f"An error occurred: {e}")
            return

        area_id = None
        if args.area:
            try:
                area_id = _resolve_area_id(client, args.department, args.area)
            except ValueError as e:
                print(f"An error occurred: {e}")
                return

        print(f"Fetching {args.type} outages for department: {args.department}...")
        try:
            if args.address:
                print(f"Filtering for address: {args.address}")
                outages = client.get_outages_for_address(args.address, args.department, outage_type)
            else:
                outages = client.get_outages_for_department(
                    args.department, outage_type, area=area_id, city=args.city, street=args.street
                )

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


def _resolve_area_id(client: EneaOutagesClient, department: str, area: str) -> str:
    """Resolves an area given as either its numeric id or its display name to an id."""
    areas = client.get_available_areas(department)
    if area in areas:
        return area

    normalized = area.strip().lower()
    for area_id, name in areas.items():
        if name.lower() == normalized:
            return area_id

    raise ValueError(f"Unknown area {area!r} for department {department!r}. Known values: {areas}")


def main():
    """Main entry point for the CLI."""
    try:
        run_cli_logic()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")


if __name__ == "__main__":
    main()
