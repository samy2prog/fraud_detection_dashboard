import streamlit as st
import pandas as pd
import requests
from sqlalchemy import create_engine
import hashlib
import os

# Connexion à la base de données PostgreSQL
DATABASE_URL = "postgresql://fraud_admin:password@localhost:5432/fraud_detection"
engine = create_engine(DATABASE_URL)

# Charger les données de la base PostgreSQL
def load_data():
    query = """
        SELECT user_agent, ip_address, screen_resolution, timezone, language, 
               refund_count, payment_attempts, country_ip, country_shipping, created_at
        FROM user_fingerprints
    """
    df = pd.read_sql(query, engine)
    return df

# Générer un identifiant unique basé sur plusieurs caractéristiques
def generate_fingerprint(df):
    df['fingerprint'] = df.apply(lambda row: hashlib.sha256(
        (row['user_agent'] + row['screen_resolution'] + row['timezone'] + row['ip_address']).encode()
    ).hexdigest(), axis=1)
    return df

# Calcul du risk score
def calculate_risk_score(df):
    df['risk_score'] = 0
    
    # Score basé sur le nombre d'IP pour une même empreinte
    df['ip_count'] = df.groupby('fingerprint')['ip_address'].transform('nunique')
    df['risk_score'] += df['ip_count'] * 10
    
    # Score basé sur le nombre d'empreintes pour une même IP
    df['fingerprint_count'] = df.groupby('ip_address')['fingerprint'].transform('nunique')
    df['risk_score'] += df['fingerprint_count'] * 10
    
    # Vérification de la présence de remboursement
    if 'refund_count' in df.columns:
        df['refund_requests'] = df.groupby('fingerprint')['refund_count'].transform('sum')
        df['risk_score'] += df['refund_requests'] * 15
    
    # Score basé sur le nombre de tentatives de paiement
    df['risk_score'] += df['payment_attempts'] * 5
    
    # Score basé sur l'incohérence entre pays IP et pays de livraison
    df['risk_score'] += df.apply(lambda row: 25 if row['country_ip'] != row['country_shipping'] else 0, axis=1)
    
    # Score basé sur la récidive d'une empreinte utilisateur
    df['fingerprint_recurrence'] = df.groupby('fingerprint')['ip_address'].transform('count')
    df['risk_score'] += df['fingerprint_recurrence'] * 8
    
    # Normalisation du score entre 0 et 100
    df['risk_score'] = df['risk_score'].clip(0, 100)
    
    return df

# Interface Streamlit
st.title("Fraud Detection Dashboard")

st.write("Ce tableau de bord affiche les empreintes numériques et un score de risque calculé en fonction des activités suspectes.")

data = load_data()
data = generate_fingerprint(data)
data = calculate_risk_score(data)

# Convertir la date pour un affichage clair
data['created_at'] = pd.to_datetime(data['created_at']).dt.strftime("%Y-%m-%d %H:%M:%S")

# Renommer et réorganiser les colonnes
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

columns_order = ["Date & Heure", "Adresse IP", "Navigateur", "Résolution Écran", "Fuseau Horaire",
                 "Langue", "Pays IP", "Pays Livraison", "Remboursements", "Tentatives Paiement", "Score de Risque", "Empreinte Unique"]

st.dataframe(data[columns_order])
