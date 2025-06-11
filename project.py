import requests
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
from matplotlib.figure import Figure

class CurrencyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Kursy Walut")
        self.root.geometry("1000x700")
        
        # Dostępne waluty (na podstawie API NBP i EBC)
        self.currencies = ["USD", "EUR", "GBP", "CHF", "JPY", "AUD", "CAD"]
        self.sources = ["NBP", "EBC"]
        
        # Domyślne daty
        self.default_end_date = datetime.now().strftime("%Y-%m-%d")
        self.default_start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        # GUI Elements
        self.create_widgets()
        
        # Matplotlib Figure
        self.figure = Figure(figsize=(6, 4), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.root)
        self.canvas_widget = self.canvas.get_tk_widget()
        # Domyślnie wykres ukryty
        self.canvas_widget.pack_forget()
    
    def create_widgets(self):
        # Ramka na wybór waluty, źródła i danych archiwalnych
        self.input_frame = tk.Frame(self.root)
        self.input_frame.pack(pady=10, padx=10, fill=tk.X)
        
        # Waluta
        tk.Label(self.input_frame, text="Wybierz walutę:", font=("Arial", 12)).pack(anchor="w")
        self.currency_var = tk.StringVar()
        self.currency_combobox = ttk.Combobox(self.input_frame, values=self.currencies, textvariable=self.currency_var, font=("Arial", 10))
        self.currency_combobox.pack(fill=tk.X, pady=5)
        self.currency_combobox.set(self.currencies[0])
        
        # Źródło danych
        tk.Label(self.input_frame, text="Wybierz źródło danych:", font=("Arial", 12)).pack(anchor="w")
        self.source_var = tk.StringVar()
        self.source_combobox = ttk.Combobox(self.input_frame, values=self.sources, textvariable=self.source_var, font=("Arial", 10))
        self.source_combobox.pack(fill=tk.X, pady=5)
        self.source_combobox.set(self.sources[0])
        
        # Dane archiwalne
        self.historical_var = tk.BooleanVar()
        self.historical_check = tk.Checkbutton(self.input_frame, text="Pobierz dane archiwalne", variable=self.historical_var, command=self.toggle_date_fields, font=("Arial", 12))
        self.historical_check.pack(anchor="w", pady=10)
        
        # Ramka na pola dat
        self.date_frame = tk.Frame(self.input_frame)
        # Data początkowa
        tk.Label(self.date_frame, text="Data początkowa (RRRR-MM-DD):", font=("Arial", 12)).pack(anchor="w")
        self.start_date_entry = tk.Entry(self.date_frame, font=("Arial", 10))
        self.start_date_entry.insert(0, self.default_start_date)
        self.start_date_entry.pack(fill=tk.X, pady=5)
        
        # Data końcowa
        tk.Label(self.date_frame, text="Data końcowa (RRRR-MM-DD):", font=("Arial", 12)).pack(anchor="w")
        self.end_date_entry = tk.Entry(self.date_frame, font=("Arial", 10))
        self.end_date_entry.insert(0, self.default_end_date)
        self.end_date_entry.pack(fill=tk.X, pady=5)
        
        # Ukryj pola dat na początku
        self.date_frame.pack_forget()
        
        # Przyciski
        self.button_frame = tk.Frame(self.root)
        self.button_frame.pack(pady=10)
        tk.Button(self.button_frame, text="Pobierz kursy", command=self.fetch_rates, font=("Arial", 12), bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(self.button_frame, text="Wyczyść wyniki", command=self.clear_results, font=("Arial", 12), bg="#f44336", fg="white").pack(side=tk.LEFT, padx=5)
        
        # Obszar wyników tekstowych
        tk.Label(self.root, text="Wyniki:", font=("Arial", 12)).pack(anchor="w", padx=10)
        self.result_text = tk.Text(self.root, height=5, width=70, font=("Arial", 10))
        self.result_text.pack(pady=10, padx=10)
    
    def toggle_date_fields(self):
        """Pokazuje/ukrywa pola dat i wykres w zależności od wyboru danych archiwalnych."""
        if self.historical_var.get():
            self.date_frame.pack(pady=5, fill=tk.X)
        else:
            self.date_frame.pack_forget()
            self.canvas_widget.pack_forget()
    
    def get_nbp_rates(self, currency, table, start_date=None, end_date=None, retry_days=0):
        """Pobiera kursy walut z API NBP dla podanej waluty, tabeli (A lub C) i zakresu dat."""
        try:
            if start_date and end_date:
                url = f"https://api.nbp.pl/api/exchangerates/rates/{table}/{currency}/{start_date}/{end_date}/?format=json"
            else:
                # Zawsze zaczynaj od poprzedniego dnia w trybie aktualnym
                retry_days = max(1, retry_days)
                current_date = (datetime.now() - timedelta(days=retry_days)).strftime("%Y-%m-%d")
                url = f"https://api.nbp.pl/api/exchangerates/rates/{table}/{currency}/{current_date}/?format=json"
            
            response = requests.get(url)
            if response.status_code == 404:
                if not start_date and retry_days < 5:
                    return self.get_nbp_rates(currency, table, retry_days=retry_days + 1)
                error_msg = "Brak danych dla podanego zakresu lub waluty." if start_date else f"Brak danych dla podanego zakresu lub waluty (po {retry_days} prób)."
                return None, error_msg, None
            response.raise_for_status()
            data = response.json()
            effective_date = current_date if not start_date else None
            return data, None, effective_date
        except requests.RequestException as e:
            return None, f"Błąd podczas pobierania danych z NBP: {e}", None
    
    def get_ecb_rates(self, currency, start_date=None, end_date=None):
        """Pobiera kursy walut z API opartego na danych EBC (pierwszeństwo: frankfurter.app, zapasowe: exchangerate.host)."""
        try:
            base_url = "https://api.frankfurter.app"
            if start_date and end_date:
                url = f"{base_url}/{start_date}..{end_date}?to={currency}"
            else:
                url = f"{base_url}/latest?to={currency}"
            
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            return data, None
        except requests.RequestException as e:
            try:
                base_url = "https://api.exchangerate.host"
                if start_date and end_date:
                    url = f"{base_url}/timeseries?start_date={start_date}&end_date={end_date}&base=EUR&symbols={currency}"
                else:
                    url = f"{base_url}/latest?base=EUR&symbols={currency}"
                
                response = requests.get(url)
                response.raise_for_status()
                data = response.json()
                return data, None
            except requests.RequestException as e2:
                return None, f"Błąd podczas pobierania danych z EBC: {e} (frankfurter.app) i {e2} (exchangerate.host)"
    
    def plot_rates(self, currency, source, start_date, end_date):
        """Rysuje wykres kursów średnich walut dla danych archiwalnych."""
        self.ax.clear()  # Czyści poprzedni wykres
        
        dates = []
        
        if source == "NBP":
            # Pobieranie danych z NBP (tylko kurs średni)
            data_a, error_a, _ = self.get_nbp_rates(currency, "A", start_date, end_date)
            if error_a:
                self.ax.text(0.5, 0.5, error_a, ha="center", va="center")
                self.canvas.draw()
                self.canvas_widget.pack(pady=20, padx=10, fill=tk.BOTH, expand=True)
                return
            dates = [datetime.strptime(rate["effectiveDate"], "%Y-%m-%d") for rate in data_a["rates"]]
            nbp_mid = [rate["mid"] for rate in data_a["rates"]]
            if nbp_mid:
                self.ax.plot(dates, nbp_mid, label="NBP Średni (PLN)", marker="o")
        
        elif source == "EBC":
            # Pobieranie danych z EBC
            data, error = self.get_ecb_rates(currency, start_date, end_date)
            if error:
                self.ax.text(0.5, 0.5, error, ha="center", va="center")
                self.canvas.draw()
                self.canvas_widget.pack(pady=20, padx=10, fill=tk.BOTH, expand=True)
                return
            dates = [datetime.strptime(date, "%Y-%m-%d") for date in data["rates"].keys()]
            ecb_rates = [data["rates"][date][currency] for date in data["rates"].keys()]
            if ecb_rates:
                self.ax.plot(dates, ecb_rates, label="EBC (EUR)", marker="d")
        
        # Formatowanie osi
        if dates:
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
            self.ax.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=10))
            self.figure.autofmt_xdate(rotation=45)
            self.ax.set_xlabel("Data")
            self.ax.set_ylabel("Kurs")
            self.ax.set_title(f"Kurs średni waluty {currency} ({source})")
            self.ax.legend()
            self.ax.grid(True)
        else:
            self.ax.text(0.5, 0.5, "Brak danych do wyświetlenia", ha="center", va="center")
        
        self.canvas.draw()
        # Pokaz wykres poniżej pola tekstowego
        self.canvas_widget.pack(pady=20, padx=10, fill=tk.BOTH, expand=True)
    
    def display_rates(self, currency, source, start_date=None, end_date=None):
        """Wyświetla kursy walut w polu tekstowym."""
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, f"Kursy dla waluty {currency} (źródło: {source})\n\n")
        
        if source == "NBP":
            # Tabela A (kurs średni)
            data_a, error_a, effective_date = self.get_nbp_rates(currency, "A", start_date, end_date)
            if error_a:
                self.result_text.insert(tk.END, f"NBP Tabela A: {error_a}\n")
            else:
                self.result_text.insert(tk.END, "NBP Tabela A (kurs średni):\n")
                if start_date and end_date:
                    for rate in data_a["rates"]:
                        self.result_text.insert(tk.END, f"Data: {rate['effectiveDate']}, Kurs średni: {rate['mid']} PLN\n")
                else:
                    date_str = effective_date or data_a["rates"][0]["effectiveDate"]
                    self.result_text.insert(tk.END, f"Data: {date_str}, Kurs średni: {data_a['rates'][0]['mid']} PLN\n")
                    if effective_date:
                        self.result_text.insert(tk.END, f"Uwaga: Pobrano kurs z {effective_date} zamiast bieżącego dnia.\n")
            
            # Tabela C (kursy kupna i sprzedaży)
            data_c, error_c, effective_date_c = self.get_nbp_rates(currency, "C", start_date, end_date)
            if error_c:
                self.result_text.insert(tk.END, f"NBP Tabela C: {error_c}\n")
            else:
                self.result_text.insert(tk.END, "\nNBP Tabela C (kursy kupna/sprzedaży):\n")
                if start_date and end_date:
                    for rate in data_c["rates"]:
                        self.result_text.insert(tk.END, f"Data: {rate['effectiveDate']}, Kupno: {rate['bid']} PLN, Sprzedaż: {rate['ask']} PLN\n")
                else:
                    date_str = effective_date_c or data_c["rates"][0]["effectiveDate"]
                    self.result_text.insert(tk.END, f"Data: {date_str}, Kupno: {data_c['rates'][0]['bid']} PLN, Sprzedaż: {data_c['rates'][0]['ask']} PLN\n")
                    if effective_date_c:
                        self.result_text.insert(tk.END, f"Uwaga: Pobrano kurs z {effective_date_c} zamiast bieżącego dnia.\n")
        
        elif source == "EBC":
            data, error = self.get_ecb_rates(currency, start_date, end_date)
            if error:
                self.result_text.insert(tk.END, f"EBC: {error}\n")
                self.result_text.insert(tk.END, "Uwaga: API EBC może być niedostępne. Spróbuj źródła NBP lub innego zakresu dat.\n")
            else:
                self.result_text.insert(tk.END, "EBC (kurs względem EUR):\n")
                if start_date and end_date:
                    for date, rates in data["rates"].items():
                        self.result_text.insert(tk.END, f"Data: {date}, Kurs: {rates[currency]} EUR\n")
                else:
                    self.result_text.insert(tk.END, f"Data: {data['date']}, Kurs: {data['rates'][currency]} EUR\n")
    
    def fetch_rates(self):
        """Pobiera i wyświetla kursy na podstawie danych wprowadzonych przez użytkownika."""
        currency = self.currency_var.get()
        source = self.source_var.get()
        
        if not currency or currency not in self.currencies:
            messagebox.showerror("Błąd", "Wybierz poprawną walutę!")
            return
        if not source or source not in self.sources:
            messagebox.showerror("Błąd", "Wybierz poprawne źródło danych!")
            return
        
        if self.historical_var.get():
            start_date = self.start_date_entry.get()
            end_date = self.end_date_entry.get()
            if not start_date or not end_date:
                messagebox.showerror("Błąd", "Wprowadź obie daty (początkową i końcową)!")
                return
            try:
                start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
                end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
                if end_date_obj < start_date_obj:
                    messagebox.showerror("Błąd", "Data końcowa nie może być wcześniejsza niż data początkowa!")
                    return
            except ValueError:
                messagebox.showerror("Błąd", "Nieprawidłowy format daty. Użyj RRRR-MM-DD!")
                return
        else:
            start_date = end_date = None
            self.canvas_widget.pack_forget()  # Ukryj wykres dla danych aktualnych
        
        self.display_rates(currency, source, start_date, end_date)
        if self.historical_var.get():
            self.plot_rates(currency, source, start_date, end_date)
    
    def clear_results(self):
        """Czyści pole wyników i ukrywa wykres."""
        self.result_text.delete(1.0, tk.END)
        self.ax.clear()
        self.canvas_widget.pack_forget()

if __name__ == "__main__":
    root = tk.Tk()
    app = CurrencyApp(root)
    root.mainloop()