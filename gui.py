# gui.py

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import pandas as pd
from calculations import (
    calculate_payment_schedule,
    calculate_payment_schedule_with_fixed_overpayment,
    calculate_payment_schedule_mix_strategy,
    calculate_monthly_rate,
    calculate_savings,
)
from schedule import generate_installment_dates
from datetime import datetime
import locale
import mplcursors

# Ustawienie lokalizacji dla formatowania walut (dopasuje się do systemu użytkownika)
locale.setlocale(locale.LC_ALL, '')

def run_gui():
    """
    Główna funkcja uruchamiająca interfejs użytkownika.
    """

    # Zmienne globalne (dla uproszczenia)
    schedule = []
    interest_changes = []

    # -------------------------- FUNKCJE POMOCNICZE -------------------------- #
    def validate_input(value, value_type):
        """
        Funkcja pomocnicza do walidacji wartości w polach tekstowych.
        value: tekst z pola Entry
        value_type: 'float' lub 'int'
        """
        try:
            if value_type == 'float':
                val = float(value)
                return val >= 0
            elif value_type == 'int':
                val = int(value)
                return val > 0
            else:
                return False
        except ValueError:
            return False

    def show_strategy_info():
        """
        Wyświetla okno dialogowe z opisami strategii spłaty.
        """
        info_text = (
            "Opis strategii spłaty:\n\n"
            "1) Bez nadpłat:\n"
            "   Spłata kredytu bez dokonywania nadpłat.\n\n"
            "2) Stała nadpłata:\n"
            "   Co miesiąc dokonywana jest stała nadpłata w kwocie\n"
            "   podanej przez użytkownika.\n\n"
            "3) Strategia mix:\n"
            "   Użytkownik podaje łączną kwotę miesięczną, jaką chce płacić.\n"
            "   Nadpłata jest różnicą między tą kwotą a aktualną ratą kredytu,\n"
            "   która zmniejsza się w wyniku nadpłat z poprzednich miesięcy."
        )
        messagebox.showinfo("Informacje o strategiach spłaty", info_text)

    def edit_interest_changes():
        """
        Okno dialogowe do edycji zmian oprocentowania.
        Pozwala dodać wiersze z (miesiąc, oprocentowanie).
        """
        interest_window = tk.Toplevel(root)
        interest_window.title("Zmiany oprocentowania")

        tk.Label(interest_window, text="Miesiąc").grid(row=0, column=0)
        tk.Label(interest_window, text="Oprocentowanie (%)").grid(row=0, column=1)

        entries = []

        def add_row():
            row = len(entries) + 1
            month_entry = tk.Entry(interest_window)
            rate_entry = tk.Entry(interest_window)
            month_entry.grid(row=row, column=0)
            rate_entry.grid(row=row, column=1)
            entries.append((month_entry, rate_entry))

        def save_changes():
            nonlocal interest_changes
            interest_changes = []
            for month_entry, rate_entry in entries:
                month = month_entry.get()
                rate = rate_entry.get()
                if validate_input(month, 'int') and validate_input(rate, 'float'):
                    interest_changes.append((int(month), float(rate)))
                else:
                    messagebox.showerror("Błąd", "Nieprawidłowe dane w zmianach oprocentowania.")
                    return

            # Jeśli nic nie podano, wstawiamy domyślne oprocentowanie
            if not interest_changes:
                interest_changes = [(1, float(entry_interest_rate.get()))]
            else:
                # Sortujemy po miesiącu i sprawdzamy, czy pierwszy wiersz to miesiąc 1
                interest_changes.sort(key=lambda x: x[0])
                if interest_changes[0][0] != 1:
                    interest_changes.insert(0, (1, float(entry_interest_rate.get())))

            interest_window.destroy()

        add_button = tk.Button(interest_window, text="Dodaj zmianę", command=add_row)
        add_button.grid(row=100, column=0)

        save_button = tk.Button(interest_window, text="Zapisz", command=save_changes)
        save_button.grid(row=100, column=1)

    def load_data():
        """
        Wczytywanie danych z pliku JSON (np. danych wejściowych).
        """
        filepath = filedialog.askopenfilename(filetypes=[('Data files', '*.json')])
        if not filepath:
            return
        try:
            data = pd.read_json(filepath)
            entry_loan_amount.delete(0, tk.END)
            entry_loan_amount.insert(0, data['loan_amount'][0])
            entry_loan_period.delete(0, tk.END)
            entry_loan_period.insert(0, data['loan_period'][0])
            entry_interest_rate.delete(0, tk.END)
            entry_interest_rate.insert(0, data['interest_rate'][0])
            entry_additional_costs.delete(0, tk.END)
            entry_additional_costs.insert(0, data['additional_costs'][0])
            currency_var.set(data['currency'][0])
            messagebox.showinfo("Sukces", f"Dane zostały wczytane z pliku {filepath}")
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się wczytać pliku:\n{e}")

    def save_data():
        """
        Zapis danych wejściowych (np. do pliku JSON).
        """
        filetypes = [('Data files', '*.json')]
        filepath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=filetypes)
        if not filepath:
            return
        data = {
            'loan_amount': [entry_loan_amount.get()],
            'loan_period': [entry_loan_period.get()],
            'interest_rate': [entry_interest_rate.get()],
            'additional_costs': [entry_additional_costs.get()],
            'currency': [currency_var.get()],
        }
        df = pd.DataFrame(data)
        try:
            df.to_json(filepath, orient='records')
            messagebox.showinfo("Sukces", f"Dane zostały zapisane do pliku {filepath}")
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się zapisać pliku:\n{e}")

    def save_schedule():
        """
        Zapis harmonogramu do pliku Excel (xlsx) lub CSV.
        """
        if not schedule:
            messagebox.showerror("Błąd", "Brak harmonogramu do zapisania.")
            return
        filetypes = [('Excel files', '*.xlsx'), ('CSV files', '*.csv')]
        filepath = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=filetypes)
        if not filepath:
            return

        df = pd.DataFrame(schedule)
        df['Data'] = [inst['date'] for inst in schedule]

        # Przeniesienie kolumny 'Data' na drugą pozycję
        cols = df.columns.tolist()
        cols.insert(1, cols.pop(cols.index('Data')))
        df = df[cols]

        # Zmiana nazw kolumn na bardziej czytelne
        df.rename(columns={
            'installment_number': 'Nr raty',
            'date': 'Data',
            'interest_rate': 'Oprocentowanie (%)',
            'current_debt': 'Pozostało do spłaty',
            'installment_amount': 'Wysokość raty',
            'capital_payment': 'Spłata kapitału',
            'interest_payment': 'Odsetki',
            'overpayment': 'Nadpłata',
            'remaining_capital': 'Kapitał pozostały',
        }, inplace=True)

        # Ustawienie kolejności kolumn
        df = df[['Nr raty', 'Data', 'Oprocentowanie (%)',
                 'Pozostało do spłaty', 'Wysokość raty', 'Spłata kapitału',
                 'Odsetki', 'Nadpłata', 'Kapitał pozostały']]

        try:
            if filepath.endswith('.xlsx'):
                df.to_excel(filepath, index=False)
            else:
                df.to_csv(filepath, index=False)
            messagebox.showinfo("Sukces", f"Harmonogram został zapisany do pliku {filepath}")
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się zapisać pliku:\n{e}")

    def update_fixed_payment_suggestion(event=None):
        """
        Aktualizuje pole z sugerowaną ratą standardową (bez nadpłat)
        po zmianie któregoś z pól kwota/okres/oprocentowanie.
        """
        try:
            loan_amount = float(entry_loan_amount.get())
            loan_period_months = int(entry_loan_period.get())
            annual_interest_rate = float(entry_interest_rate.get())

            standard_monthly_rate = calculate_monthly_rate(
                loan_amount, annual_interest_rate, loan_period_months
            )
            label_standard_rate.config(text="Standardowa rata:")

            entry_standard_rate.config(state='normal')
            entry_standard_rate.delete(0, tk.END)
            entry_standard_rate.insert(0, f"{standard_monthly_rate:.2f}")
            entry_standard_rate.config(state='readonly')

            # Jeśli wybrano "Strategia mix", można zasugerować kwotę = standardowej racie
            strategy = strategy_var.get()
            if strategy == "Strategia mix":
                entry_fixed_overpayment.delete(0, tk.END)
                entry_fixed_overpayment.insert(0, f"{standard_monthly_rate:.2f}")

        except ValueError:
            pass  # Jeśli dane nie są kompletne, pomijamy

    def on_strategy_change(event=None):
        """
        Reakcja na zmianę strategii spłaty w comboboxie.
        """
        strategy = strategy_var.get()
        if strategy == "Strategia mix":
            try:
                loan_amount = float(entry_loan_amount.get())
                loan_period_months = int(entry_loan_period.get())
                annual_interest_rate = float(entry_interest_rate.get())

                standard_monthly_rate = calculate_monthly_rate(
                    loan_amount, annual_interest_rate, loan_period_months
                )
                entry_fixed_overpayment.delete(0, tk.END)
                entry_fixed_overpayment.insert(0, f"{standard_monthly_rate:.2f}")
            except ValueError:
                pass
        else:
            # W innych strategiach wyczyść pole nadpłaty
            entry_fixed_overpayment.delete(0, tk.END)

    def calculate():
        """
        Wywołuje odpowiednią funkcję obliczeniową w zależności od wybranej strategii
        i aktualizuje tabelę z harmonogramem.
        """
        nonlocal schedule, interest_changes
        try:
            loan_amount = float(entry_loan_amount.get())
            loan_period_months = int(entry_loan_period.get())
            annual_interest_rate = float(entry_interest_rate.get())
            additional_costs = float(entry_additional_costs.get()) if entry_additional_costs.get() else 0.0
            user_amount = entry_fixed_overpayment.get()
            if user_amount:
                user_amount = float(user_amount)
            else:
                user_amount = 0.0
        except ValueError:
            messagebox.showerror("Błąd", "Proszę wprowadzić prawidłowe dane.")
            return

        if loan_amount <= 0 or loan_period_months <= 0 or annual_interest_rate < 0 or additional_costs < 0:
            messagebox.showerror("Błąd", "Proszę wprowadzić prawidłowe wartości.")
            return

        strategy = strategy_var.get()

        # Ustawienie zmian oprocentowania
        if not interest_changes:
            interest_changes.append((1, annual_interest_rate))
        else:
            if interest_changes[0][0] != 1:
                interest_changes.insert(0, (1, annual_interest_rate))

        # Obliczenie harmonogramu
        if strategy == "Bez nadpłat":
            schedule = calculate_payment_schedule(
                loan_amount, interest_changes, loan_period_months, additional_costs
            )
            original_schedule = schedule  # brak nadpłat => ten sam harmonogram
        elif strategy == "Stała nadpłata":
            if user_amount <= 0:
                messagebox.showerror("Błąd", "Proszę wprowadzić prawidłową kwotę nadpłaty.")
                return
            schedule = calculate_payment_schedule_with_fixed_overpayment(
                loan_amount, interest_changes, loan_period_months, user_amount, additional_costs
            )
            # Oryginalny harmonogram bez nadpłat
            original_schedule = calculate_payment_schedule(
                loan_amount, interest_changes, loan_period_months, additional_costs
            )
        elif strategy == "Strategia mix":
            if user_amount <= 0:
                messagebox.showerror("Błąd", "Proszę wprowadzić prawidłową kwotę miesięczną.")
                return
            try:
                schedule = calculate_payment_schedule_mix_strategy(
                    loan_amount, interest_changes, loan_period_months, user_amount, additional_costs
                )
                original_schedule = calculate_payment_schedule(
                    loan_amount, interest_changes, loan_period_months, additional_costs
                )
            except ValueError as e:
                messagebox.showerror("Błąd", str(e))
                return
        else:
            messagebox.showerror("Błąd", "Nieznana strategia spłaty.")
            return

        # Generowanie dat rat
        installment_dates = generate_installment_dates(datetime.today(), len(schedule))

        # Dodanie dat do harmonogramu
        for i, installment in enumerate(schedule):
            installment['date'] = installment_dates[i]

        # Obliczanie oszczędności (jeśli dotyczy)
        if strategy != "Bez nadpłat":
            savings = calculate_savings(original_schedule, schedule)
        else:
            savings = None

        # Czyszczenie tabeli Treeview
        for row in tree.get_children():
            tree.delete(row)

        # Wypełnianie tabeli danymi
        for installment in schedule:
            total_capital = installment['capital_payment'] + installment['overpayment']
            tree.insert(
                "",
                "end",
                values=(
                    installment["installment_number"],
                    installment["date"],
                    f"{installment['interest_rate']:.2f}%",
                    f"{installment['current_debt']:.2f}",
                    f"{installment['installment_amount']:.2f}",
                    f"{total_capital:.2f}",
                    f"{installment['interest_payment']:.2f}",
                    f"{installment['overpayment']:.2f}",
                    f"{installment['remaining_capital']:.2f}",
                ),
            )

        # Czyszczenie poprzednich informacji o podsumowaniu (w summary_frame)
        for widget in summary_frame.winfo_children():
            widget.destroy()

        # Wyświetlanie oszczędności i generowanie wykresu w summary_frame (prawa część)
        if savings:
            savings_text = (
                f"Całkowite odsetki bez nadpłat: {savings['original_interest']:.2f} {currency_var.get()}\n"
                f"Całkowite odsetki z nadpłatami: {savings['overpayment_interest']:.2f} {currency_var.get()}\n"
                f"Oszczędność na odsetkach: "
            )

            label_savings_text = tk.Label(summary_frame, text=savings_text, justify="left")
            label_savings_text.pack(anchor='w')

            # Oszczędność w kolorze zielonym
            label_savings_value = tk.Label(
                summary_frame,
                text=f"{savings['interest_savings']:.2f} {currency_var.get()}",
                fg="green",
                font=("Arial", 10, "bold")
            )
            label_savings_value.pack(anchor='w')

            period_text = (
                f"Pierwotny okres kredytowania: {savings['original_period']} miesięcy\n"
                f"Skrócony okres kredytowania: {savings['overpayment_period']} miesięcy\n"
                f"Skrócenie okresu o: {savings['period_reduction']} miesięcy"
            )
            label_period = tk.Label(summary_frame, text=period_text, justify="left")
            label_period.pack(anchor='w')

            # Generowanie wykresu w summary_frame
            plot_savings_over_time(schedule, original_schedule, summary_frame)
        else:
            # Brak oszczędności => brak wykresu
            pass

    def plot_savings_over_time(schedule, original_schedule, parent_frame):
        """
        Rysuje wykres skumulowanych odsetek w czasie oraz obszar 
        symbolizujący oszczędności.
        """
        max_index = min(len(schedule), len(original_schedule))
        if max_index < 1:
            return

        overpayment_cumulative_interest = []
        cumulative_savings = []
        cumulative_original = 0
        cumulative_overpayment = 0

        for i in range(max_index):
            cumulative_overpayment += schedule[i]['interest_payment']
            overpayment_cumulative_interest.append(cumulative_overpayment)

            cumulative_original += original_schedule[i]['interest_payment']
            saving = cumulative_original - cumulative_overpayment
            cumulative_savings.append(saving)

        x_values = range(1, max_index + 1)

        fig = Figure(figsize=(5, 3), dpi=100)
        ax = fig.add_subplot(111)

        ax.plot(x_values, overpayment_cumulative_interest, label='Z nadpłatami', color='orange')
        ax.fill_between(x_values, cumulative_savings, color='green', alpha=0.3, label='Oszczędności')

        ax.set_title('Skumulowane odsetki i oszczędności w czasie')
        ax.set_xlabel('Numer raty')
        ax.set_ylabel(f'Kwota ({currency_var.get()})')
        ax.legend()

        # Interaktywne etykiety z mplcursors
        cursor = mplcursors.cursor(ax, hover=True)
        cursor.connect(
            "add",
            lambda sel: sel.annotation.set_text(
                f"Rata: {int(sel.target[0])}\nKwota: {sel.target[1]:.2f}"
            )
        )

        # Czyścimy poprzednie widgety w ramce (jeśli jakieś są)
        for widget in parent_frame.winfo_children():
            if isinstance(widget, FigureCanvasTkAgg):
                widget.get_tk_widget().destroy()

        canvas = FigureCanvasTkAgg(fig, master=parent_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)

    # -------------------------- UKŁAD GUI -------------------------- #

    # Główne okno
    root = tk.Tk()
    root.title("Kalkulator Kredytowy")

    # Ramka główna (kontener)
    main_frame = ttk.Frame(root)
    main_frame.pack(fill='both', expand=True)

    # Dzielimy okno główne na górę (top_frame) i dół (bottom_frame)
    top_frame = ttk.Frame(main_frame)
    top_frame.pack(side='top', fill='both', expand=True)

    bottom_frame = ttk.Frame(main_frame)
    bottom_frame.pack(side='bottom', fill='both', expand=True)

    # W górnej części dzielimy na lewo (left_frame) i prawo (summary_frame)
    left_frame = ttk.Frame(top_frame)
    left_frame.pack(side='left', fill='both', expand=True, padx=5, pady=5)

    summary_frame = ttk.Frame(top_frame)
    summary_frame.pack(side='right', fill='both', expand=True, padx=5, pady=5)

    # -------------- LEWA CZĘŚĆ (DANE WEJŚCIOWE) -------------- #
    frame_inputs = ttk.Frame(left_frame)
    frame_inputs.pack(padx=10, pady=10, fill='x')

    # Kwota kredytu
    tk.Label(frame_inputs, text="Kwota kredytu:").grid(row=0, column=0, sticky="e")
    entry_loan_amount = ttk.Entry(frame_inputs)
    entry_loan_amount.grid(row=0, column=1, sticky="w")
    entry_loan_amount.bind("<FocusOut>", update_fixed_payment_suggestion)

    # Okres kredytu
    tk.Label(frame_inputs, text="Okres kredytu (miesiące):").grid(row=1, column=0, sticky="e")
    entry_loan_period = ttk.Entry(frame_inputs)
    entry_loan_period.grid(row=1, column=1, sticky="w")
    entry_loan_period.bind("<FocusOut>", update_fixed_payment_suggestion)

    # Oprocentowanie roczne
    tk.Label(frame_inputs, text="Oprocentowanie roczne (%):").grid(row=2, column=0, sticky="e")
    entry_interest_rate = ttk.Entry(frame_inputs)
    entry_interest_rate.grid(row=2, column=1, sticky="w")
    entry_interest_rate.bind("<FocusOut>", update_fixed_payment_suggestion)

    # Dodatkowe koszty
    tk.Label(frame_inputs, text="Dodatkowe koszty:").grid(row=3, column=0, sticky="e")
    entry_additional_costs = ttk.Entry(frame_inputs)
    entry_additional_costs.grid(row=3, column=1, sticky="w")

    # Zmiany oprocentowania
    tk.Label(frame_inputs, text="Zmiany oprocentowania:").grid(row=4, column=0, sticky="e")
    btn_interest_changes = ttk.Button(frame_inputs, text="Ustaw", command=edit_interest_changes)
    btn_interest_changes.grid(row=4, column=1, sticky="w")

    # Waluta
    tk.Label(frame_inputs, text="Waluta:").grid(row=5, column=0, sticky="e")
    currency_var = tk.StringVar(value="PLN")
    currency_option_menu = ttk.Combobox(
        frame_inputs,
        textvariable=currency_var,
        values=["PLN", "EUR", "USD"],
        state="readonly",
    )
    currency_option_menu.grid(row=5, column=1, sticky="w")

    # Strategia spłaty -> przeniesiona nad "Kwota miesięczna / Nadpłata"
    tk.Label(frame_inputs, text="Strategia spłaty:").grid(row=6, column=0, sticky="e")
    strategy_var = tk.StringVar(value="Bez nadpłat")
    strategy_option_menu = ttk.Combobox(
        frame_inputs,
        textvariable=strategy_var,
        values=["Bez nadpłat", "Stała nadpłata", "Strategia mix"],
        state="readonly",
    )
    strategy_option_menu.grid(row=6, column=1, sticky="w")
    strategy_option_menu.bind("<<ComboboxSelected>>", on_strategy_change)

    # Przycisk "i" z opisem strategii
    info_button = tk.Button(frame_inputs, text="i", command=show_strategy_info)
    info_button.grid(row=6, column=2, padx=(5, 0))

    # Standardowa rata
    label_standard_rate = tk.Label(frame_inputs, text="Standardowa rata:")
    label_standard_rate.grid(row=7, column=0, sticky="e")
    entry_standard_rate = ttk.Entry(frame_inputs, state='readonly')
    entry_standard_rate.grid(row=7, column=1, sticky="w")

    # Kwota miesięczna / Nadpłata
    tk.Label(frame_inputs, text="Kwota miesięczna / Nadpłata:").grid(row=8, column=0, sticky="e")
    entry_fixed_overpayment = ttk.Entry(frame_inputs)
    entry_fixed_overpayment.grid(row=8, column=1, sticky="w")

    # Przyciski zapisu / wczytywania danych
    btn_frame = ttk.Frame(left_frame)
    btn_frame.pack(padx=10, pady=(0,10), fill='x')

    btn_save_data = ttk.Button(btn_frame, text="Zapisz dane", command=save_data)
    btn_save_data.pack(side='left', padx=5)

    btn_load_data = ttk.Button(btn_frame, text="Wczytaj dane", command=load_data)
    btn_load_data.pack(side='left', padx=5)

    # Przycisk "Oblicz"
    button_calculate = ttk.Button(btn_frame, text="Oblicz harmonogram", command=calculate)
    button_calculate.pack(side='left', padx=5)

    # -------------- PRAWA CZĘŚĆ (PODSUMOWANIE) -------------- #
    # summary_frame – tutaj pojawi się wynik obliczeń (oszczędności, wykres).

    # -------------- DOLNA CZĘŚĆ (HARMONOGRAM) -------------- #

    # Tabela (Treeview) do wyświetlania harmonogramu
    columns = (
        "Nr",
        "Data",
        "Oprocentowanie",
        "Pozostało do spłaty",
        "Wysokość raty",
        "Kapitał",
        "Odsetki",
        "Nadpłata",
        "Kapitał pozostały",
    )
    tree = ttk.Treeview(bottom_frame, columns=columns, show="headings")
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, anchor="center")
    tree.pack(side='top', padx=10, pady=10, fill="both", expand=True)

    # Przycisk eksportu harmonogramu
    btn_export_frame = ttk.Frame(bottom_frame)
    btn_export_frame.pack(side='bottom', pady=(0,10))
    btn_save_schedule = ttk.Button(btn_export_frame, text="Eksportuj harmonogram", command=save_schedule)
    btn_save_schedule.pack()

    # Start pętli głównej
    root.mainloop()
