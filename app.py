import os
import xgboost as xgb
import numpy as np
from flask import Flask, render_template, request, session, redirect, url_for
import sqlite3
import pickle
import pandas as pd
import datetime
import csv
import random
import smtplib
from email.message import EmailMessage
from io import StringIO
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email import policy
from email_validator import validate_email, EmailNotValidError
from flask import flash
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from flask_dance.contrib.google import make_google_blueprint, google
from flask_login import LoginManager, login_user, logout_user, current_user, login_required, UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func

app = Flask(__name__)
app.config['SECRET_KEY'] = 'e3f1c8940a8f4771a99de2be22cfb5aa'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['REMEMBER_COOKIE_DURATION'] = datetime.timedelta(seconds=1)
app.config['SESSION_FILE_THRESHOLD'] = 10

# ✅ Initialize LoginManager properly
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.session_protection = None



BASE_DIR = os.path.dirname(os.path.abspath(__file__))

model_path = os.path.join(BASE_DIR, "model", "model", "credit_model.json")
scaler_path = os.path.join(BASE_DIR, "model", "model", "scaler.pkl")
features_path = os.path.join(BASE_DIR, "model", "model", "features.pkl")

model = xgb.Booster()
try:
    model.load_model(model_path)
except Exception:
    pass

scaler = None
features = None
try:
    with open(scaler_path, "rb") as f:
        scaler = pickle.load(f)
    with open(features_path, "rb") as f:
        features = pickle.load(f)
except Exception:
    pass

USER_DB = os.path.join(BASE_DIR, "userdb", "user.db")
os.makedirs(os.path.dirname(USER_DB), exist_ok=True)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{USER_DB}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.unauthorized_handler
def unauthorized_callback():
    return redirect(url_for('index'))


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150))
    monthly_income = db.Column(db.Float, default=0)
    savings_goal = db.Column(db.Float, default=0)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(150), nullable=True)
    description = db.Column(db.String(500), nullable=True)
    user = db.relationship('User', backref=db.backref('transactions', lazy=True))

@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except Exception:
        return None

app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME=' ',
    MAIL_PASSWORD=' ',
    MAIL_DEFAULT_SENDER=' '
)
mail = Mail(app)

serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
google_bp = make_google_blueprint(
    client_id="6709...apps.googleusercontent.com",
    client_secret="GOCSPX-...cC_D",
    scope=[
        
    ],
    redirect_to="google_authorized"
)
app.register_blueprint(google_bp, url_prefix="/login")

