import csv
import datetime
import smtplib
from email.message import EmailMessage

DATA_FILE = "transactions.csv"

# Credit score evaluator
# Evaluate credit score text
def evaluate_credit_score(score):
    if 750 <= score <= 900:
        return "Excellent — Easy loan approval"
    elif 700 <= score < 750:
        return "Good — Likely to get approved"
    elif 650 <= score < 700:
        return "Fair — You might face higher interest rates"
    elif 550 <= score < 650:
        return "Poor — Hard to get loan"
    else:
        return "Very poor — High risk for lenders"

# Get bank offers based on credit score
def get_bank_offers(score):
    if score >= 750:
        return [
            {"bank": "HDFC Bank", "rate": "8.2%"},
            {"bank": "ICICI Bank", "rate": "8.4%"},
            {"bank": "SBI", "rate": "8.5%"},
        ]
    elif 700 <= score < 750:
        return [
            {"bank": "Axis Bank", "rate": "9.0%"},
            {"bank": "Kotak Mahindra", "rate": "9.2%"},
        ]
    elif 650 <= score < 700:
        return [
            {"bank": "PNB", "rate": "10.5%"},
            {"bank": "IDBI", "rate": "10.8%"},
        ]
    elif 550 <= score < 650:
        return [
            {"bank": "Bajaj Finserv", "rate": "12.0%"},
        ]
    else:
        return []

# Function to send alert email
def send_email_alert(amount, month):
    msg = EmailMessage()
    msg['Subject'] = f'🚨 Monthly Budget Exceeded - {month}'
    msg['From'] = " "
    msg['To'] =  input("Enter your email ")

    msg.set_content(f'''
Dear User,

⚠️ ALERT: Your total spending for {month} has exceeded your budget.

Current spending: ₹{amount:.2f}

Please review your expenses and plan accordingly.

- FinSmart Bot
''')

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(" ", " ")
            smtp.send_message(msg)
        print("📧 Email alert sent successfully.")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

# Alert user if monthly spending exceeds threshold
def spending_alert(threshold):
    today = datetime.date.today()
    current_month = today.strftime("%Y-%m")
    total_spent = 0

    try:
        with open(DATA_FILE, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['Date'].startswith(current_month):
                    total_spent += float(row['Amount'])

        print(f"\n📊 Total spending in {current_month}: ₹{total_spent:.2f}")
        if total_spent > threshold:
            print("🚨 Alert: You've exceeded your monthly budget!")
            send_email_alert(total_spent, current_month)
        else:
            print("✅ You are within your budget. Keep it up!")
    except FileNotFoundError:
        print("❌ No transaction data found.")

# CLI Interface
def run_alert_bot():
    print("\n💬 Welcome to FinSmart Alerts + Credit Score Checker")

    while True:
        print("\nChoose an option:")
        print("1. Check Spending Alert")
        print("2. Evaluate Credit Score")
        print("3. Exit")

        choice = input("Enter choice (1-3): ")

        if choice == '1':
            budget = float(input("Enter your monthly budget: ₹"))
            spending_alert(budget)
        elif choice == '2':
            score = int(input("Enter your credit score: "))
            print("📈 Credit Score Status:", evaluate_credit_score(score))
        elif choice == '3':
            print("👋 Exiting Alert Bot.")
            break
        else:
            print("❌ Invalid choice. Try again.")

if __name__ == '__main__':
    run_alert_bot()
