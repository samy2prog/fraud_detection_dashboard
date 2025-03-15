from fastapi import FastAPI, HTTPException
import psycopg2
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel
import uuid

# Connexion à la base de données PostgreSQL (Supabase)
DATABASE_URL = "postgresql://postgres:XGXgDGiGuhzbnfFH@db.yawimpxwrcadpsizozfp.supabase.co:5432/postgres"

conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
cursor = conn.cursor()

# Création de l'application FastAPI
app = FastAPI()

# Définition du modèle des empreintes utilisateur
class UserFingerprint(BaseModel):
    user_agent: str
    ip_address: str
    timezone: str
    screen_resolution: str
    language: str
    account_age: int
    average_refund_time: float
    payment_attempts: int
    country_ip: str
    country_shipping: str

# Endpoint pour collecter une empreinte numérique
@app.post("/collect_fingerprint/")
def collect_fingerprint(fingerprint: UserFingerprint):
    user_id = str(uuid.uuid4())
    cursor.execute('''
        INSERT INTO user_fingerprints (id, user_agent, ip_address, timezone, screen_resolution, language, 
        account_age, average_refund_time, payment_attempts, country_ip, country_shipping)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', (user_id, fingerprint.user_agent, fingerprint.ip_address, fingerprint.timezone, 
          fingerprint.screen_resolution, fingerprint.language, fingerprint.account_age, 
          fingerprint.average_refund_time, fingerprint.payment_attempts, fingerprint.country_ip, fingerprint.country_shipping))
    conn.commit()
    return {"message": "Fingerprint stored successfully", "user_id": user_id}

# Endpoint pour récupérer toutes les empreintes numériques
@app.get("/fingerprints/")
def get_fingerprints():
    cursor.execute("SELECT * FROM user_fingerprints")
    fingerprints = cursor.fetchall()
    return {"data": fingerprints}

# Vérification de l'état de l'API
@app.get("/")
def root():
    return {"message": "Fraud Detection API is running"}