TRANSACTION_CSV = os.path.join(BASE_DIR, 'fin_bot', 'transactions.csv')
os.makedirs(os.path.dirname(TRANSACTION_CSV), exist_ok=True)
if not os.path.exists(TRANSACTION_CSV):
    with open(TRANSACTION_CSV, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Date", "Amount", "Category", "Description"])

def evaluate_credit_score(score):
    if 750 <= score <= 900:
        return (
            "✅ Excellent — Easy loan approval",
            [
                {"bank": "HDFC Bank", "rate": "8.2%"},
                {"bank": "Axis Bank", "rate": "8.5%"},
                {"bank": "ICICI Bank", "rate": "8.1%"},
                {"bank": "Kotak Mahindra Bank", "rate": "8.3%"},
                {"bank": "SBI", "rate": "8.4%"},
            ]
        )
    elif 700 <= score < 750:
        return (
            "🟢 Good — Likely to get approved",
            [
                {"bank": "Punjab National Bank", "rate": "9.1%"},
                {"bank": "Union Bank of India", "rate": "9.4%"},
                {"bank": "IDFC First Bank", "rate": "9.3%"},
                {"bank": "Yes Bank", "rate": "9.5%"},
            ]
        )
    elif 650 <= score < 700:
        return (
            "🟡 Fair — You might face higher interest rates",
            [
                {"bank": "Bank of India", "rate": "10.5%"},
                {"bank": "UCO Bank", "rate": "10.3%"},
                {"bank": "Canara Bank", "rate": "10.4%"},
            ]
        )
    elif 550 <= score < 650:
        return (
            "🔴 Poor — Hard to get loan",
            [
                {"bank": "Bajaj Finserv", "rate": "14%"},
                {"bank": "Tata Capital", "rate": "15.5%"},
                {"bank": "Fullerton India", "rate": "16.5%"},
            ]
        )
    else:
        return (
            "❌ Very poor — High risk for lenders",
            []
        )

def get_tip():
    tips = [
        "Track every rupee you spend.",
        "Cancel subscriptions you don't use.",
        "Use the 50/30/20 budgeting rule.",
        "Automate savings and avoid credit card debt.",
        "Cook at home, save big.",
    ]
    return random.choice(tips)

def save_expense(form, user_id):
    amount = float(form.get("amount", 0))
    category = form.get("category", "Misc")
    description = form.get("description", "")
    txn = Transaction(
        user_id=user_id,
        date=datetime.datetime.utcnow(),
        amount=amount,
        category=category,
        description=description
    )
    db.session.add(txn)
    db.session.commit()

def get_user_total_spent(user_id):
    total = db.session.query(func.sum(Transaction.amount)).filter(Transaction.user_id == user_id).scalar()
    return total or 0

def get_user_summary(user_id):
    rows = db.session.query(Transaction.category, func.sum(Transaction.amount)) \
                     .filter(Transaction.user_id == user_id) \
                     .group_by(Transaction.category).all()
    return {r[0]: r[1] for r in rows}

def generate_report(user_id):
    rows = db.session.query(Transaction.date, Transaction.amount, Transaction.category, Transaction.description) \
                     .filter(Transaction.user_id == user_id).all()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Amount", "Category", "Description"])
    for r in rows:
        d = r[0]
        if isinstance(d, datetime.datetime):
            d = d.strftime("%Y-%m-%d")
        writer.writerow([d, r[1], r[2], r[3]])
    return output.getvalue()

def send_report_via_email(report_csv_data, to_email):
    sender_email = " "
    sender_password = " "

    # Create message
    message = MIMEMultipart()
    message["Subject"] = "📊 Your FinSmart Monthly Report"
    message["From"] = sender_email
    message["To"] = to_email

    # Body in UTF-8
    body = MIMEText(
        "Hi,\n\nAttached is your monthly spending report from FinSmart. 💸\n\nStay smart!",
        "plain",
        "utf-8"
    )
    message.attach(body)

    # CSV attachment in UTF-8
    attachment = MIMEApplication(report_csv_data.encode('utf-8'), Name="FinSmart_Report.csv")
    attachment.add_header("Content-Disposition", "attachment", filename="FinSmart_Report.csv")
    message.attach(attachment)

    # Send email using UTF-8 encoded string
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, message.as_bytes())  # ✅ Use as_bytes() instead of as_string()





def download_report_file_and_email(user):
    user_id = user.id
    email = user.email
    today = datetime.date.today().strftime("%Y-%m-%d")
    filename = f"report_{today}.csv"
    rows = db.session.query(Transaction.date, Transaction.amount, Transaction.category, Transaction.description) \
                     .filter(Transaction.user_id == user_id).all()
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Date", "Amount", "Category", "Description"])
        for r in rows:
            d = r[0]
            if isinstance(d, datetime.datetime):
                d = d.strftime("%Y-%m-%d")
            writer.writerow([d, r[1], r[2], r[3]])
    msg = EmailMessage()
    msg['Subject'] = f'📥 Your FinSmart Report - {today}'
    msg['From'] = " "
    msg['To'] = email
    msg.set_content("Attached is your personal spending report. Review and plan wisely!")
    with open(filename, 'rb') as f:
        msg.add_attachment(f.read(), maintype='application', subtype='csv', filename=filename)
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(" ", " ")
        smtp.send_message(msg)
    try:
        os.remove(filename)
    except Exception:
        pass




@app.route('/')
def index():
    from flask_login import current_user
    print("🔸 Still authenticated user:", current_user.id if current_user.is_authenticated else "No user")

    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')




