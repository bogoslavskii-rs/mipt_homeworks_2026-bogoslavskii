#!/usr/bin/env python

from collections.abc import Callable
from typing import Any

UNKNOWN_COMMAND_MSG = "Unknown command!"
NONPOSITIVE_VALUE_MSG = "Value must be grater than zero!"
INCORRECT_DATE_MSG = "Invalid date!"
NOT_EXISTS_CATEGORY = "Category not exists!"
OP_SUCCESS_MSG = "Added"

INCOME_TYPE = "income"
COST_TYPE = "cost"

TYPE = "type"
AMOUNT = "amount"
DATE = "date"
CATEGORY = "category"

INCOME_ARGS = 3
COST_ARGS = 4
STATS_ARGS = 2
MONTHS = 12

Date = tuple[int, int, int]
Context = tuple[float, float, float, float, dict[str, float]]

EXPENSE_CATEGORIES = {
    "Food": ("Supermarket", "Restaurants", "FastFood", "Coffee", "Delivery"),
    "Transport": ("Taxi", "Public transport", "Gas", "Car service"),
    "Housing": ("Rent", "Utilities", "Repairs", "Furniture"),
    "Health": ("Pharmacy", "Doctors", "Dentist", "Lab tests"),
    "Entertainment": ("Movies", "Concerts", "Games", "Subscriptions"),
    "Clothing": ("Outerwear", "Casual", "Shoes", "Accessories"),
    "Education": ("Courses", "Books", "Tutors"),
    "Communications": ("Mobile", "Internet", "Subscriptions"),
    "Other": ("SomeCategory", "SomeOtherCategory"),
}

DAYS_IN_MONTH = (
    31,
    28,
    31,
    30,
    31,
    30,
    31,
    31,
    30,
    31,
    30,
    31,
)

financial_transactions_storage: list[dict[str, Any]] = []


def is_leap_year(year: int) -> bool:
    if year % 400 == 0:
        return True
    if year % 100 == 0:
        return False
    return year % 4 == 0


def extract_date(maybe_dt: str) -> Date | None:
    parts = maybe_dt.split("-")
    if len(parts) != INCOME_ARGS:
        return None

    if not all(p.isdigit() for p in parts):
        return None

    day, month, year = map(int, parts)

    if not 1 <= month <= MONTHS:
        return None

    days = list(DAYS_IN_MONTH)
    if is_leap_year(year):
        days[1] = 29

    if not 1 <= day <= days[month - 1]:
        return None

    return day, month, year


def valid_category(category_name: str) -> bool:
    if "::" not in category_name:
        return False

    main, sub = category_name.split("::", 1)

    if main not in EXPENSE_CATEGORIES:
        return False

    return sub in EXPENSE_CATEGORIES[main]


def income_handler(amount: float, income_date: str) -> str:
    if amount <= 0:
        financial_transactions_storage.append({})
        return NONPOSITIVE_VALUE_MSG

    dt = extract_date(income_date)
    if dt is None:
        financial_transactions_storage.append({})
        return INCORRECT_DATE_MSG

    financial_transactions_storage.append(
        {
            TYPE: INCOME_TYPE,
            AMOUNT: amount,
            DATE: dt,
        }
    )

    return OP_SUCCESS_MSG


def cost_handler(category_name: str, amount: float, income_date: str) -> str:
    if not valid_category(category_name):
        financial_transactions_storage.append({})
        return NOT_EXISTS_CATEGORY

    if amount <= 0:
        financial_transactions_storage.append({})
        return NONPOSITIVE_VALUE_MSG

    dt = extract_date(income_date)
    if dt is None:
        financial_transactions_storage.append({})
        return INCORRECT_DATE_MSG

    financial_transactions_storage.append(
        {
            TYPE: COST_TYPE,
            CATEGORY: category_name,
            AMOUNT: amount,
            DATE: dt,
        }
    )

    return OP_SUCCESS_MSG


def build_categories() -> list[str]:
    result: list[str] = []

    for cat, subs in EXPENSE_CATEGORIES.items():
        for sub in subs:
            pair = f"{cat}::{sub}"
            result.append(pair)

    return result


def cost_categories_handler() -> str:
    return "\n".join(build_categories())


def date_leq(d1: Date, d2: Date) -> bool:
    if d1[2] < d2[2]:
        return True
    if d1[2] > d2[2]:
        return False
    if d1[1] < d2[1]:
        return True
    if d1[1] > d2[1]:
        return False
    return d1[0] <= d2[0]


