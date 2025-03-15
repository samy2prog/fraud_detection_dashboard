import streamlit as st
import pandas as pd
import requests
from sqlalchemy import create_engine, text
import hashlib

# 📌 Connexion à la base de données PostgreSQL
DATABASE_URL = "postgresql://neondb_owner:npg_KXoDg7AWT1yF@ep-late-mouse-a25ew7xn-pooler.eu-central-1.aws.neon.tech/neondb?sslmode=require"

try:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    conn = engine.connect()
    conn.close()
except Exception as e:
    st.error(f"❌ Erreur de connexion à la base de données : {e}")

# 📌 Charger les données des empreintes numériques
def load_fingerprints():
    try:
        query = text("""
            SELECT id, user_agent, ip_address, screen_resolution, timezone, language, 
                   refund_count, payment_attempts, country_ip, country_shipping, created_at 
            FROM user_fingerprints
        """)
        with engine.connect() as conn:
            df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement des empreintes numériques : {e}")
        return pd.DataFrame()

# 📌 Charger les transactions
def load_transactions():
    try:
        query = text("""
            SELECT id, user_agent, ip_address, screen_resolution, timezone, language, 
                   transaction_type, amount, created_at 
            FROM transactions
        """)
        with engine.connect() as conn:
            df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement des transactions : {e}")
        return pd.DataFrame()

# 📌 Générer un identifiant unique basé sur plusieurs caractéristiques
def generate_fingerprint(df):
    df['fingerprint'] = df.apply(lambda row: hashlib.sha256(
        (row['user_agent'] + row['screen_resolution'] + row['timezone'] + row['ip_address']).encode()
    ).hexdigest(), axis=1)
    return df

# 📌 Calcul du risk score basé sur plusieurs critères
def calculate_risk_score(df):
    df['risk_score'] = 0
    df['ip_count'] = df.groupby('fingerprint')['ip_address'].transform('nunique')
    df['risk_score'] += df['ip_count'] * 10
    df['fingerprint_count'] = df.groupby('ip_address')['fingerprint'].transform('nunique')
    df['risk_score'] += df['fingerprint_count'] * 10
    
    if 'refund_count' in df.columns:
        df['refund_requests'] = df.groupby('fingerprint')['refund_count'].transform('sum')
        df['risk_score'] += df['refund_requests'] * 15
    
    df['risk_score'] += df['payment_attempts'] * 5
    df['risk_score'] += df.apply(lambda row: 25 if row['country_ip'] != row['country_shipping'] else 0, axis=1)
    df['fingerprint_recurrence'] = df.groupby('fingerprint')['ip_address'].transform('count')
    df['risk_score'] += df['fingerprint_recurrence'] * 8
    df['risk_score'] = df['risk_score'].clip(0, 100)
    return df

# 📌 Interface Streamlit
st.title("📊 Fraud Detection Dashboard")
st.write("🚨 Ce tableau de bord affiche les empreintes numériques et les transactions suspectes.")

# 📌 Charger les empreintes et transactions
fingerprints_data = load_fingerprints()
transactions_data = load_transactions()

# 📌 Transformer et afficher les empreintes
if not fingerprints_data.empty:
    fingerprints_data = generate_fingerprint(fingerprints_data)
    fingerprints_data = calculate_risk_score(fingerprints_data)

    fingerprints_data['created_at'] = pd.to_datetime(fingerprints_data['created_at']).dt.strftime("%Y-%m-%d %H:%M:%S")

    fingerprints_data = fingerprints_data.rename(columns={
        "user_agent": "Navigateur",
        "ip_address": "Adresse IP",
        "screen_resolution": "Résolution Écran",
        "timezone": "Fuseau Horaire",
        "language": "Langue",
        "refund_count": "Remboursements",
        "payment_attempts": "Tentatives Paiement",
        "country_ip": "Pays IP",
        "country_shipping": "Pays Livraison",
        "created_at": "Date & Heure",
        "risk_score": "Score de Risque",
        "fingerprint": "Empreinte Unique"
    })

    st.subheader("📌 Empreintes Numériques")
    st.dataframe(fingerprints_data[["Date & Heure", "Adresse IP", "Navigateur", "Résolution Écran", "Fuseau Horaire",
                                    "Langue", "Pays IP", "Pays Livraison", "Remboursements", "Tentatives Paiement", 
                                    "Empreinte Unique", "Score de Risque"]])

# 📌 Transformer et afficher les transactions
if not transactions_data.empty:
    transactions_data['created_at'] = pd.to_datetime(transactions_data['created_at']).dt.strftime("%Y-%m-%d %H:%M:%S")

    transactions_data = transactions_data.rename(columns={
        "user_agent": "Navigateur",
        "ip_address": "Adresse IP",
        "screen_resolution": "Résolution Écran",
        "timezone": "Fuseau Horaire",
        "language": "Langue",
        "transaction_type": "Type Transaction",
        "amount": "Montant",
        "created_at": "Date & Heure"
    })

    st.subheader("💳 Transactions")
    st.dataframe(transactions_data[["Date & Heure", "Adresse IP", "Navigateur", "Résolution Écran", "Fuseau Horaire",
                                    "Langue", "Type Transaction", "Montant"]])


