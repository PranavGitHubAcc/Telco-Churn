import streamlit as st
import sqlite3
import bcrypt
import pandas as pd
import joblib
from catboost import CatBoostClassifier

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
            gender = st.selectbox("Gender", ['Male', 'Female'])
            age = st.number_input("Age", min_value=0, max_value=120)
            senior_citizen = st.selectbox("Senior Citizen", ['Yes', 'No'])
            married = st.selectbox("Married", ['Yes', 'No'])
            dependents = st.selectbox("Dependents", ['Yes', 'No'])
            num_dependents = st.number_input("Number of Dependents", min_value=0, max_value=10)
            under_30 = st.selectbox("Under 30", ["Yes", "No"])
            partner = st.selectbox("Partner", ["Yes", "No"])

            monthly_charge = st.number_input("Monthly Charge", min_value=0.0)
            total_charges = st.number_input("Total Charges", min_value=0.0)
            total_refunds = st.number_input("Total Refunds", min_value=0.0)
            total_long_distance_charges = st.number_input("Total Long Distance Charges", min_value=0.0)
            total_extra_data_charges = st.number_input("Total Extra Data Charges", min_value=0.0)
            avg_monthly_gb_download = st.number_input("Avg Monthly GB Download", min_value=0.0)
            avg_monthly_long_distance_charges = st.number_input("Avg Monthly Long Distance Charges", min_value=0.0)

            payment_method = st.selectbox("Payment Method", [
                'Bank transfer (automatic)',
                'Credit card (automatic)',
                'Electronic check',
                'Mailed check'
            ])
            paperless_billing = st.selectbox("Paperless Billing", ['Yes', 'No'])

            city = st.text_input("City", "Los Angeles")
            state = st.text_input("State", "California")
            country = st.text_input("Country", "United States")
            zip_code = st.text_input("Zip Code", "90001")
            latitude = st.number_input("Latitude", value=34.05)
            longitude = st.number_input("Longitude", value=-118.24)
            population = st.number_input("Population", min_value=0, value=10000)

            referred = st.selectbox("Referred a Friend", ["Yes", "No"])
            num_referrals = st.number_input("Number of Referrals", min_value=0)
            offer = st.selectbox("Offer", [
                "None", "Offer A", "Offer B", "Offer C", "Offer D", "Offer E"
            ])
            contract = st.selectbox("Contract", ['Month-to-month', 'One year', 'Two year'])
            tenure_months = st.number_input("Tenure in Months", min_value=0)
            quarter = st.selectbox("Quarter", ["Q1", "Q2", "Q3", "Q4"])

            phone_service = st.selectbox("Phone Service", ["Yes", "No"])
            multiple_lines = st.selectbox("Multiple Lines", ["Yes", "No", "No phone service"])
            internet_service = st.selectbox("Internet Service", ['DSL', 'Fiber optic', 'No'])
            internet_type = st.selectbox("Internet Type", ["Cable", "DSL", "Fiber Optic", "No"])
            streaming_tv = st.selectbox("Streaming TV", ["Yes", "No"])
            streaming_movies = st.selectbox("Streaming Movies", ["Yes", "No"])
            streaming_music = st.selectbox("Streaming Music", ["Yes", "No"])
            online_security = st.selectbox("Online Security", ["Yes", "No"])
            online_backup = st.selectbox("Online Backup", ["Yes", "No"])
            device_protection = st.selectbox("Device Protection Plan", ["Yes", "No"])
            premium_support = st.selectbox("Premium Tech Support", ["Yes", "No"])
            unlimited_data = st.selectbox("Unlimited Data", ["Yes", "No"])

            submit = st.form_submit_button("Predict")

        if submit:
            features = {
                "gender": gender,
                "age": age,
                "senior_citizen": senior_citizen,
                "married": married,
                "dependents": dependents,
                "num_dependents": num_dependents,
                "under_30": under_30,
                "partner": partner,
                "monthly_charge": monthly_charge,
                "total_charges": total_charges,
                "total_refunds": total_refunds,
                "total_long_distance_charges": total_long_distance_charges,
                "total_extra_data_charges": total_extra_data_charges,
                "avg_monthly_gb_download": avg_monthly_gb_download,
                "avg_monthly_long_distance_charges": avg_monthly_long_distance_charges,
                "payment_method": payment_method,
                "paperless_billing": paperless_billing,
                "city": city,
                "state": state,
                "country": country,
                "zip_code": zip_code,
                "latitude": latitude,
                "longitude": longitude,
                "population": population,
                "referred": referred,
                "num_referrals": num_referrals,
                "offer": offer,
                "contract": contract,
                "tenure_months": tenure_months,
                "quarter": quarter,
                "phone_service": phone_service,
                "multiple_lines": multiple_lines,
                "internet_service": internet_service,
                "internet_type": internet_type,
                "streaming_tv": streaming_tv,
                "streaming_movies": streaming_movies,
                "streaming_music": streaming_music,
                "online_security": online_security,
                "online_backup": online_backup,
                "device_protection": device_protection,
                "premium_support": premium_support,
                "unlimited_data": unlimited_data
            }

            input_df = pd.DataFrame([features])
            input_df = pd.get_dummies(input_df)

            model = CatBoostClassifier()
            model.load_model("catboost_churn_model.cbm")
            scaler = joblib.load("scaler.pkl")
            model_columns = joblib.load("model_features.pkl")

            input_df = input_df.reindex(columns=model_columns, fill_value=0)
            input_scaled = scaler.transform(input_df)

            prediction = model.predict(input_scaled)[0]
            prediction_proba = model.predict_proba(input_scaled)[0][1]

            st.success(f"Prediction: {'Churn' if prediction == 1 else 'No Churn'}")
            st.info(f"Churn Probability: {prediction_proba:.2f}")
            
    if st.button("Logout"):
        st.session_state['logged_in'] = False
        st.session_state['username'] = None
        st.experimental_rerun()