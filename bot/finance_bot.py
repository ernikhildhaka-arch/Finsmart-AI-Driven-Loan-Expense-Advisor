# Phase 3: Personal Finance Bot (Enhanced with Income-Based Alerts & Report Download)

import csv
import datetime
import random
import os

# CSV File to store transactions
DATA_FILE = "transactions.csv"

# Global variables for income and alert
monthly_income = None
alert_threshold = None

# Ensure file exists and set income threshold
def init_file():
    global monthly_income, alert_threshold
    try:
        with open(DATA_FILE, mode='x', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Date", "Amount", "Category", "Description"])
    except FileExistsError:
        pass

    # Ask for income at start
    try:
        monthly_income = float(input("💰 Enter your monthly income (used for budget & alerts): ₹"))
        alert_threshold = 0.8 * monthly_income
        print(f"🚨 You’ll be alerted if your spending exceeds ₹{alert_threshold:.2f} this month.")
    except ValueError:
        print("❌ Invalid input. Default threshold will not be set.")

# Add expense to CSV and check alert
def add_expense():
    amount = float(input("Enter amount spent: "))
    category = input("Enter category (e.g., groceries, rent , subscription , Bills): ")
    description = input("Enter short description: ")
    date = datetime.date.today().isoformat()

    with open(DATA_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([date, amount, category, description])

    print(f"✅ Expense of ₹{amount} added to category '{category}'.")

    # Spending alert
    total_spent = 0
    with open(DATA_FILE, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            total_spent += float(row['Amount'])

    if alert_threshold and total_spent > alert_threshold:
        print(f"🚨 Alert: Your total spending ₹{total_spent:.2f} has exceeded 80% of your monthly income!")

# Show summary of spending by category
def show_summary():
    summary = {}
    try:
        with open(DATA_FILE, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                category = row['Category']
                amount = float(row['Amount'])
                summary[category] = summary.get(category, 0) + amount
        print("\n📊 Spending Summary:")
        for cat, amt in summary.items():
            print(f"- {cat}: ₹{amt:.2f}")
    except FileNotFoundError:
        print("No data found.")

# Suggest a basic 50/30/20 budget

def suggest_budget():
    income = float(input("Enter your monthly income: "))
    needs = 0.5 * income
    wants = 0.3 * income
    savings = 0.2 * income
    print("\n📈 Suggested Monthly Budget (50/30/20 Rule):")
    print(f"- Needs (50%): ₹{needs:.2f}")
    print(f"- Wants (30%): ₹{wants:.2f}")
    print(f"- Savings (20%): ₹{savings:.2f}")

# Provide a saving tip

def saving_tip():
    tips = [
        "Set a monthly savings goal — Even ₹500 a month adds up over time!",
        "Track every rupee — Use apps or a notebook to see where your money goes.",
        "Avoid impulse purchases — Wait 24 hours before buying anything non-essential.",
        "Cancel unused subscriptions — Streaming services, gym, or apps you don’t use.",
        "Cook at home — Homemade meals are healthier and cheaper.",
        "Use cash instead of cards — You’ll feel more aware of your spending.",
        "Buy during sales — Plan big purchases around festive or end-of-season sales.",
        "Use the 50/30/20 rule — Budget your income smartly.",
        "Automate savings — Set a recurring bank transfer to a savings account.",
        "Avoid credit card debt — Interest can eat into your savings quickly.",
        "Shop with a list — Especially for groceries to avoid overspending.",
        "Buy generic brands — Often same quality, lower cost.",
        "Start an emergency fund — Aim for 3-6 months of expenses saved up.",
        "Turn off lights & appliances — Save on electricity and lower bills.",
        "Review your expenses weekly — Spot patterns and adjust your budget."
    ]
    print("\n💡 Saving Tip:")
    print(random.choice(tips))

# Export report to CSV

def download_report():
    today = datetime.date.today().strftime("%Y-%m-%d")
    filename = f"report_{today}.csv"
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as src, open(filename, 'w', newline='') as dest:
            dest.write(src.read())
        print(f"📥 Report downloaded as '{filename}'")
    else:
        print("❌ No transaction data to export.")

# Main chatbot loop
def run_bot():
    init_file()
    print("\n🤖 Welcome to FinSmart - Your Personal Finance Bot (Income-Aware)")
    while True:
        print("\n📋 Menu:")
        print("1. Add Expense")
        print("2. Show Expense Summary")
        print("3. Suggest Monthly Budget")
        print("4. Give Me a Saving Tip")
        print("5. Download My Report")
        print("6. Exit")

        choice = input("Enter choice (1-6): ")

        if choice == '1':
            add_expense()
        elif choice == '2':
            show_summary()
        elif choice == '3':
            suggest_budget()
        elif choice == '4':
            saving_tip()
        elif choice == '5':
            download_report()
        elif choice == '6':
            print("👋 Goodbye! Stay financially smart.")
            break
        else:
            print("❌ Invalid choice. Please try again.")

if __name__ == '__main__':
    run_bot()
