import streamlit as st
import sqlite3
import bcrypt
import pandas as pd
import joblib
from catboost import CatBoostClassifier
import numpy as np

# --- Database Functions ---
def create_users_table():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    try:
        c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_pw))
        conn.commit()
        result = True
    except sqlite3.IntegrityError:
        result = False
    conn.close()
    return result

def check_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT password FROM users WHERE username = ?', (username,))
    result = c.fetchone()
    conn.close()
    if result and bcrypt.checkpw(password.encode('utf-8'), result[0]):
        return True
    return False

# --- UI ---
st.title("🔐 Login / Signup")

create_users_table()

menu = st.sidebar.selectbox("Menu", ["Login", "Signup"])


if menu == "Signup":
    st.subheader("Create a new account")
    new_user = st.text_input("Username")
    new_password = st.text_input("Password", type='password')
    if st.button("Signup"):
        if add_user(new_user, new_password):
            st.success("Account created successfully. Please log in.")
        else:
            st.error("Username already exists.")

elif menu == "Login":
    # label_encoders = joblib.load("label_encoders.pkl")
    # st.write("Encoder classes for 'Paperless Billing':", label_encoders['Offer'].classes_)
    st.subheader("Login to your account")
    username = st.text_input("Username")
    password = st.text_input("Password", type='password')
    if st.button("Login"):
        if check_user(username, password):
            st.session_state['logged_in'] = True
            st.session_state['username'] = username
            st.success(f"Welcome {username}!")
        else:
            st.error("Invalid username or password.")

