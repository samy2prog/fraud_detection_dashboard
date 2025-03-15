import streamlit as st
import pandas as pd
import requests
from sqlalchemy import create_engine, text
import hashlib

# \ud83d\udccc Connexion \u00e0 la base de donn\u00e9es PostgreSQL
DATABASE_URL = "postgresql://neondb_owner:npg_KXoDg7AWT1yF@ep-late-mouse-a25ew7xn-pooler.eu-central-1.aws.neon.tech/neondb?sslmode=require"

try:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    conn = engine.connect()
    conn.close()
except Exception as e:
    st.error(f"\u274c Erreur de connexion \u00e0 la base de donn\u00e9es : {e}")

# \ud83d\udccc Charger les donn\u00e9es des empreintes num\u00e9riques
def load_fingerprints():
    try:
        query = text("""
            SELECT uf.id, uf.user_agent, uf.ip_address, uf.screen_resolution, uf.timezone, uf.language, 
                   uf.payment_attempts, uf.country_ip, uf.country_shipping, uf.created_at, 
                   COALESCE(SUM(CASE WHEN t.transaction_type = 'refund' THEN 1 ELSE 0 END), 0) AS refund_count
            FROM user_fingerprints uf
            LEFT JOIN transactions t ON uf.ip_address = t.ip_address
            GROUP BY uf.id, uf.user_agent, uf.ip_address, uf.screen_resolution, uf.timezone, uf.language, 
                     uf.payment_attempts, uf.country_ip, uf.country_shipping, uf.created_at
        """)
        with engine.connect() as conn:
            df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        st.error(f"\u274c Erreur lors du chargement des empreintes num\u00e9riques : {e}")
        return pd.DataFrame()

# \ud83d\udccc Charger les transactions
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
        st.error(f"\u274c Erreur lors du chargement des transactions : {e}")
        return pd.DataFrame()

# \ud83d\udccc G\u00e9n\u00e9rer un identifiant unique bas\u00e9 sur plusieurs caract\u00e9ristiques
def generate_fingerprint(df):
    df['fingerprint'] = df.apply(lambda row: hashlib.sha256(
        (row['user_agent'] + row['screen_resolution'] + row['timezone'] + row['ip_address']).encode()
    ).hexdigest(), axis=1)
    return df

# \ud83d\udccc Calcul du risk score bas\u00e9 sur plusieurs crit\u00e8res
def calculate_risk_score(df):
    df['risk_score'] = 0
    df['ip_count'] = df.groupby('fingerprint')['ip_address'].transform('nunique')
    df['risk_score'] += df['ip_count'] * 10
    df['fingerprint_count'] = df.groupby('ip_address')['fingerprint'].transform('nunique')
    df['risk_score'] += df['fingerprint_count'] * 10
    
    df['risk_score'] += df['payment_attempts'] * 5
    df['risk_score'] += df.apply(lambda row: 25 if row['country_ip'] != row['country_shipping'] else 0, axis=1)
    df['fingerprint_recurrence'] = df.groupby('fingerprint')['ip_address'].transform('count')
    df['risk_score'] += df['fingerprint_recurrence'] * 8
    
    df['risk_score'] += df['refund_count'] * 15
    df['risk_score'] += df.apply(lambda row: 20 if row['refund_count'] > 2 else 0, axis=1)
    df['risk_score'] += df.apply(lambda row: 30 if row['refund_count'] + row['payment_attempts'] > 5 else 0, axis=1)
    
    df['risk_score'] = df['risk_score'].clip(0, 100)
    return df

# \ud83d\udccc Interface Streamlit
st.title("\ud83d\udcca Fraud Detection Dashboard")
st.write("\ud83d\udea8 Ce tableau de bord affiche les empreintes num\u00e9riques et les transactions suspectes.")

# \ud83d\udccc Charger les empreintes et transactions
fingerprints_data = load_fingerprints()
transactions_data = load_transactions()

# \ud83d\udccc Transformer et afficher les empreintes
if not fingerprints_data.empty:
    fingerprints_data = generate_fingerprint(fingerprints_data)
    fingerprints_data = calculate_risk_score(fingerprints_data)

    fingerprints_data['created_at'] = pd.to_datetime(fingerprints_data['created_at']).dt.strftime("%Y-%m-%d %H:%M:%S")

    fingerprints_data = fingerprints_data.rename(columns={
        "user_agent": "Navigateur",
        "ip_address": "Adresse IP",
        "screen_resolution": "R\u00e9solution \u00c9cran",
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

    st.subheader("\ud83d\udcc9 Empreintes Num\u00e9riques")
    st.dataframe(fingerprints_data[["Date & Heure", "Adresse IP", "Navigateur", "R\u00e9solution \u00c9cran", "Fuseau Horaire",
                                    "Langue", "Pays IP", "Pays Livraison", "Remboursements", "Tentatives Paiement", 
                                    "Empreinte Unique", "Score de Risque"]])

# \ud83d\udccc Transformer et afficher les transactions
if not transactions_data.empty:
    transactions_data['created_at'] = pd.to_datetime(transactions_data['created_at']).dt.strftime("%Y-%m-%d %H:%M:%S")

    transactions_data = transactions_data.rename(columns={
        "user_agent": "Navigateur",
        "ip_address": "Adresse IP",
        "screen_resolution": "R\u00e9solution \u00c9cran",
        "timezone": "Fuseau Horaire",
        "language": "Langue",
        "transaction_type": "Type Transaction",
        "amount": "Montant",
        "created_at": "Date & Heure"
    })

    st.subheader("\ud83d\udcb3 Transactions")
    st.dataframe(transactions_data[["Date & Heure", "Adresse IP", "Navigateur", "R\u00e9solution \u00c9cran", "Fuseau Horaire",
                                    "Langue", "Type Transaction", "Montant"]])