@app.route('/loan', methods=['GET', 'POST'])
def loan():
    result = None
    probability = None
    error = None
    if request.method == 'POST':
        try:
            form = request.form
            age = float(form.get('Age'))
            income = float(form.get('AnnualIncome'))
            if age < 18:
                error = "❌ You must be at least 18 years old to apply for a loan."
                return render_template("loan.html", result=None, probability=None, error=error)
            if income < 150000:
                error = "❌ Your annual income must be at least ₹1,50,000 to be eligible for a loan."
                return render_template("loan.html", result=None, probability=None, error=error)
            user_data = {
                'Age': age,
                'InterestRate': float(form.get('InterestRate')),
                'AnnualIncome': income,
                'CreditScore': float(form.get('CreditScore')),
                'LoanAmount': float(form.get('LoanAmount')),
                'MonthlyIncome': float(form.get('MonthlyIncome')),
                'TotalLiabilities': float(form.get('TotalLiabilities')),
                'LoanDuration': float(form.get('LoanDuration')),
                'PreviousLoanDefaults': 1 if form.get('PreviousLoanDefaults') == 'Yes' else 0,
                'BankruptcyHistory': 1 if form.get('BankruptcyHistory') == 'Yes' else 0,
                'EducationLevel': form.get('EducationLevel'),
                'EmploymentStatus': form.get('EmploymentStatus'),
                'LoanPurpose': form.get('LoanPurpose'),
            }
            monthly_income = user_data['MonthlyIncome']
            liabilities = user_data['TotalLiabilities']
            loan_amount = user_data['LoanAmount']
            duration = user_data['LoanDuration']
            defaults = {
                'Experience': 5,
                'NumberOfDependents': 0,
                'MonthlyDebtPayments': 1000,
                'CreditCardUtilizationRate': 0.3,
                'NumberOfOpenCreditLines': 4,
                'NumberOfCreditInquiries': 2,
                'DebtToIncomeRatio': liabilities / monthly_income if monthly_income > 0 else 0,
                'LengthOfCreditHistory': 5,
                'SavingsAccountBalance': 30000,
                'CheckingAccountBalance': 15000,
                'TotalAssets': 250000,
                'JobTenure': 2,
                'NetWorth': 100000,
                'BaseInterestRate': 6.5,
                'MonthlyLoanPayment': loan_amount / duration if duration > 0 else 0,
                'LoanToIncome': loan_amount / monthly_income if monthly_income > 0 else 0,
                'TotalDebtToIncome': liabilities / monthly_income if monthly_income > 0 else 0,
                'NetAssets': 250000 - liabilities,
            }
            user_data.update(defaults)
            df_base = pd.DataFrame([{k: v for k, v in user_data.items() if k not in ['EducationLevel', 'EmploymentStatus', 'LoanPurpose']}])
            df_cat = pd.get_dummies(pd.DataFrame([{
                'EducationLevel': user_data['EducationLevel'],
                'EmploymentStatus': user_data['EmploymentStatus'],
                'LoanPurpose': user_data['LoanPurpose'],
            }]))
            input_df = pd.concat([df_base, df_cat], axis=1)
            if features is not None:
                input_df = input_df.reindex(columns=features, fill_value=0)
            if scaler is not None:
                input_scaled = scaler.transform(input_df)
            else:
                input_scaled = input_df.values
            try:
                result = model.predict(input_scaled)[0]
                probability = model.predict_proba(input_scaled)[0][1] * 100
            except Exception:
                try:
                    result = model.predict(xgb.DMatrix(input_scaled))[0]
                except Exception as e:
                    error = str(e)
        except Exception as e:
            error = str(e)
    return render_template("loan.html", result=result, probability=round(probability, 2) if probability else None, error=error)

@app.route('/bot', methods=['GET', 'POST'])
@login_required
def bot():
    result = None
    user_id = current_user.id
    income = session.get('income')
    if income is None:
        income = current_user.monthly_income or 0
        if income:
            session['income'] = income
    if request.method == 'POST':
        action = request.form.get('action')
        if 'monthly_income' in request.form:
            try:
                income = float(request.form['monthly_income'])
                current_user.monthly_income = income
                current_user.savings_goal = round(0.2 * income, 2)
                db.session.commit()
                session['income'] = income
                session['savings_goal'] = current_user.savings_goal
                spending_limit = 0.8 * income
                result = f"✅ Income saved. You should not exceed ₹{spending_limit:.2f} this month."
            except Exception:
                result = "❌ Invalid income entered."
        spending_limit = 0.8 * income if income else None
        if action == 'add':
            if not income:
                result = "⚠️ Please enter your monthly income first."
            else:
                save_expense(request.form, user_id)
                total_spent = get_user_total_spent(user_id)
                if spending_limit is not None and total_spent > spending_limit:
                    result = f"🚨 You've spent ₹{total_spent:.2f} which exceeds your 80% budget of ₹{spending_limit:.2f}."
                else:
                    result = f"✅ Expense saved. Total spent so far: ₹{total_spent:.2f}"
        elif action == 'summary':
            summary = get_user_summary(user_id)
            result = "<br>".join([f"{k}: ₹{v:.2f}" for k, v in summary.items()]) if summary else "No data."
        elif action == 'budget':
            if income:
                needs = 0.5 * income
                wants = 0.3 * income
                saves = 0.2 * income
                result = f"💡 With ₹{income:.2f}, allocate:<br>🛒 Needs: ₹{needs:.2f}<br>🎉 Wants: ₹{wants:.2f}<br>💰 Savings: ₹{saves:.2f}"
            else:
                result = "⚠️ Please enter your income first to get budget suggestions."
        elif action == 'tip':
            result = get_tip()
        elif action == 'download':
            try:
                download_report_file_and_email(current_user)
                result = "📧 Report sent to your email."
            except Exception as e:
                result = f"❌ Error sending report: {e}"
    return render_template('bot.html', result=result)

