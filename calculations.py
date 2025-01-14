# calculations.py

from decimal import Decimal, getcontext

getcontext().prec = 10  # Ustawiamy precyzję obliczeń dziesiętnych

def calculate_monthly_rate(loan_amount, annual_interest_rate, loan_period_months):
    """
    Oblicza stałą miesięczną ratę kredytu (raty annuitetowe).
    """
    loan_amount = Decimal(loan_amount)
    annual_interest_rate = Decimal(annual_interest_rate)
    loan_period_months = int(loan_period_months)

    monthly_interest_rate = annual_interest_rate / Decimal('12') / Decimal('100')
    if monthly_interest_rate == 0:
        return loan_amount / loan_period_months
    else:
        rate = loan_amount * (monthly_interest_rate * (1 + monthly_interest_rate) ** loan_period_months) / \
               ((1 + monthly_interest_rate) ** loan_period_months - 1)
        return rate

def calculate_payment_schedule(loan_amount, interest_changes, loan_period_months, additional_costs=0):
    """
    Generuje harmonogram spłat kredytu z ratami stałymi (annuitetowymi) bez nadpłat.
    Uwzględnia zmiany oprocentowania w czasie oraz dodatkowe koszty.

    :param loan_amount: Kwota kredytu.
    :param interest_changes: Lista krotek (miesiąc, oprocentowanie) wskazująca zmiany oprocentowania.
    :param loan_period_months: Okres kredytowania w miesiącach.
    :param additional_costs: Dodatkowe koszty (prowizje, ubezpieczenia).
    :return: Lista słowników z harmonogramem spłat.
    """
    schedule = []
    remaining_balance = Decimal(loan_amount) + Decimal(additional_costs)
    loan_period_months = int(loan_period_months)

    # Przygotowanie listy oprocentowania dla każdego miesiąca
    monthly_interest_rates = [Decimal('0.0')] * loan_period_months
    current_interest_rate = Decimal(interest_changes[0][1]) / Decimal('12') / Decimal('100')
    change_index = 0

    for month in range(loan_period_months):
        # Sprawdzamy, czy w tym miesiącu jest zmiana oprocentowania
        if change_index + 1 < len(interest_changes) and month + 1 == interest_changes[change_index + 1][0]:
            change_index += 1
            current_interest_rate = Decimal(interest_changes[change_index][1]) / Decimal('12') / Decimal('100')
        monthly_interest_rates[month] = current_interest_rate

    for installment_number in range(1, loan_period_months + 1):
        current_debt = remaining_balance

        monthly_interest_rate = monthly_interest_rates[installment_number - 1]

        # Obliczamy ratę dla aktualnego salda i oprocentowania
        remaining_periods = loan_period_months - installment_number + 1
        monthly_rate = calculate_monthly_rate(remaining_balance, monthly_interest_rate * Decimal('12') * Decimal('100'), remaining_periods)

        interest_payment = remaining_balance * monthly_interest_rate
        capital_payment = monthly_rate - interest_payment

        # Sprawdzamy, czy nie przekroczymy pozostałego kapitału
        if remaining_balance < capital_payment:
            capital_payment = remaining_balance
            monthly_rate = capital_payment + interest_payment

        remaining_balance -= capital_payment

        overpayment = Decimal('0.00')

        installment = {
            'installment_number': installment_number,
            'date': '',  # Data zostanie dodana w GUI
            'interest_rate': round(monthly_interest_rate * Decimal('12') * Decimal('100'), 2),
            'current_debt': round(current_debt, 2),
            'installment_amount': round(monthly_rate, 2),
            'capital_payment': round(capital_payment, 2),
            'interest_payment': round(interest_payment, 2),
            'overpayment': round(overpayment, 2),
            'remaining_capital': round(remaining_balance, 2),
        }
        schedule.append(installment)

        if remaining_balance <= 0:
            break

    return schedule

def calculate_payment_schedule_with_fixed_overpayment(loan_amount, interest_changes, loan_period_months, fixed_overpayment, additional_costs=0):
    """
    Generuje harmonogram spłat kredytu z ratami stałymi (annuitetowymi) i stałą nadpłatą.
    Uwzględnia zmiany oprocentowania w czasie oraz dodatkowe koszty.
    """
    schedule = []
    remaining_balance = Decimal(loan_amount) + Decimal(additional_costs)
    loan_period_months = int(loan_period_months)
    fixed_overpayment = Decimal(fixed_overpayment)

    # Przygotowanie listy oprocentowania dla każdego miesiąca
    monthly_interest_rates = [Decimal('0.0')] * loan_period_months
    current_interest_rate = Decimal(interest_changes[0][1]) / Decimal('12') / Decimal('100')
    change_index = 0

    for month in range(loan_period_months):
        if change_index + 1 < len(interest_changes) and month + 1 == interest_changes[change_index + 1][0]:
            change_index += 1
            current_interest_rate = Decimal(interest_changes[change_index][1]) / Decimal('12') / Decimal('100')
        monthly_interest_rates[month] = current_interest_rate

    installment_number = 0

    while remaining_balance > 0:
        installment_number += 1
        current_debt = remaining_balance

        if installment_number > loan_period_months:
            break

        monthly_interest_rate = monthly_interest_rates[installment_number - 1]

        remaining_periods = loan_period_months - installment_number + 1
        monthly_rate = calculate_monthly_rate(remaining_balance, monthly_interest_rate * Decimal('12') * Decimal('100'), remaining_periods)

        interest_payment = remaining_balance * monthly_interest_rate
        capital_payment = monthly_rate - interest_payment

        # Nadpłata
        overpayment = fixed_overpayment
        if remaining_balance - capital_payment < overpayment:
            overpayment = remaining_balance - capital_payment

        # Upewniamy się, że nadpłata nie jest ujemna
        if overpayment < 0:
            overpayment = Decimal('0.00')

        total_capital_payment = capital_payment + overpayment
        remaining_balance -= total_capital_payment

        installment = {
            'installment_number': installment_number,
            'date': '',
            'interest_rate': round(monthly_interest_rate * Decimal('12') * Decimal('100'), 2),
            'current_debt': round(current_debt, 2),
            'installment_amount': round(monthly_rate, 2),
            'capital_payment': round(capital_payment, 2),
            'interest_payment': round(interest_payment, 2),
            'overpayment': round(overpayment, 2),
            'remaining_capital': round(remaining_balance, 2),
        }

        schedule.append(installment)

    return schedule

