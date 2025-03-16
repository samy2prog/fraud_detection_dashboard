import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import hashlib

# Connexion à la base de données PostgreSQL
DATABASE_URL = "postgresql://neondb_owner:npg_KXoDg7AWT1yF@ep-late-mouse-a25ew7xn-pooler.eu-central-1.aws.neon.tech/neondb?sslmode=require"
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

st.title("📊 Fraud Detection Dashboard")
st.write("🚨 Empreintes numériques et transactions suspectes.")

# Charger les empreintes numériques avec jointure
@st.cache_data
def load_fingerprints():
    query = text("""
        SELECT uf.id AS fingerprint_id, uf.user_agent, uf.ip_address, uf.screen_resolution, uf.timezone, 
               uf.language, uf.account_age, uf.average_refund_time, uf.payment_attempts, 
               uf.country_ip, uf.country_shipping, uf.created_at,
               COALESCE(SUM(CASE WHEN t.transaction_type = 'refund' THEN 1 ELSE 0 END), 0) AS refund_count,
               COUNT(t.id) AS total_transactions
        FROM user_fingerprints uf
        LEFT JOIN transactions t ON uf.id = t.fingerprint_id
        GROUP BY uf.id, uf.user_agent, uf.ip_address, uf.screen_resolution, uf.timezone, 
                 uf.language, uf.account_age, uf.average_refund_time, uf.payment_attempts, 
                 uf.country_ip, uf.country_shipping, uf.created_at
    """)
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    return df

# Charger les transactions
@st.cache_data
def load_transactions():
    query = text("""
        SELECT id, fingerprint_id, user_agent, ip_address, screen_resolution, timezone, language, 
               transaction_type, amount, created_at 
        FROM transactions
    """)
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    return df

# Générer un identifiant unique basé sur plusieurs caractéristiques
def generate_fingerprint(df):
    df['fingerprint'] = df.apply(lambda row: hashlib.sha256(
        (row['user_agent'] + row['screen_resolution'] + row['timezone'] + row['ip_address']).encode()
    ).hexdigest(), axis=1)
    return df

# Calcul du risk score basé sur plusieurs critères
def calculate_risk_score(df):
    df['risk_score'] = 0
    df['risk_score'] += df['refund_count'] * 20
    df['risk_score'] += df['payment_attempts'] * 5
    df['risk_score'] += df.apply(lambda row: 25 if row['country_ip'] != row['country_shipping'] else 0, axis=1)
    df['risk_score'] = df['risk_score'].clip(0, 100)
    return df

# Affichage des empreintes numériques
fingerprints_data = load_fingerprints()
transactions_data = load_transactions()

if not fingerprints_data.empty:
    fingerprints_data = generate_fingerprint(fingerprints_data)
    fingerprints_data = calculate_risk_score(fingerprints_data)

    fingerprints_data['created_at'] = pd.to_datetime(fingerprints_data['created_at']).dt.strftime("%Y-%m-%d %H:%M:%S")

    st.subheader("📌 Empreintes Numériques")
    st.dataframe(fingerprints_data[["created_at", "ip_address", "user_agent", "screen_resolution", "timezone",
                                    "language", "country_ip", "country_shipping", "refund_count", "payment_attempts", 
                                    "total_transactions", "risk_score"]])

# Affichage des transactions
if not transactions_data.empty:
    transactions_data['created_at'] = pd.to_datetime(transactions_data['created_at']).dt.strftime("%Y-%m-%d %H:%M:%S")

    st.subheader("💳 Transactions")
    st.dataframe(transactions_data[["created_at", "ip_address", "user_agent", "screen_resolution", "timezone",
                                    "language", "transaction_type", "amount"]])

