import requests
from datetime import datetime, timedelta
from tabulate import tabulate
from typing import Dict, List, Optional

class ExchangeRateClient:
    def __init__(self):
        self.nbp_base_url = "http://api.nbp.pl/api/exchangerates/rates/A"
        self.ecb_base_url = "https://api.exchangeratesapi.io/v1/latest"
        self.ecb_historical_base_url = "https://api.exchangeratesapi.io/v1"

    def get_nbp_rates(self, currency: str, date: Optional[str] = None) -> Dict:
        """Pobiera kurs waluty z API NBP dla podanej daty lub najnowszy."""
        try:
            url = f"{self.nbp_base_url}/{currency}"
            if date:
                url += f"/{date}"
            response = requests.get(url, headers={"Accept": "application/json"})
            response.raise_for_status()
            data = response.json()
            return {
                "source": "NBP",
                "currency": currency,
                "date": data["effectiveDate"],
                "rate": data["rates"][0]["mid"],
            }
        except requests.RequestException as e:
            return {"source": "NBP", "currency": currency, "error": str(e)}

    def get_ecb_rates(self, currency: str, date: Optional[str] = None) -> Dict:
        """Pobiera kurs waluty z API ECB dla podanej daty lub najnowszy."""
        try:
            params = {"access_key": "YOUR_ECB_API_KEY", "symbols": currency}
            if date:
                url = f"{self.ecb_historical_base_url}/{date}"
            else:
                url = self.ecb_base_url
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            if data.get("success", False):
                return {
                    "source": "ECB",
                    "currency": currency,
                    "date": date or datetime.now().strftime("%Y-%m-%d"),
                    "rate": data["rates"][currency],
                }
            return {"source": "ECB", "currency": currency, "error": "API error"}
        except requests.RequestException as e:
            return {"source": "ECB", "currency": currency, "error": str(e)}

class ExchangeRateApp:
    def __init__(self):
        self.client = ExchangeRateClient()
        self.available_sources = ["NBP", "ECB", "ALL"]

    def validate_currency(self, currency: str, source: str) -> bool:
        """Weryfikuje, czy waluta jest obsługiwana przez dane źródło."""
        valid_currencies = {
            "NBP": ["USD", "EUR", "GBP", "CHF"],
            "ECB": ["USD", "EUR", "GBP", "CHF", "JPY"],
        }
        return currency in valid_currencies.get(source, [])

    def get_rates(self, currency: str, sources: List[str], date: Optional[str] = None) -> List[Dict]:
        """Pobiera kursy waluty z wybranych źródeł."""
        results = []
        if "ALL" in sources:
            sources = ["NBP", "ECB"]

        for source in sources:
            if not self.validate_currency(currency, source):
                results.append({"source": source, "currency": currency, "error": "Invalid currency"})
                continue
            if source == "NBP":
                results.append(self.client.get_nbp_rates(currency, date))
            elif source == "ECB":
                results.append(self.client.get_ecb_rates(currency, date))
        return results

    def display_rates(self, results: List[Dict]):
        """Wyświetla wyniki w formacie tabeli."""
        table = []
        for result in results:
            row = [
                result["source"],
                result["currency"],
                result.get("date", "-"),
                result.get("rate", "-"),
                result.get("error", "-"),
            ]
            table.append(row)
        headers = ["Source", "Currency", "Date", "Rate", "Error"]
        print(tabulate(table, headers, tablefmt="grid"))

    def run(self):
        """Główna pętla aplikacji."""
        while True:
            print("\n=== Aplikacja kursów walut ===")
            print("Dostępne źródła: NBP, ECB, ALL")
            print("Dostępne waluty: USD, EUR, GBP, CHF (ECB obsługuje także JPY)")
            currency = input("Podaj walutę (np. USD): ").upper()
            sources = input("Podaj źródła (np. NBP, ECB, ALL, oddzielone przecinkami): ").upper().split(",")
            sources = [s.strip() for s in sources]
            use_historical = input("Czy pobrać dane archiwalne? (tak/nie): ").lower() == "tak"

            date = None
            if use_historical:
                date = input("Podaj datę (RRRR-MM-DD, np. 2023-10-01): ")
                try:
                    datetime.strptime(date, "%Y-%m-%d")
                except ValueError:
                    print("Nieprawidłowy format daty!")
                    continue

            if not currency or not sources:
                print("Podaj walutę i źródła!")
                continue

            results = self.get_rates(currency, sources, date)
            self.display_rates(results)

            if input("Czy chcesz kontynuować? (tak/nie): ").lower() != "tak":
                break

if __name__ == "__main__":
    app = ExchangeRateApp()
    app.run()