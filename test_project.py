import unittest
from unittest.mock import patch, MagicMock
import tkinter as tk
from tkinter import TclError
from datetime import datetime, timedelta
import requests
from project import CurrencyApp

class TestCurrencyApp(unittest.TestCase):
    def setUp(self):
        """Inicjalizacja przed każdym testem."""
        self.root = tk.Tk()
        self.app = CurrencyApp(self.root)
        # Przygotowanie przykładowych danych
        self.currency = "USD"
        self.source = "NBP"
        self.start_date = "2025-06-01"
        self.end_date = "2025-06-05"
        self.current_date = datetime.now().strftime("%Y-%m-%d")
        self.previous_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    def tearDown(self):
        """Sprzątanie po każdym teście."""
        try:
            if self.root.winfo_exists():
                self.root.quit()
                self.root.update()
                self.root.destroy()
        except (TclError, RuntimeError):
            pass

    @patch('requests.get')
    def test_get_nbp_rates_success_archival(self, mock_get):
        """Test pobierania danych NBP dla trybu archiwalnego (sukces)."""
        # Mock odpowiedzi API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "table": "A",
            "currency": "USD",
            "rates": [
                {"effectiveDate": "2025-06-01", "mid": 3.9500},
                {"effectiveDate": "2025-06-02", "mid": 3.9600}
            ]
        }
        mock_get.return_value = mock_response

        # Wywołanie metody
        data, error, effective_date = self.app.get_nbp_rates(self.currency, "A", self.start_date, self.end_date)

        # Weryfikacja
        self.assertIsNone(error)
        self.assertIsNone(effective_date)  # Brak cofania dla trybu archiwalnego
        self.assertEqual(data["rates"][0]["mid"], 3.9500)
        mock_get.assert_called_once_with(
            f"https://api.nbp.pl/api/exchangerates/rates/A/USD/2025-06-01/2025-06-05/?format=json"
        )

    @patch('requests.get')
    def test_get_nbp_rates_current_skips_today(self, mock_get):
        """Test pomijania bieżącego dnia i pobierania danych z poprzedniego dnia."""
        # Mock odpowiedzi API dla poprzedniego dnia
        mock_response = MagicMock(status_code=200, json=lambda: {
            "table": "A",
            "currency": "USD",
            "rates": [{"effectiveDate": self.previous_date, "mid": 3.9400}]
        })
        mock_get.return_value = mock_response

        # Wywołanie metody
        data, error, effective_date = self.app.get_nbp_rates(self.currency, "A")

        # Weryfikacja
        self.assertIsNone(error)
        self.assertEqual(effective_date, self.previous_date)
        self.assertEqual(data["rates"][0]["mid"], 3.9400)
        mock_get.assert_called_once_with(
            f"https://api.nbp.pl/api/exchangerates/rates/A/USD/{self.previous_date}/?format=json"
        )

    @patch('requests.get')
    def test_get_nbp_rates_current_retry_further(self, mock_get):
        """Test cofania do wcześniejszego dnia, gdy poprzedni dzień niedostępny."""
        # Mock odpowiedzi: 404 dla poprzedniego dnia, sukces dla dwa dni wstecz
        previous_date_2 = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
        mock_response_404 = MagicMock(status_code=404)
        mock_response_success = MagicMock(status_code=200, json=lambda: {
            "table": "A",
            "currency": "USD",
            "rates": [{"effectiveDate": previous_date_2, "mid": 3.9300}]
        })
        mock_get.side_effect = [mock_response_404, mock_response_success]

        # Wywołanie metody
        data, error, effective_date = self.app.get_nbp_rates(self.currency, "A")

        # Weryfikacja
        self.assertIsNone(error)
        self.assertEqual(effective_date, previous_date_2)
        self.assertEqual(data["rates"][0]["mid"], 3.9300)
        self.assertEqual(mock_get.call_count, 2)
        mock_get.assert_called_with(
            f"https://api.nbp.pl/api/exchangerates/rates/A/USD/{previous_date_2}/?format=json"
        )

    @patch('requests.get')
    def test_get_nbp_rates_404_after_retries(self, mock_get):
        """Test braku danych po 5 próbach cofania."""
        # Mock 404 dla wszystkich prób
        mock_response = MagicMock(status_code=404)
        mock_get.return_value = mock_response

        # Wywołanie metody
        data, error, effective_date = self.app.get_nbp_rates(self.currency, "A")

        # Weryfikacja
        self.assertIsNone(data)
        self.assertIsNone(effective_date)
        self.assertEqual(error, "Brak danych dla podanego zakresu lub waluty (po 5 prób).")
        self.assertEqual(mock_get.call_count, 5)  # Próbuje od dnia -1 do -5

    @patch('requests.get')
    def test_get_nbp_rates_network_error(self, mock_get):
        """Test pobierania danych NBP przy błędzie sieciowym."""
        # Mock wyjątku sieciowego
        mock_get.side_effect = requests.RequestException("Błąd sieci")

        # Wywołanie metody
        data, error, effective_date = self.app.get_nbp_rates(self.currency, "A")

        # Weryfikacja
        self.assertIsNone(data)
        self.assertIsNone(effective_date)
        self.assertTrue(error.startswith("Błąd podczas pobierania danych z NBP:"))
        mock_get.assert_called_once()

    @patch('requests.get')
    def test_get_ecb_rates_success(self, mock_get):
        """Test pobierania danych EBC (frankfurter.app) dla trybu archiwalnego (sukces)."""
        # Mock odpowiedzi API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "rates": {
                "2025-06-01": {"USD": 1.0800},
                "2025-06-02": {"USD": 1.0850}
            }
        }
        mock_get.return_value = mock_response

        # Wywołanie metody
        data, error = self.app.get_ecb_rates(self.currency, self.start_date, self.end_date)

        # Weryfikacja
        self.assertIsNone(error)
        self.assertEqual(data["rates"]["2025-06-01"]["USD"], 1.0800)
        mock_get.assert_called_once_with(
            f"https://api.frankfurter.app/2025-06-01..2025-06-05?to=USD"
        )

    @patch('requests.get')
    def test_get_ecb_rates_fallback_success(self, mock_get):
        """Test pobierania danych EBC z zapasowego API (exchangerate.host) po błędzie."""
        # Mock błędu dla frankfurter.app
        mock_get.side_effect = [
            requests.RequestException("Błąd frankfurter"),
            MagicMock(status_code=200, json=lambda: {
                "rates": {
                    "2025-06-01": {"USD": 1.0800},
                    "2025-06-02": {"USD": 1.0850}
                }
            })
        ]

        # Wywołanie metody
        data, error = self.app.get_ecb_rates(self.currency, self.start_date, self.end_date)

        # Weryfikacja
        self.assertIsNone(error)
        self.assertEqual(data["rates"]["2025-06-01"]["USD"], 1.0800)
        mock_get.assert_called_with(
            f"https://api.exchangerate.host/timeseries?start_date=2025-06-01&end_date=2025-06-05&base=EUR&symbols=USD"
        )

    @patch('requests.get')
    def test_get_ecb_rates_both_fail(self, mock_get):
        """Test pobierania danych EBC przy błędzie obu API."""
        # Mock błędów dla obu API
        mock_get.side_effect = [
            requests.RequestException("Błąd frankfurter"),
            requests.RequestException("Błąd exchangerate")
        ]

        # Wywołanie metody
        data, error = self.app.get_ecb_rates(self.currency)

        # Weryfikacja
        self.assertIsNone(data)
        self.assertTrue(error.startswith("Błąd podczas pobierania danych z EBC:"))
        self.assertEqual(mock_get.call_count, 2)

    @patch('requests.get')
    def test_display_rates_nbp_success_current(self, mock_get):
        """Test wyświetlania kursów NBP w polu tekstowym dla danych bieżących (poprzedni dzień)."""
        # Mock odpowiedzi API dla tabel A i C (poprzedni dzień)
        mock_response_a = MagicMock(status_code=200, json=lambda: {
            "table": "A",
            "currency": "USD",
            "rates": [{"effectiveDate": self.previous_date, "mid": 3.9400}]
        })
        mock_response_c = MagicMock(status_code=200, json=lambda: {
            "table": "C",
            "currency": "USD",
            "rates": [{"effectiveDate": self.previous_date, "bid": 3.9100, "ask": 3.9700}]
        })
        mock_get.side_effect = [mock_response_a, mock_response_c]

        # Wywołanie metody
        self.app.display_rates(self.currency, "NBP")

        # Weryfikacja zawartości pola tekstowego
        text_content = self.app.result_text.get(1.0, tk.END).strip()
        expected = (
            f"Kursy dla waluty USD (źródło: NBP)\n\n"
            f"NBP Tabela A (kurs średni):\n"
            f"Data: {self.previous_date}, Kurs średni: 3.94 PLN\n"
            f"Uwaga: Pobrano kurs z {self.previous_date} zamiast bieżącego dnia.\n"
            f"\n"
            f"NBP Tabela C (kursy kupna/sprzedaży):\n"
            f"Data: {self.previous_date}, Kupno: 3.91 PLN, Sprzedaż: 3.97 PLN\n"
            f"Uwaga: Pobrano kurs z {self.previous_date} zamiast bieżącego dnia."
        )
        self.assertEqual(text_content, expected)

    @patch('requests.get')
    def test_display_rates_nbp_success_archival(self, mock_get):
        """Test wyświetlania kursów NBP w polu tekstowym dla danych archiwalnych (sukces)."""
        # Mock odpowiedzi API dla tabel A i C
        mock_response_a = MagicMock(status_code=200, json=lambda: {
            "table": "A",
            "currency": "USD",
            "rates": [{"effectiveDate": "2025-06-01", "mid": 3.9500}]
        })
        mock_response_c = MagicMock(status_code=200, json=lambda: {
            "table": "C",
            "currency": "USD",
            "rates": [{"effectiveDate": "2025-06-01", "bid": 3.9200, "ask": 3.9800}]
        })
        mock_get.side_effect = [mock_response_a, mock_response_c]

        # Wywołanie metody
        self.app.display_rates(self.currency, "NBP", self.start_date, self.end_date)

        # Weryfikacja zawartości pola tekstowego
        text_content = self.app.result_text.get(1.0, tk.END).strip()
        expected = (
            f"Kursy dla waluty USD (źródło: NBP)\n\n"
            f"NBP Tabela A (kurs średni):\n"
            f"Data: 2025-06-01, Kurs średni: 3.95 PLN\n"
            f"\n"
            f"NBP Tabela C (kursy kupna/sprzedaży):\n"
            f"Data: 2025-06-01, Kupno: 3.92 PLN, Sprzedaż: 3.98 PLN"
        )
        self.assertEqual(text_content, expected)

    @patch('requests.get')
    def test_display_rates_ecb_success(self, mock_get):
        """Test wyświetlania kursów EBC w polu tekstowym dla danych archiwalnych (sukces)."""
        # Mock odpowiedzi API
        mock_response = MagicMock(status_code=200, json=lambda: {
            "rates": {"2025-06-01": {"USD": 1.0800}}
        })
        mock_get.return_value = mock_response

        # Wywołanie metody
        self.app.display_rates(self.currency, "EBC", self.start_date, self.end_date)

        # Weryfikacja zawartości pola tekstowego
        text_content = self.app.result_text.get(1.0, tk.END).strip()
        expected = (
            f"Kursy dla waluty USD (źródło: EBC)\n\n"
            f"EBC (kurs względem EUR):\n"
            f"Data: 2025-06-01, Kurs: 1.08 EUR"
        )
        self.assertEqual(text_content, expected)

    @patch('requests.get')
    def test_plot_rates_nbp_success(self, mock_get):
        """Test rysowania wykresu dla danych archiwalnych NBP (sukces)."""
        # Mock odpowiedzi API
        mock_response = MagicMock(status_code=200, json=lambda: {
            "rates": [
                {"effectiveDate": "2025-06-01", "mid": 3.9500},
                {"effectiveDate": "2025-06-02", "mid": 3.9600}
            ]
        })
        mock_get.return_value = mock_response

        # Mock canvas.draw
        with patch.object(self.app.canvas, 'draw') as mock_draw:
            # Wywołanie metody
            self.app.plot_rates(self.currency, "NBP", self.start_date, self.end_date)
            self.root.update()  # Aktualizuj GUI przed sprawdzeniem

            # Weryfikacja
            self.assertEqual(self.app.ax.get_title(), "Kurs średni waluty USD (NBP)")
            self.assertTrue(mock_draw.called)
            self.assertTrue(self.app.canvas_widget.winfo_ismapped())  # Wykres widoczny

    @patch('requests.get')
    def test_plot_rates_nbp_error(self, mock_get):
        """Test rysowania wykresu dla danych NBP przy błędzie."""
        # Mock błędu API
        mock_response = MagicMock(status_code=404)
        mock_get.return_value = mock_response

        # Mock canvas.draw
        with patch.object(self.app.canvas, 'draw') as mock_draw:
            # Wywołanie metody
            self.app.plot_rates(self.currency, "NBP", self.start_date, self.end_date)
            self.root.update()  # Aktualizuj GUI przed sprawdzeniem

            # Weryfikacja
            self.assertTrue(mock_draw.called)
            self.assertTrue(self.app.canvas_widget.winfo_ismapped())
            texts = [text.get_text() for text in self.app.ax.texts]
            self.assertIn("Brak danych dla podanego zakresu lub waluty.", texts)

    def test_toggle_date_fields_show(self):
        """Test pokazywania pól dat po zaznaczeniu danych archiwalnych."""
        # Zaznacz dane archiwalne
        self.app.historical_var.set(True)
        self.app.toggle_date_fields()
        self.root.update()  # Wymagane dla Tkinter w testach

        # Weryfikacja
        self.assertTrue(self.app.date_frame.winfo_ismapped())
        self.assertFalse(self.app.canvas_widget.winfo_ismapped())

    def test_toggle_date_fields_hide(self):
        """Test ukrywania pól dat po odznaczeniu danych archiwalnych."""
        # Odznacz dane archiwalne
        self.app.historical_var.set(False)
        self.app.toggle_date_fields()
        self.root.update()

        # Weryfikacja
        self.assertFalse(self.app.date_frame.winfo_ismapped())
        self.assertFalse(self.app.canvas_widget.winfo_ismapped())

    @patch('tkinter.messagebox.showerror')
    def test_fetch_rates_invalid_currency(self, mock_showerror):
        """Test walidacji nieprawidłowej waluty."""
        # Ustaw nieprawidłową walutę
        self.app.currency_var.set("")
        self.app.source_var.set("NBP")

        # Wywołanie metody
        self.app.fetch_rates()

        # Weryfikacja
        mock_showerror.assert_called_with("Błąd", "Wybierz poprawną walutę!")

    @patch('tkinter.messagebox.showerror')
    def test_fetch_rates_invalid_date_format(self, mock_showerror):
        """Test walidacji nieprawidłowego formatu daty w fetch_rates."""
        # Ustaw dane archiwalne z błędnym formatem daty
        self.app.historical_var.set(True)
        self.app.currency_var.set("USD")
        self.app.source_var.set("NBP")
        self.app.start_date_entry.delete(0, tk.END)
        self.app.start_date_entry.insert(0, "2025-06-abc")
        self.app.end_date_entry.delete(0, tk.END)
        self.app.end_date_entry.insert(0, "2025-06-05")

        # Wywołanie metody
        self.app.fetch_rates()

        # Weryfikacja
        mock_showerror.assert_called_with("Błąd", "Nieprawidłowy format daty. Użyj RRRR-MM-DD!")

    @patch('requests.get')
    @patch('tkinter.messagebox.showerror')
    def test_fetch_rates_success(self, mock_showerror, mock_get):
        """Test poprawnego pobierania kursów w fetch_rates dla danych archiwalnych."""
        # Mock dla NBP (tabela A, tabela C, plot_rates)
        mock_response_a = MagicMock(status_code=200, json=lambda: {
            "rates": [{"effectiveDate": "2025-06-01", "mid": 3.9500}]
        })
        mock_response_c = MagicMock(status_code=200, json=lambda: {
            "rates": [{"effectiveDate": "2025-06-01", "bid": 3.9200, "ask": 3.9800}]
        })
        mock_response_plot = MagicMock(status_code=200, json=lambda: {
            "rates": [{"effectiveDate": "2025-06-01", "mid": 3.9500}]
        })
        mock_get.side_effect = [mock_response_a, mock_response_c, mock_response_plot]

        # Ustaw poprawne dane
        self.app.historical_var.set(True)
        self.app.currency_var.set("USD")
        self.app.source_var.set("NBP")
        self.app.start_date_entry.delete(0, tk.END)
        self.app.start_date_entry.insert(0, "2025-06-01")
        self.app.end_date_entry.delete(0, tk.END)
        self.app.end_date_entry.insert(0, "2025-06-05")

        # Mock canvas.draw
        with patch.object(self.app.canvas, 'draw'):
            # Wywołanie
            self.app.fetch_rates()
            self.root.update()  # Aktualizuj GUI przed sprawdzeniem

        # Weryfikacja
        self.assertFalse(mock_showerror.called)
        text_content = self.app.result_text.get(1.0, tk.END).strip()
        self.assertIn("Kurs średni: 3.95 PLN", text_content)
        self.assertTrue(self.app.canvas_widget.winfo_ismapped())

if __name__ == "__main__":
    unittest.main()