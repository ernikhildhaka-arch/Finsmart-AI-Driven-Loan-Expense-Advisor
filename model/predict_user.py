import pickle
import pandas as pd

def get_minimal_user_input():
    """
    Gather user inputs including validation for age and annual income.
    """
    while True:
        age = int(input("Enter your age: "))
        if age < 18:
            print("❌ You must be at least 18 years old to apply for a loan.")
        else:
            break

    while True:
        annual_income = float(input("Enter your annual income (Minimum ₹1.5 Lakhs): "))
        if annual_income < 150000:
            print("❌ Annual income must be at least ₹1,50,000 to apply for a loan.")
        else:
            break

    user_data = {
        'Age': age,
        'InterestRate': float(input("Enter InterestRate Minimum 10.05: ")),
        'AnnualIncome': annual_income,
        'CreditScore': float(input("Enter your credit score: ")),
        'LoanAmount': float(input("Requested loan amount: ")),
        'MonthlyIncome': float(input("Monthly income: ")),
        'TotalLiabilities': float(input("Total liabilities: ")),
        'LoanDuration': float(input("Loan duration (in months): ")),
        'PreviousLoanDefaults': 1 if input("Any previous loan defaults? (Yes/No): ").lower() == "yes" else 0,
        'BankruptcyHistory': 1 if input("Any bankruptcy history? (Yes/No): ").lower() == "yes" else 0,
        'EducationLevel': input("Education level (High School, Bachelor, Master, PhD): "),
        'EmploymentStatus': input("Employment status (Employed, Unemployed, Self-Employed): "),
        'LoanPurpose': input("Loan purpose (Home, Car, Debt Consolidation, Education): "),
    }

    # Default/derived features
    defaults = {
        'Experience': 5,
        'NumberOfDependents': 0,
        'MonthlyDebtPayments': 1000,
        'CreditCardUtilizationRate': 0.3,
        'NumberOfOpenCreditLines': 4,
        'NumberOfCreditInquiries': 2,
        'DebtToIncomeRatio': user_data['TotalLiabilities'] / user_data['MonthlyIncome'],
        'LengthOfCreditHistory': 5,
        'SavingsAccountBalance': 30000,
        'CheckingAccountBalance': 15000,
        'TotalAssets': 250000,
        'JobTenure': 2,
        'NetWorth': 100000,
        'BaseInterestRate': 6.5,
    }

    if user_data['LoanDuration'] > 0:
        defaults['MonthlyLoanPayment'] = user_data['LoanAmount'] / user_data['LoanDuration']
    else:
        defaults['MonthlyLoanPayment'] = 0

    defaults['LoanToIncome'] = user_data['LoanAmount'] / user_data['MonthlyIncome']
    defaults['TotalDebtToIncome'] = user_data['TotalLiabilities'] / user_data['MonthlyIncome']
    defaults['NetAssets'] = defaults['TotalAssets'] - user_data['TotalLiabilities']

    user_data.update(defaults)
    return user_data