@app.route('/score', methods=['GET', 'POST'])
def score():
    result = None
    offers = []
    if request.method == 'POST':
        try:
            score_input = request.form['score']
            if not score_input.isdigit():
                raise ValueError("Score must be a number")
            score = int(score_input)
            if score < 100 or score > 900:
                raise ValueError("Score must be between 100 and 900")
            result, offers = evaluate_credit_score(score)
            session['offers'] = offers
            session['result'] = result
        except Exception as e:
            result = f"❌ Invalid score entered. {str(e)}"
            offers = []
            session['offers'] = []
            session['result'] = result
    return render_template('score.html', result=result, offers=offers)

@app.route("/calculate_emi", methods=["POST"])
def calculate_emi_route():
    bank = request.form["bank"]
    amount = float(request.form["amount"])
    tenure = int(request.form["tenure"])
    offers = session.get("offers", [])
    rate = next((float(offer["rate"].replace('%', '')) for offer in offers if offer["bank"] == bank), 10.0)
    emi = calculate_emi(amount, rate, tenure)
    result = session.get("result", "Your previous score result")
    return render_template("score.html", result=result, offers=offers, emi=emi)

def calculate_emi(principal, annual_rate, tenure_years):
    r = annual_rate / (12 * 100)
    n = tenure_years * 12
    emi = (principal * r * (1 + r) ** n) / ((1 + r) ** n - 1)
    return round(emi, 2)

@app.route('/alert', methods=['GET', 'POST'])
@login_required
def alert():
    result = None
    user_email = current_user.email
    user_id = current_user.id
    income = current_user.monthly_income or session.get("income")
    if request.method == 'POST':
        try:
            if not user_email or not user_id:
                result = "❌ You're not logged in. Please log in first."
                return render_template('alert.html', result=result, user_email=user_email)
            if income is None or income == 0:
                result = "⚠️ Please set your monthly income first in the bot section."
                return render_template('alert.html', result=result, user_email=user_email)
            threshold = 0.8 * float(income)
            current_month = datetime.date.today().strftime("%Y-%m")
            row = db.session.query(func.sum(Transaction.amount)) \
                            .filter(Transaction.user_id == user_id, func.strftime('%Y-%m', Transaction.date) == current_month) \
                            .scalar()
            total_spent = row if row else 0
            if total_spent > threshold:
                send_email_alert(total_spent, current_month, user_email)
                result = f"🚨 Alert email sent! You spent ₹{total_spent:.2f} which is above 80% of your income (₹{threshold:.2f})."
            else:
                result = f"✅ You're within your safe spending zone. Total: ₹{total_spent:.2f} (Limit: ₹{threshold:.2f})"
        except Exception as e:
            result = f"❌ Error: {e}"
    return render_template('alert.html', result=result, user_email=user_email)

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/privacy')
def privacy():
    return render_template("privacy.html")

@app.route('/terms')
def terms():
    return render_template("terms.html")

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        try:
            name = request.form['name']
            email = request.form['email']
            subject = request.form['subject']
            message = request.form['message']
            msg = EmailMessage()
            msg['Subject'] = f"📬 FinSmart Contact Form: {subject}"
            msg['From'] = ""
            msg['To'] = ""
            msg.set_content(f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}\n")
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(" ", " ")
                smtp.send_message(msg)
            return render_template("contact.html", success=True)
        except Exception as e:
            return render_template("contact.html", error=str(e))
    return render_template("contact.html")

@app.route('/confirm/<token>')
def confirm_email(token):
    try:
        email = serializer.loads(token, salt='email-verify', max_age=3600)
    except Exception:
        return render_template('login.html', error="❌ Verification link expired or invalid.")
    user = User.query.filter_by(email=email).first()
    if not user:
        return render_template('login.html', error="❌ Account not found.")
    user.is_verified = True
    db.session.commit()
    login_user(user, remember=True)
    return redirect(url_for('dashboard'))

