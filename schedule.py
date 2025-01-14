# schedule.py

from datetime import datetime, timedelta

def generate_installment_dates(start_date, num_installments):
    """
    Generates a list of dates for the installments.

    :param start_date: The date from which to start generating dates.
    :param num_installments: The number of installment dates to generate.
    :return: List of dates as strings in format 'YYYY-MM-DD'.
    """
    dates = []
    current_date = start_date

    for _ in range(num_installments):
        # Add one month to the current date
        month = current_date.month - 1 + 1
        year = current_date.year + month // 12
        month = month % 12 + 1
        day = min(current_date.day, 28)  # To handle months with less than 31 days
        current_date = current_date.replace(year=year, month=month, day=day)
        dates.append(current_date.strftime('%Y-%m-%d'))

    return dates
