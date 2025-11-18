import csv
import datetime
import smtplib
from email.message import EmailMessage

DATA_FILE = "bot/transactions.csv"

# Send email alert
def send_email_alert(amount, month, to_email):
    msg = EmailMessage()
    msg['Subject'] = f'\U0001F6A8 Monthly Budget Exceeded - {month}'
    msg['From'] = " "
    msg['To'] = to_email

    msg.set_content(f'''
Dear User,

⚠️ ALERT: Your total spending for {month} has exceeded your budget.

Current spending: ₹{amount:.2f}

Please review your expenses and plan accordingly.

- FinSmart Bot
''')

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(" ", " ")  # App password (never share this in public repos!)
            smtp.send_message(msg)
        return "📧 Email alert sent successfully."
    except Exception as e:
        return f"❌ Failed to send email: {e}"

# Alert user if monthly spending exceeds threshold and send email
def spending_alert(threshold, email):
    today = datetime.date.today()
    current_month = today.strftime("%Y-%m")
    total_spent = 0

    try:
        with open(DATA_FILE, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['Date'].startswith(current_month):
                    total_spent += float(row['Amount'])

        if total_spent > threshold:
            email_status = send_email_alert(total_spent, current_month, email)
            return f"🚨 Alert: You've spent ₹{total_spent:.2f} — over your budget of ₹{threshold}!\n{email_status}"
        else:
            return f"✅ You're within budget. Total spent: ₹{total_spent:.2f}"
    except FileNotFoundError:
        return "❌ No transaction data found."
    except Exception as e:
        return f"❌ Error reading data: {e}"