@app.route('/signup', methods=['POST'])
def signup():
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    income = request.form.get('income')
    if not all([name, email, password, income]):
        return render_template('login.html', error="⚠️ All fields are required.")
    try:
        valid = validate_email(email)
        email = valid.email
    except EmailNotValidError:
        return render_template('login.html', error="❌ Invalid email format.")
    try:
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return render_template('login.html', error="❌ Email already exists.")
        hashed_password = generate_password_hash(password)
        new_user = User(
            name=name,
            email=email,
            password=hashed_password,
            monthly_income=float(income),
            savings_goal=round(0.2 * float(income), 2),
            is_verified=False
        )
        db.session.add(new_user)
        db.session.commit()
        token = serializer.dumps(email, salt='email-verify')
        link = url_for('confirm_email', token=token, _external=True)
        msg = Message("Confirm your FinSmart email", recipients=[email])
        msg.body = (
            f"Hi {name},\n\n"
            f"Click the link below to verify your email:\n{link}\n\n"
            f"Thanks,\nFinSmart Team"
        )
        mail.send(msg)
        return render_template('login.html', error="✅ Signup successful! Please check your email to verify your account.")
    except Exception as e:
        return render_template('login.html', error=f"❌ Error: {e}")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        try:
            valid = validate_email(email)
            email = valid.email
        except EmailNotValidError:
            return render_template('login.html', error="❌ Invalid email format.")
        user = User.query.filter_by(email=email).first()
        if not user:
            return render_template('login.html', error="❌ Invalid email or password.")
        if user.password is None:
            return render_template('login.html', error="⚠️ Please log in using Google.")
        if not check_password_hash(user.password, password):
            return render_template('login.html', error="❌ Invalid email or password.")
        if not user.is_verified:
            return render_template('login.html', error="❌ Please verify your email before logging in.")
        login_user(user, remember=True)
        next_page = request.args.get('next')
        return redirect(next_page or url_for('dashboard'))
    return render_template('login.html')

@app.route("/login/google/authorized")
def google_authorized():
    if not google.authorized:
        return redirect(url_for("google.login"))
    resp = google.get("/oauth2/v2/userinfo")
    if not resp.ok:
        return redirect(url_for("login"))
    user_info = resp.json()
    email = user_info.get("email")
    name = user_info.get("name", "Google User")
    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(
            email=email,
            name=name,
            password=None,
            monthly_income=0,
            savings_goal=0,
            is_verified=True
        )
        db.session.add(user)
        db.session.commit()
    login_user(user)
    session['income'] = user.monthly_income
    session['savings_goal'] = user.savings_goal
    return redirect(url_for("dashboard"))

@app.route('/dashboard')
@login_required
def dashboard():
    user = current_user
    last_5_txns = Transaction.query.filter_by(user_id=user.id) \
                      .order_by(Transaction.date.desc()) \
                      .limit(5).all()
    txns_list = [
        {
            'date': txn.date.strftime('%Y-%m-%d'),
            'amount': txn.amount,
            'category': txn.category,
            'description': txn.description
        } for txn in last_5_txns
    ]
    return render_template(
        'dashboard.html',
        user_name=user.name,
        income=user.monthly_income,
        savings_goal=user.savings_goal,
        last_5_txns=txns_list
    )

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    if request.method == 'POST':
        print("🔹 Logging out user:", current_user.id if current_user.is_authenticated else "No user")
        logout_user()
        session.clear()
        print("🔹 Session cleared.")

        resp = redirect(url_for('index'))
        resp.set_cookie('remember_token', '', expires=0)  # ✅ clears Flask-Login cookie
        return resp

    return render_template('logout.html')





@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user_id = current_user.id
    message = ""
    if request.method == 'POST':
        new_email = request.form['email']
        new_income = float(request.form['income'])
        new_savings_goal = round(0.2 * new_income, 2)
        current_user.email = new_email
        current_user.monthly_income = new_income
        current_user.savings_goal = new_savings_goal
        db.session.commit()
        session['income'] = new_income
        session['savings_goal'] = new_savings_goal
        message = "✅ Profile updated successfully."
    user = (current_user.name, current_user.email, current_user.monthly_income, current_user.savings_goal)
    return render_template("profile.html", user=user, message=message)

@app.route('/download')
@login_required
def download():
    try:
        report_csv_data = generate_report(current_user.id)
        send_report_via_email(report_csv_data, current_user.email)
        return render_template('message.html', message="📩 Report sent to your email.")
    except Exception as e:
        return render_template('message.html', message=f"❌ Error sending report: {str(e)}")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
