# schedule.py

from datetime import datetime

def generate_installment_dates(start_date, num_installments):
    """
    Generuje listę dat (jako stringi) dla rat kredytu, dodając co miesiąc do start_date.
    
    :param start_date: Data, od której rozpoczynamy generowanie.
    :param num_installments: Liczba rat do wygenerowania.
    :return: Lista dat w formacie 'YYYY-MM-DD'.
    """
    dates = []
    current_date = start_date

    for _ in range(num_installments):
        # Dodajemy 1 miesiąc do current_date
        month = current_date.month + 1
        year = current_date.year
        if month > 12:
            month = 1
            year += 1

        # Dzień ograniczamy do 28, aby uniknąć błędów w miesiącach o mniejszej liczbie dni
        day = min(current_date.day, 28)

        # Aktualizujemy current_date
        current_date = current_date.replace(year=year, month=month, day=day)
        dates.append(current_date.strftime('%Y-%m-%d'))

    return dates
