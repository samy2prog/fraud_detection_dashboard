import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import hashlib

# ✅ Connexion à la base de données PostgreSQL (NeonDB)
DATABASE_URL = "postgresql://neondb_owner:npg_KXoDg7AWT1yF@ep-late-mouse-a25ew7xn-pooler.eu-central-1.aws.neon.tech/neondb?sslmode=require"

try:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    conn = engine.connect()
    conn.close()
    st.success("✅ Connexion à la base de données établie avec succès !")
except Exception as e:
    st.error(f"❌ Erreur de connexion à la base de données : {e}")

# ✅ Charger les données de la base PostgreSQL
def load_data():
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
        st.error(f"❌ Erreur lors du chargement des données : {e}")
        return pd.DataFrame()

# ✅ Générer un identifiant unique basé sur plusieurs caractéristiques
def generate_fingerprint(df):
    if not df.empty:
        df['fingerprint'] = df.apply(lambda row: hashlib.sha256(
            (row['user_agent'] + row['screen_resolution'] + row['timezone'] + row['ip_address']).encode()
        ).hexdigest(), axis=1)
    return df

# ✅ Calcul du Risk Score
def calculate_risk_score(df):
    if df.empty:
        return df
    
    df['risk_score'] = 0
    
    # 🎯 Score basé sur le nombre d'IP pour une même empreinte
    df['ip_count'] = df.groupby('fingerprint')['ip_address'].transform('nunique')
    df['risk_score'] += df['ip_count'] * 10
    
    # 🎯 Score basé sur le nombre d'empreintes pour une même IP
    df['fingerprint_count'] = df.groupby('ip_address')['fingerprint'].transform('nunique')
    df['risk_score'] += df['fingerprint_count'] * 10
    
    # 🎯 Vérification des demandes de remboursement
    if 'refund_count' in df.columns:
        df['refund_requests'] = df.groupby('fingerprint')['refund_count'].transform('sum')
        df['risk_score'] += df['refund_requests'] * 15
    
    # 🎯 Nombre de tentatives de paiement
    df['risk_score'] += df['payment_attempts'] * 5
    
    # 🎯 Incohérence entre pays IP et pays de livraison
    df['risk_score'] += df.apply(lambda row: 25 if row['country_ip'] != row['country_shipping'] else 0, axis=1)
    
    # 🎯 Score basé sur la récidive d'une empreinte utilisateur
    df['fingerprint_recurrence'] = df.groupby('fingerprint')['ip_address'].transform('count')
    df['risk_score'] += df['fingerprint_recurrence'] * 8
    
    # Normalisation entre 0 et 100
    df['risk_score'] = df['risk_score'].clip(0, 100)
    
    return df

# ✅ Interface Streamlit
st.title("📊 Fraud Detection Dashboard")

st.write("🚨 Ce tableau de bord affiche les empreintes numériques et un **score de risque** basé sur plusieurs facteurs.")

# 🔄 Charger les données et calculer le Risk Score
data = load_data()
data = generate_fingerprint(data)
data = calculate_risk_score(data)

# 📅 Convertir la date pour un affichage clair
if not data.empty:
    data['created_at'] = pd.to_datetime(data['created_at']).dt.strftime("%Y-%m-%d %H:%M:%S")

    # 🏷️ Renommer les colonnes
    data = data.rename(columns={
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

    # 📌 Colonnes à afficher
    columns_order = ["Date & Heure", "Adresse IP", "Navigateur", "Résolution Écran", "Fuseau Horaire",
                     "Langue", "Pays IP", "Pays Livraison", "Remboursements", "Tentatives Paiement", "Empreinte Unique", "Score de Risque"]

    st.dataframe(data[columns_order])

else:
    st.warning("⚠️ Aucune donnée disponible pour le moment.")