# --- Protected content ---
if st.session_state.get('logged_in'):

    st.sidebar.success(f"Logged in as {st.session_state['username']}")
    st.sidebar.subheader("📋 Navigation")
    nav_option = st.sidebar.radio("Go to:", ["View Tables", "Prediction"])


    conn = sqlite3.connect('users.db')


    if nav_option == "View Tables":
        st.subheader("🔍 Search by Customer ID")
        search_id = st.text_input("Enter Customer ID")
        

        if search_id:
            query = f'''
            SELECT 
                customer."Customer ID" AS "Customer ID",
                customer.Gender AS "customer_Gender",
                customer.Age AS "customer_Age",
                customer."Senior Citizen" AS "customer_Senior Citizen",
                customer.Married AS "customer_Married",
                customer.Dependents AS "customer_Dependents",
                customer."Number of Dependents" AS "customer_Number of Dependents",
                customer."Under 30" AS "customer_Under 30",
                customer.Partner AS "customer_Partner",

                charges."Monthly Charge" AS "charges_Monthly Charge",
                charges."Total Charges" AS "charges_Total Charges",
                charges."Total Revenue" AS "charges_Total Revenue",
                charges."Total Refunds" AS "charges_Total Refunds",
                charges."Total Long Distance Charges" AS "charges_Total Long Distance Charges",
                charges."Total Extra Data Charges" AS "charges_Total Extra Data Charges",
                charges."Avg Monthly GB Download" AS "charges_Avg Monthly GB Download",
                charges."Avg Monthly Long Distance Charges" AS "charges_Avg Monthly Long Distance Charges",
                charges.CLTV AS "charges_CLTV",
                charges."Payment Method" AS "charges_Payment Method",
                charges."Paperless Billing" AS "charges_Paperless Billing",

                churn.Churn AS "churn_Churn",
                churn."Churn Category" AS "churn_Churn Category",
                churn."Churn Reason" AS "churn_Churn Reason",
                churn."Churn Score" AS "churn_Churn Score",
                churn."Customer Status" AS "churn_Customer Status",
                churn."Satisfaction Score" AS "churn_Satisfaction Score",

                location.City AS "location_City",
                location.State AS "location_State",
                location.Country AS "location_Country",
                location."Zip Code" AS "location_Zip Code",
                location.Latitude AS "location_Latitude",
                location.Longitude AS "location_Longitude",
                location."Lat Long" AS "location_Lat Long",
                location.Population AS "location_Population",

                referrals."Referred a Friend" AS "referrals_Referred a Friend",
                referrals."Number of Referrals" AS "referrals_Number of Referrals",
                referrals.Offer AS "referrals_Offer",
                referrals.Contract AS "referrals_Contract",
                referrals."Tenure in Months" AS "referrals_Tenure in Months",
                referrals.Quarter AS "referrals_Quarter",

                services."Phone Service" AS "services_Phone Service",
                services."Multiple Lines" AS "services_Multiple Lines",
                services."Internet Service" AS "services_Internet Service",
                services."Internet Type" AS "services_Internet Type",
                services."Streaming TV" AS "services_Streaming TV",
                services."Streaming Movies" AS "services_Streaming Movies",
                services."Streaming Music" AS "services_Streaming Music",
                services."Online Security" AS "services_Online Security",
                services."Online Backup" AS "services_Online Backup",
                services."Device Protection Plan" AS "services_Device Protection Plan",
                services."Premium Tech Support" AS "services_Premium Tech Support",
                services."Unlimited Data" AS "services_Unlimited Data"

            FROM customer
            LEFT JOIN charges ON customer."Customer ID" = charges."Customer ID"
            LEFT JOIN churn ON customer."Customer ID" = churn."Customer ID"
            LEFT JOIN location ON customer."Customer ID" = location."Customer ID"
            LEFT JOIN referrals ON customer."Customer ID" = referrals."Customer ID"
            LEFT JOIN services ON customer."Customer ID" = services."Customer ID"
            WHERE customer."Customer ID" = ?
        '''
            result_df = pd.read_sql_query(query, conn, params=(search_id,))
            if not result_df.empty:
                st.dataframe(result_df)
            else:
                st.warning("No customer found with that ID.")

    # Sidebar Table Viewer
        st.sidebar.subheader("📋 View Raw Tables")
        tables = ['charges', 'churn', 'customer', 'location', 'referrals', 'services']
        selected_table = st.sidebar.selectbox("Select Table", tables)

        df = pd.read_sql_query(f"SELECT * FROM {selected_table}", conn)
        st.dataframe(df)

        conn.close()

    elif nav_option == "Prediction":
        st.subheader("📈 Predict Churn / Score / Customer Status")
        st.markdown("Enter customer details below:")

        with st.form("prediction_form"):
            gender = st.selectbox("Gender", ['Male', 'Female'], index=0)
            age = st.number_input("Age", min_value=0, max_value=120, value=35)
            
            # Removed senior_citizen, under_30, partner as they're not in the specified features
            
            married = st.selectbox("Married", ['Yes', 'No'], index=0)
            dependents = st.selectbox("Dependents", ['Yes', 'No'], index=0)
            num_dependents = st.number_input("Number of Dependents", min_value=0, max_value=10, value=0)
            
            monthly_charge = st.number_input("Monthly Charge", min_value=0.0, value=65.0)
            total_charges = st.number_input("Total Charges", min_value=0.0, value=2000.0)
            total_refunds = st.number_input("Total Refunds", min_value=0.0, value=0.0)
            total_long_distance_charges = st.number_input("Total Long Distance Charges", min_value=0.0, value=50.0)
            total_extra_data_charges = st.number_input("Total Extra Data Charges", min_value=0.0, value=0.0)
            avg_monthly_gb_download = st.number_input("Avg Monthly GB Download", min_value=0.0, value=25.0)
            avg_monthly_long_distance_charges = st.number_input("Avg Monthly Long Distance Charges", min_value=0.0, value=10.0)
            
            payment_method = st.selectbox("Payment Method", [
                'Credit Card',
                'Bank Withdrawal',
                'Mailed Check'
            ], index=2)
            paperless_billing = st.selectbox("Paperless Billing", ['Yes', 'No'], index=0)
            
            # Removed city, country, zip_code, latitude, longitude as they're not in the specified features
            state = st.text_input("State", "California")
            
            # Removed population as it's not in the specified features
            
            num_referrals = st.number_input("Number of Referrals", min_value=0, value=0)
            offer = st.selectbox("Offer", [
                "None", "Offer A", "Offer B", "Offer C", "Offer D", "Offer E"
            ], index=0)
            contract = st.selectbox("Contract", ['Month-to-Month', 'One Year', 'Two Year'], index=0)
            tenure_months = st.number_input("Tenure in Months", min_value=0, value=12)
            
            # Removed quarter as it's not in the specified features
            
            phone_service = st.selectbox("Phone Service", ["Yes", "No"], index=0)
            multiple_lines = st.selectbox("Multiple Lines", ["Yes", "No", "No phone service"], index=0)
            internet_service = st.selectbox("Internet Service", ['Yes', 'No'], index=1)
            internet_type = st.selectbox("Internet Type", ["Cable", "DSL", "Fiber Optic", ], index=2)
            
            streaming_tv = st.selectbox("Streaming TV", ["Yes", "No"], index=0)
            streaming_movies = st.selectbox("Streaming Movies", ["Yes", "No"], index=0)
            streaming_music = st.selectbox("Streaming Music", ["Yes", "No"], index=0)
            
            online_security = st.selectbox("Online Security", ["Yes", "No"], index=0)
            online_backup = st.selectbox("Online Backup", ["Yes", "No"], index=0)
            device_protection = st.selectbox("Device Protection Plan", ["Yes", "No"], index=0)
            premium_support = st.selectbox("Premium Tech Support", ["Yes", "No"], index=0)
            unlimited_data = st.selectbox("Unlimited Data", ["Yes", "No"], index=0)
            
            # Added CLTV and Total Revenue which were in the specified features but missing from form
            cltv = st.number_input("CLTV (Customer Lifetime Value)", min_value=0, value=3000)
            total_revenue = st.number_input("Total Revenue", min_value=0.0, value=2500.0)

            submit = st.form_submit_button("Predict")

        binary_mapping = {
            "Yes": 1,
            "No": 0
        }

        if submit:
            features = {
                "Age": age,
                "Avg Monthly GB Download": avg_monthly_gb_download,
                "Avg Monthly Long Distance Charges": avg_monthly_long_distance_charges,
                "CLTV": cltv,
                "Contract": contract,
                "Dependents": binary_mapping.get(dependents, 0),
                "Device Protection Plan": binary_mapping.get(device_protection, 0),
                "Gender": gender,
                "Internet Service": binary_mapping.get(internet_service, 0),
                "Internet Type": internet_type,
                "Married": binary_mapping.get(married, 0),
                "Monthly Charge": monthly_charge,
                "Multiple Lines": binary_mapping.get(multiple_lines, 0),
                "Number of Dependents": num_dependents,
                "Number of Referrals": num_referrals,
                "Offer": None if offer == "None" else offer,
                "Online Backup": binary_mapping.get(online_backup, 0),
                "Online Security": binary_mapping.get(online_security, 0),
                "Paperless Billing": binary_mapping.get(paperless_billing, 0),
                "Payment Method": payment_method,
                "Phone Service": binary_mapping.get(phone_service, 0),
                "Premium Tech Support": binary_mapping.get(premium_support, 0),
                "State": state,
                "Streaming Movies": binary_mapping.get(streaming_movies, 0),
                "Streaming Music": binary_mapping.get(streaming_music, 0),
                "Streaming TV": binary_mapping.get(streaming_tv, 0),
                "Tenure in Months": tenure_months,
                "Total Charges": total_charges,
                "Total Extra Data Charges": total_extra_data_charges,
                "Total Long Distance Charges": total_long_distance_charges,
                "Total Refunds": total_refunds,
                "Total Revenue": total_revenue,
                "Unlimited Data": binary_mapping.get(unlimited_data, 0)
            }

            input_df = pd.DataFrame([features])

            # Load Random Forest model and label encoders
            model = joblib.load("rf_model.pkl")
            label_encoders = joblib.load("label_encoders.pkl")
            model_columns = joblib.load("model_features.pkl")  

            # Align input features
            input_df = input_df.reindex(columns=model_columns, fill_value=0)

            # Safe transformation with error handling
            for col in label_encoders:
                if col in input_df.columns:
                    try:
                        input_df[col] = input_df[col].astype(str).replace('None', np.nan)
                        # Only transform non-null values
                        mask = input_df[col].notna()
                        if mask.any():
                            input_df.loc[mask, col] = label_encoders[col].transform(input_df.loc[mask, col])
                    except ValueError as e:
                        st.error(f"Encoding failed for column '{col}': {e}")
                        st.stop()

            # Predict
            prediction = model.predict(input_df)[0]
            prediction_proba = model.predict_proba(input_df)[0][1]

            st.success(f"Prediction: {'Churn' if prediction == 1 else 'No Churn'}")
            st.info(f"Churn Probability: {prediction_proba:.2f}")
            
    if st.button("Logout"):
        st.session_state['logged_in'] = False
        st.session_state['username'] = None
        st.experimental_rerun()