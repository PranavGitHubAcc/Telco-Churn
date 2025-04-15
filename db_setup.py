import sqlite3
import pandas as pd

# File paths to CSVs
csv_files = {
    'charges': 'charges.csv',
    'churn': 'churn.csv',
    'customer': 'customer.csv',
    'location': 'location.csv',
    'referrals': 'referrals.csv',
    'services': 'services.csv'
}

# Connect to SQLite DB
conn = sqlite3.connect('users.db')
cursor = conn.cursor()

# Define basic schema for each table (you can update types later)
table_schemas = {
    'charges': '''
        CREATE TABLE IF NOT EXISTS charges (
            "Customer ID" TEXT PRIMARY KEY,
            "Monthly Charge" REAL,
            "Total Charges" REAL,
            "Total Revenue" REAL,
            "Total Refunds" REAL,
            "Total Long Distance Charges" REAL,
            "Total Extra Data Charges" REAL,
            "Avg Monthly GB Download" REAL,
            "Avg Monthly Long Distance Charges" REAL,
            "CLTV" REAL,
            "Payment Method" TEXT,
            "Paperless Billing" TEXT
        )
    ''',
    'churn': '''
        CREATE TABLE IF NOT EXISTS churn (
            "Customer ID" TEXT PRIMARY KEY,
            "Churn" TEXT,
            "Churn Category" TEXT,
            "Churn Reason" TEXT,
            "Churn Score" INTEGER,
            "Customer Status" TEXT,
            "Satisfaction Score" INTEGER
        )
    ''',
    'customer': '''
        CREATE TABLE IF NOT EXISTS customer (
            "Customer ID" TEXT PRIMARY KEY,
            "Gender" TEXT,
            "Age" INTEGER,
            "Senior Citizen" TEXT,
            "Married" TEXT,
            "Dependents" TEXT,
            "Number of Dependents" INTEGER,
            "Under 30" TEXT,
            "Partner" TEXT
        )
    ''',
    'location': '''
        CREATE TABLE IF NOT EXISTS location (
            "Customer ID" TEXT PRIMARY KEY,
            "City" TEXT,
            "State" TEXT,
            "Country" TEXT,
            "Zip Code" TEXT,
            "Latitude" REAL,
            "Longitude" REAL,
            "Lat Long" TEXT,
            "Population" INTEGER
        )
    ''',
    'referrals': '''
        CREATE TABLE IF NOT EXISTS referrals (
            "Customer ID" TEXT PRIMARY KEY,
            "Referred a Friend" TEXT,
            "Number of Referrals" INTEGER,
            "Offer" TEXT,
            "Contract" TEXT,
            "Tenure in Months" INTEGER,
            "Quarter" TEXT
        )
    ''',
    'services': '''
        CREATE TABLE IF NOT EXISTS services (
            "Customer ID" TEXT PRIMARY KEY,
            "Phone Service" TEXT,
            "Multiple Lines" TEXT,
            "Internet Service" TEXT,
            "Internet Type" TEXT,
            "Streaming TV" TEXT,
            "Streaming Movies" TEXT,
            "Streaming Music" TEXT,
            "Online Security" TEXT,
            "Online Backup" TEXT,
            "Device Protection Plan" TEXT,
            "Premium Tech Support" TEXT,
            "Unlimited Data" TEXT
        )
    '''
}

# Create tables
for table_name, schema in table_schemas.items():
    cursor.execute(schema)

# Insert CSV data
for table_name, file_path in csv_files.items():
    df = pd.read_csv(file_path)
    df.to_sql(table_name, conn, if_exists='replace', index=False)

conn.commit()
conn.close()
print("Database setup complete.")