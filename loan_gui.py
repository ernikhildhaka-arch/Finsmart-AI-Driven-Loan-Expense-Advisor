# Loan Prediction UI using Tkinter

import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import pickle

# Load model, scaler, and feature list
with open("credit_model.pkl", "rb") as f:
    model = pickle.load(f)
with open("scaler.pkl", "rb") as f:
    scaler = pickle.load(f)
with open("features.pkl", "rb") as f:
    feature_list = pickle.load(f)

# Function to collect inputs and predict

def predict():
    try:
        # Gather inputs
        inputs = {
            'Age': int(age_var.get()),
            'AnnualIncome': float(income_var.get()),
            'CreditScore': float(credit_score_var.get()),
            'LoanAmount': float(loan_amt_var.get()),
            'LoanDuration': float(loan_duration_var.get()),
            'MonthlyIncome': float(monthly_income_var.get()),
            'TotalLiabilities': float(liabilities_var.get()),
            'PreviousLoanDefaults': 1 if defaults_var.get() == "Yes" else 0,
            'BankruptcyHistory': 1 if bankruptcy_var.get() == "Yes" else 0,
            'EducationLevel': education_var.get(),
            'EmploymentStatus': employment_var.get(),
            'LoanPurpose': purpose_var.get(),
        }

        # Derived features
        inputs.update({
            'Experience': 5,
            'NumberOfDependents': 0,
            'MonthlyDebtPayments': 1000,
            'CreditCardUtilizationRate': 0.3,
            'NumberOfOpenCreditLines': 4,
            'NumberOfCreditInquiries': 2,
            'DebtToIncomeRatio': inputs['TotalLiabilities'] / inputs['MonthlyIncome'],
            'LengthOfCreditHistory': 5,
            'SavingsAccountBalance': 30000,
            'CheckingAccountBalance': 15000,
            'TotalAssets': 250000,
            'JobTenure': 2,
            'NetWorth': 100000,
            'BaseInterestRate': 6.5,
            'MonthlyLoanPayment': inputs['LoanAmount'] / inputs['LoanDuration'] if inputs['LoanDuration'] > 0 else 0,
            'LoanToIncome': inputs['LoanAmount'] / inputs['MonthlyIncome'],
            'TotalDebtToIncome': inputs['TotalLiabilities'] / inputs['MonthlyIncome'],
            'NetAssets': 250000 - inputs['TotalLiabilities']
        })

        # Split into numerical + one-hot
        df_base = pd.DataFrame([{k: v for k, v in inputs.items() if k not in ['EducationLevel', 'EmploymentStatus', 'LoanPurpose']}])
        df_cat = pd.get_dummies(pd.DataFrame([{
            'EducationLevel': inputs['EducationLevel'],
            'EmploymentStatus': inputs['EmploymentStatus'],
            'LoanPurpose': inputs['LoanPurpose']
        }]))
        user_df = pd.concat([df_base, df_cat], axis=1)
        user_df.columns = user_df.columns.astype(str)
        user_df = user_df.reindex(columns=feature_list, fill_value=0)
        scaled = scaler.transform(user_df)
        prediction = model.predict(scaled)[0]
        prob = model.predict_proba(scaled)[0][1]

        # Show result
        if prediction == 1:
            result_label.config(text=f"✅ Loan likely approved\nProbability: {prob:.2f}", foreground="green")
        else:
            result_label.config(text=f"❌ Loan likely rejected\nProbability: {prob:.2f}", foreground="red")
    except Exception as e:
        messagebox.showerror("Input Error", f"Please check inputs.\n\nDetails: {e}")

# Build UI
root = tk.Tk()
root.title("Finsmart Loan Predictor")
root.geometry("600x700")
root.configure(bg="#121212")

# Style
style = ttk.Style(root)
style.theme_use("clam")
style.configure("TLabel", background="#121212", foreground="white", font=("Segoe UI", 10))
style.configure("TButton", padding=6, relief="flat", background="#1f1f1f", foreground="white")
style.configure("TEntry", fieldbackground="#1f1f1f", foreground="white")

# Variables
age_var = tk.StringVar()
income_var = tk.StringVar()
credit_score_var = tk.StringVar()
loan_amt_var = tk.StringVar()
loan_duration_var = tk.StringVar()
monthly_income_var = tk.StringVar()
liabilities_var = tk.StringVar()
defaults_var = tk.StringVar(value="No")
bankruptcy_var = tk.StringVar(value="No")
education_var = tk.StringVar()
employment_var = tk.StringVar()
purpose_var = tk.StringVar()

# Inputs
fields = [
    ("Age", age_var),
    ("Annual Income", income_var),
    ("Credit Score", credit_score_var),
    ("Loan Amount", loan_amt_var),
    ("Loan Duration (months)", loan_duration_var),
    ("Monthly Income", monthly_income_var),
    ("Total Liabilities", liabilities_var)
]
for i, (label, var) in enumerate(fields):
    ttk.Label(root, text=label).grid(row=i, column=0, padx=10, pady=5, sticky='w')
    ttk.Entry(root, textvariable=var, width=30).grid(row=i, column=1, pady=5)

# Dropdowns
ttk.Label(root, text="Employment Status").grid(row=7, column=0, padx=10, pady=5, sticky='w')
ttk.Combobox(root, textvariable=employment_var, values=["Employed", "Unemployed", "Self-Employed"]).grid(row=7, column=1)

ttk.Label(root, text="Education Level").grid(row=8, column=0, padx=10, pady=5, sticky='w')
ttk.Combobox(root, textvariable=education_var, values=["High School", "Bachelor", "Master", "PhD"]).grid(row=8, column=1)

ttk.Label(root, text="Loan Purpose").grid(row=9, column=0, padx=10, pady=5, sticky='w')
ttk.Combobox(root, textvariable=purpose_var, values=["Home", "Car", "Debt Consolidation", "Education"]).grid(row=9, column=1)

# Toggles
ttk.Label(root, text="Previous Loan Defaults?").grid(row=10, column=0, padx=10, pady=5, sticky='w')
ttk.Combobox(root, textvariable=defaults_var, values=["Yes", "No"]).grid(row=10, column=1)

ttk.Label(root, text="Bankruptcy History?").grid(row=11, column=0, padx=10, pady=5, sticky='w')
ttk.Combobox(root, textvariable=bankruptcy_var, values=["Yes", "No"]).grid(row=11, column=1)

# Button
ttk.Button(root, text="Predict Loan Eligibility", command=predict).grid(row=12, column=0, columnspan=2, pady=20)

# Result
result_label = ttk.Label(root, text="")
result_label.grid(row=13, column=0, columnspan=2, pady=10)

root.mainloop()
