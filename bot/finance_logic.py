import csv
import datetime
import os
import random

DATA_DIR = "bot"
DATA_FILE = os.path.join(DATA_DIR, "transactions.csv")

def init_data_file():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Date", "Amount", "Category", "Description"])


# ---------------------- Evaluate Credit Score ----------------------
def evaluate_credit_score(score):
    if 750 <= score <= 900:
        message = "Excellent — Easy loan approval"
        offers = [
            {"bank": "HDFC Bank", "rate": "8.5%"},
            {"bank": "ICICI Bank", "rate": "8.7%"},
            {"bank": "SBI", "rate": "8.9%"}
        ]
    elif 700 <= score < 750:
        message = "Good — Likely to get approved"
        offers = [
            {"bank": "Axis Bank", "rate": "9.5%"},
            {"bank": "Punjab National Bank", "rate": "9.8%"}
        ]
    elif 650 <= score < 700:
        message = "Fair — You might face higher interest rates"
        offers = [
            {"bank": "Kotak Mahindra", "rate": "10.5%"}
        ]
    elif 550 <= score < 650:
        message = "Poor — Hard to get loan"
        offers = []
    else:
        message = "Very poor — High risk for lenders"
        offers = []

    return message, offers


# ---------------------- Save Expense & Alert ----------------------
def save_expense(form, monthly_income):
    init_data_file()

    date = datetime.date.today().isoformat()
    amount = float(form.get("amount", 0))
    category = form.get("category", "Misc")
    description = form.get("description", "")

    with open(DATA_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([date, amount, category, description])

    # Spending alert
    total_spent = 0
    with open(DATA_FILE, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            total_spent += float(row['Amount'])

    if monthly_income and total_spent > 0.8 * monthly_income:
        return f"🚨 Alert: Your total spending ₹{total_spent:.2f} has exceeded 80% of your monthly income!"
    else:
        return None

# ---------------------- Get Expense Summary ----------------------
def get_summary():
    init_data_file()
    summary = {}
    try:
        with open(DATA_FILE, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                category = row['Category']
                amount = float(row['Amount'])
                summary[category] = summary.get(category, 0) + amount
    except FileNotFoundError:
        return {}
    return summary

# ---------------------- Get Saving Tip ----------------------
def get_tip():
    tips = [
        "Track every rupee you spend.",
        "Cancel subscriptions you don't use.",
        "Use the 50/30/20 budgeting rule.",
        "Buy groceries in bulk to save.",
        "Avoid credit card debt.",
        "Automate monthly savings.",
        "Cook at home more often.",
        "Review expenses weekly to find leaks.",
        "Avoid shopping when emotional.",
    ]
    return random.choice(tips)

# ---------------------- Download CSV Report ----------------------
def download_report():
    init_data_file()
    today = datetime.date.today().strftime("%Y-%m-%d")
    filename = f"report_{today}.csv"
    with open(DATA_FILE, 'r') as src, open(filename, 'w', newline='') as dest:
        dest.write(src.read())
