import os
import pandas as pd
import numpy as np
import pickle
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, roc_auc_score
import xgboost as xgb

# -----------------------------------------------
# Step 1: Load Dataset
# -----------------------------------------------
df = pd.read_csv("C:/Users/nikhi/OneDrive/Desktop/finsmart/model/new_loan.csv")  
df.drop(columns=['ApplicationDate'], inplace=True)

# -----------------------------------------------
# Step 2: Convert Numeric Columns
# -----------------------------------------------
numeric_cols = [
    'Age', 'AnnualIncome', 'CreditScore', 'Experience', 'LoanAmount', 'LoanDuration',
    'NumberOfDependents', 'MonthlyDebtPayments', 'CreditCardUtilizationRate',
    'NumberOfOpenCreditLines', 'NumberOfCreditInquiries', 'DebtToIncomeRatio',
    'LengthOfCreditHistory', 'SavingsAccountBalance', 'CheckingAccountBalance',
    'TotalAssets', 'TotalLiabilities', 'MonthlyIncome', 'JobTenure', 'NetWorth',
    'BaseInterestRate', 'InterestRate', 'MonthlyLoanPayment', 'TotalDebtToIncomeRatio',
    'RiskScore'
]

for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors='coerce')
df['LoanApproved'] = pd.to_numeric(df['LoanApproved'], errors='coerce')

# -----------------------------------------------
# Step 3: Handle Missing and Categorical Values
# -----------------------------------------------
df.fillna(df.median(numeric_only=True), inplace=True)

df['BankruptcyHistory'] = df['BankruptcyHistory'].apply(lambda x: 1 if str(x).lower() == 'yes' else 0)
df['PreviousLoanDefaults'] = df['PreviousLoanDefaults'].apply(lambda x: 1 if str(x).lower() == 'yes' else 0)

categorical_cols = ['EmploymentStatus', 'EducationLevel', 'MaritalStatus',
                    'HomeOwnershipStatus', 'LoanPurpose', 'UtilityBillsPaymentHistory', 'PaymentHistory']
df = pd.get_dummies(df, columns=categorical_cols, drop_first=True)

# -----------------------------------------------
# Step 4: Feature Engineering
# -----------------------------------------------
df['LoanToIncome'] = df['LoanAmount'] / df['MonthlyIncome']
df['TotalDebtToIncome'] = df['TotalLiabilities'] / df['MonthlyIncome']
df['NetAssets'] = df['TotalAssets'] - df['TotalLiabilities']

# -----------------------------------------------
# Step 5: Final Cleanup
# -----------------------------------------------
target = 'LoanApproved'
df.replace([np.inf, -np.inf], np.nan, inplace=True)
df.fillna(df.median(numeric_only=True), inplace=True)

X = df.drop(columns=[target, 'RiskScore'])
y = df[target]

# -----------------------------------------------
# Step 6: Feature Scaling
# -----------------------------------------------
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# -----------------------------------------------
# Step 7: Train-Test Split and Model Training
# -----------------------------------------------
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

model = xgb.XGBClassifier(eval_metric='logloss')
model.fit(X_train, y_train)

# -----------------------------------------------
# Step 8: Model Evaluation
# -----------------------------------------------
y_pred = model.predict(X_test)
print("\n📊 Model Performance:")
print(classification_report(y_test, y_pred))
print("ROC-AUC Score:", roc_auc_score(y_test, model.predict_proba(X_test)[:, 1]))

# -----------------------------------------------
# Step 9: Save Model, Scaler, and Features
# -----------------------------------------------

output_dir = os.path.join(os.path.dirname(__file__), "model")
os.makedirs(output_dir, exist_ok=True)

# Save XGBoost model properly
model.save_model(os.path.join(output_dir, "credit_model.json"))

# Save scaler and features using pickle (this is correct)
with open(os.path.join(output_dir, "scaler.pkl"), "wb") as f:
    pickle.dump(scaler, f)

with open(os.path.join(output_dir, "features.pkl"), "wb") as f:
    pickle.dump(X.columns.tolist(), f)


print("\n✅ Model, scaler, and features saved successfully.")