def is_same_month(d: Date, dt: Date) -> bool:
    same_month = d[1] == dt[1]
    same_year = d[2] == dt[2]
    return same_month and same_year


def handle_transaction(
    tr: dict[str, Any],
    target_date: Date,
    category_map: dict[str, float],
) -> tuple[float, float, float, float]:
    d = tr.get(DATE)
    if not d or not date_leq(d, target_date):
        return 0, 0, 0, 0

    total = tr[AMOUNT]

    if tr[TYPE] == INCOME_TYPE:
        if is_same_month(d, target_date):
            return total, 0, total, 0
        return total, 0, 0, 0

    if is_same_month(d, target_date):
        cat = tr[CATEGORY]
        category_map[cat] = category_map.get(cat, 0) + total
        return 0, total, 0, total

    return 0, total, 0, 0


def process_transactions(
    transactions: list[dict[str, Any]],
    target_date: Date,
) -> Context:
    total_income: float = 0
    total_cost: float = 0
    month_income: float = 0
    month_cost: float = 0
    category_map: dict[str, float] = {}

    for tr in transactions:
        inc, cost, mon_inc, mon_cost = handle_transaction(
            tr,
            target_date,
            category_map,
        )
        total_income += inc
        total_cost += cost
        month_income += mon_inc
        month_cost += mon_cost

    return total_income, total_cost, month_income, month_cost, category_map


def format_stats(dt: Date, totals: Context) -> str:
    total_income = totals[0]
    total_cost = totals[1]
    month_income = totals[2]
    month_cost = totals[3]
    category_map = totals[4]

    total_capital = total_income - total_cost
    diff = month_income - month_cost

    lines = [
        "Stats as of {:02d}-{:02d}-{}:".format(*dt),
        f"Total capital: {total_capital:.2f}",
    ]

    if diff >= 0:
        lines.append(f"Profit this month: {diff:.2f}")
    else:
        diff *= -1
        lines.append(f"Loss this month: {diff:.2f}")

    lines.append(f"Income: {month_income:.2f}")
    lines.append(f"Costs: {month_cost:.2f}")
    lines.append("Breakdown:")

    for i, cat in enumerate(sorted(category_map), 1):
        lines.append(f"{i}. {cat}: {category_map[cat]}")

    return "\n".join(lines)


def stats_handler(report_date: str) -> str:
    dt = extract_date(report_date)
    if dt is None:
        return INCORRECT_DATE_MSG

    totals = process_transactions(
        financial_transactions_storage,
        dt,
    )

    return format_stats(dt, totals)


def parse_float(value: str) -> float | None:
    normalized = value.replace(",", ".")

    if normalized.count(".") > 1:
        return None

    parts = normalized.split(".")
    if not all(part.isdigit() for part in parts if part):
        return None

    return float(normalized)


def handle_income(parts: list[str]) -> str:
    amount = parse_float(parts[1])
    if amount is None:
        return UNKNOWN_COMMAND_MSG
    return income_handler(amount, parts[2])


def handle_cost(parts: list[str]) -> str:
    amount = parse_float(parts[2])
    if amount is None:
        return UNKNOWN_COMMAND_MSG
    return cost_handler(parts[1], amount, parts[3])


Handler = Callable[[list[str]], str]


def get_handler(cmd: str) -> tuple[Handler | None, int | None]:
    if cmd == INCOME_TYPE:
        return handle_income, INCOME_ARGS

    if cmd == COST_TYPE:
        return handle_cost, COST_ARGS

    return None, None


def process_handler(parts: list[str]) -> str:
    cmd = parts[0]

    if cmd == "categories":
        return cost_categories_handler()

    if cmd == "stats" and len(parts) == STATS_ARGS:
        return stats_handler(parts[1])

    handler, expected_len = get_handler(cmd)

    if handler is None:
        return UNKNOWN_COMMAND_MSG

    if expected_len is not None and len(parts) != expected_len:
        return UNKNOWN_COMMAND_MSG

    return handler(parts)


def handle_command(parts: list[str]) -> str:
    if not parts:
        return UNKNOWN_COMMAND_MSG

    return process_handler(parts)


def main() -> None:
    line = input()

    while line:
        print(handle_command(line.strip().split()))
        line = input()


if __name__ == "__main__":
    main()