def calculate_payment_schedule_mix_strategy(loan_amount, interest_changes, loan_period_months, total_monthly_payment, additional_costs=0):
    """
    Generuje harmonogram spłat kredytu według "Strategii mix", gdzie łączna płatność miesięczna jest stała
    i równa kwocie podanej przez użytkownika. Nadpłata jest różnicą między podaną kwotą a aktualną ratą kredytu,
    która zmniejsza się w wyniku nadpłat z poprzednich miesięcy.
    Uwzględnia zmiany oprocentowania w czasie oraz dodatkowe koszty.
    """
    schedule = []
    remaining_balance = Decimal(loan_amount) + Decimal(additional_costs)
    loan_period_months = int(loan_period_months)
    total_monthly_payment = Decimal(total_monthly_payment)

    # Przygotowanie listy oprocentowania dla każdego miesiąca
    monthly_interest_rates = [Decimal('0.0')] * loan_period_months
    current_interest_rate = Decimal(interest_changes[0][1]) / Decimal('12') / Decimal('100')
    change_index = 0

    for month in range(loan_period_months):
        if change_index + 1 < len(interest_changes) and month + 1 == interest_changes[change_index + 1][0]:
            change_index += 1
            current_interest_rate = Decimal(interest_changes[change_index][1]) / Decimal('12') / Decimal('100')
        monthly_interest_rates[month] = current_interest_rate

    # Sprawdzamy, czy podana kwota jest większa niż początkowa rata
    initial_monthly_rate = calculate_monthly_rate(remaining_balance, interest_changes[0][1], loan_period_months)
    if total_monthly_payment <= initial_monthly_rate:
        raise ValueError("Kwota miesięczna musi być większa niż standardowa rata kredytu.")

    installment_number = 0

    while remaining_balance > 0:
        installment_number += 1
        current_debt = remaining_balance

        if installment_number > loan_period_months:
            break

        monthly_interest_rate = monthly_interest_rates[installment_number - 1]

        remaining_periods = loan_period_months - installment_number + 1
        monthly_rate = calculate_monthly_rate(remaining_balance, monthly_interest_rate * Decimal('12') * Decimal('100'), remaining_periods)

        interest_payment = remaining_balance * monthly_interest_rate
        capital_payment = monthly_rate - interest_payment

        # Nadpłata jest różnicą między podaną kwotą a aktualną ratą kredytu
        overpayment = total_monthly_payment - monthly_rate

        # Sprawdzamy, czy nadpłata nie przekracza pozostałego kapitału
        if remaining_balance - capital_payment < overpayment:
            overpayment = remaining_balance - capital_payment

        # Upewniamy się, że nadpłata nie jest ujemna
        if overpayment < 0:
            overpayment = Decimal('0.00')

        total_capital_payment = capital_payment + overpayment
        remaining_balance -= total_capital_payment

        installment = {
            'installment_number': installment_number,
            'date': '',
            'interest_rate': round(monthly_interest_rate * Decimal('12') * Decimal('100'), 2),
            'current_debt': round(current_debt, 2),
            'installment_amount': round(monthly_rate, 2),
            'capital_payment': round(capital_payment, 2),
            'interest_payment': round(interest_payment, 2),
            'overpayment': round(overpayment, 2),
            'remaining_capital': round(remaining_balance, 2),
        }

        schedule.append(installment)

    return schedule

def calculate_savings(original_schedule, overpayment_schedule):
    """
    Oblicza oszczędności wynikające z nadpłat.

    :param original_schedule: Harmonogram bez nadpłat.
    :param overpayment_schedule: Harmonogram z nadpłatami.
    :return: Słownik z informacjami o oszczędnościach.
    """
    original_interest = sum(
        [inst["interest_payment"] for inst in original_schedule]
    )
    overpayment_interest = sum(
        [inst["interest_payment"] for inst in overpayment_schedule]
    )
    interest_savings = original_interest - overpayment_interest

    original_period = len(original_schedule)
    overpayment_period = len(overpayment_schedule)
    period_reduction = original_period - overpayment_period

    return {
        "original_interest": round(original_interest, 2),
        "overpayment_interest": round(overpayment_interest, 2),
        "interest_savings": round(interest_savings, 2),
        "original_period": original_period,
        "overpayment_period": overpayment_period,
        "period_reduction": period_reduction,
    }
