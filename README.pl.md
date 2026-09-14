# Enea Outages - Biblioteka Python

Prosta biblioteka Python do pobierania informacji o przerwach w dostawie prądu ze strony Enea Operator.

## Instalacja

```bash
pip install enea-outages
```

## Użycie (Python)

```python
from enea_outages.client import EneaOutagesClient
from enea_outages.models import OutageType

# Inicjalizacja klienta synchronicznego
client = EneaOutagesClient()

# Pobierz listę dostępnych oddziałów
departments = client.get_available_departments()
print(f"Dostępne oddziały: {departments}")

# Pobierz wszystkie planowane wyłączenia dla oddziału "Poznań"
planned_outages = client.get_outages_for_department("Poznań", outage_type=OutageType.PLANNED)
print(f"Znaleziono {len(planned_outages)} planowanych wyłączeń w Poznaniu.")

# Zawęź wyszukiwanie do rejonu (id podrejonu), miejscowości i/lub ulicy
narrowed_outages = client.get_outages_for_department(
    "Poznań",
    outage_type=OutageType.PLANNED,
    area="12",  # Opalenica
    city="Komorniki",
    street="Kwiatowa",
)
print(f"Znaleziono {len(narrowed_outages)} planowanych wyłączeń dla podanej lokalizacji.")

# Pobierz wszystkie nieplanowane wyłączenia dla konkretnego adresu w "Szczecinie"
unplanned_outages = client.get_outages_for_address(
    address="Wojska Polskiego",
    department="Szczecin",
    outage_type=OutageType.UNPLANNED
)
print(f"Znaleziono {len(unplanned_outages)} nieplanowanych wyłączeń dla podanego adresu.")

if unplanned_outages:
    outage = unplanned_outages[0]
    print(
        f"Przykład -> Obszar: {outage.region}, "
        f"Opis: {outage.description}, "
        f"Czas zakończenia: {outage.end_time}"
    )
```

## Użycie (CLI)

Biblioteka udostępnia również interfejs wiersza poleceń (CLI) do szybkiego sprawdzania.

```bash
# Wyświetl wszystkie dostępne oddziały
enea-outages --list-departments

# Pobierz nieplanowane wyłączenia dla konkretnego oddziału
enea-outages --department "Poznań" --type unplanned

# Pobierz planowane wyłączenia dla konkretnego adresu w oddziale
enea-outages --department "Szczecin" --address "Wojska Polskiego" --type planned
```

---

*Ten projekt został stworzony z pomocą narzędzi AI (Google Gemini). Mimo że kod został zweryfikowany, prosimy o używanie go ze standardową ostrożnością.*
