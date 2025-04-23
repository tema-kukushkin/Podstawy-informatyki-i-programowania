import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


def filter_and_group(df, date_from, date_to):
    df_filtered = df[(df["date"] >= date_from) & (df["date"] <= date_to)]
    return df_filtered.groupby("date")["value"].mean().reset_index()

# upload data
df_temp = pd.read_csv("temperatura.csv", encoding="utf-8")
df_rain = pd.read_csv("opady.csv", encoding="utf-8")

df_temp["timestamp"] = pd.to_datetime(df_temp["timestamp"])
df_temp["date"] = df_temp["timestamp"].dt.date
df_temp["value"] = df_temp["medium"]

df_rain["timestamp"] = pd.to_datetime(df_rain["timestamp"])
df_rain["date"] = df_rain["timestamp"].dt.date
df_rain["value"] = df_rain["high"]

# GUI
root = tk.Tk()
root.title("Analiza pogodowych danych")
root.geometry("1000x650")

selected_type = tk.StringVar(value="Temperatura")
start_date = tk.StringVar()
end_date = tk.StringVar()

frame_controls = tk.Frame(root)
frame_controls.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

tk.Label(frame_controls, text="Typ danych:").pack(side=tk.LEFT)
type_box = ttk.Combobox(frame_controls, textvariable=selected_type, values=["Temperatura", "Osady"], width=15)
type_box.pack(side=tk.LEFT, padx=5)

tk.Label(frame_controls, text="Od:").pack(side=tk.LEFT, padx=10)
start_entry = DateEntry(frame_controls, textvariable=start_date, date_pattern='yyyy-mm-dd', width=12)
start_entry.pack(side=tk.LEFT)

tk.Label(frame_controls, text="Do:").pack(side=tk.LEFT, padx=10)
end_entry = DateEntry(frame_controls, textvariable=end_date, date_pattern='yyyy-mm-dd', width=12)
end_entry.pack(side=tk.LEFT)

frame_plot = tk.Frame(root)
frame_plot.pack(fill=tk.BOTH, expand=True)

canvas = None

def plot_data():
    global canvas
    for widget in frame_plot.winfo_children():
        widget.destroy()

    try:
        date_from = pd.to_datetime(start_date.get()).date()
        date_to = pd.to_datetime(end_date.get()).date()
    except Exception as e:
        messagebox.showerror("Error", f"Nie prawidłowy format daty.\n{e}")
        return

    if selected_type.get() == "Temperatura":
        df = df_temp.copy()
        y_label = "Temperatura (°C)"
        filename = "srednia_temperatura"
    else:
        df = df_rain.copy()
        y_label = "Osady (mm)"
        filename = "srednie_opady"

    df_filtered = df[(df["date"] >= date_from) & (df["date"] <= date_to)]
    if df_filtered.empty:
        messagebox.showwarning("Nie ma danych", "Nie ma danych w tym zakresie.")
        return

    df_grouped = df_filtered.groupby("date")["value"].mean().reset_index()

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df_grouped["date"], df_grouped["value"], marker="o", linestyle="-", color="blue")
    ax.set_title(f"{selected_type.get()} ({date_from} — {date_to})")
    ax.set_xlabel("Data")
    ax.set_ylabel(y_label)
    ax.grid(True)
    fig.autofmt_xdate()

    canvas = FigureCanvasTkAgg(fig, master=frame_plot)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    df_grouped.to_csv(f"{filename}.csv", index=False)
    #fig.savefig(f"{filename}.png")

    messagebox.showinfo("Zrobione", f" data saved:\n- {filename}.csv")

tk.Button(frame_controls, text="Zrobić wykres", command=plot_data).pack(side=tk.LEFT, padx=20)

if __name__ == "__main__":
    root.mainloop()