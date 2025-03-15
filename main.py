from fastapi import FastAPI
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
import uuid
from datetime import datetime

# Création de l'application FastAPI
app = FastAPI()

# Connexion à la base de données PostgreSQL
conn = psycopg2.connect(
    dbname="fraud_detection",
    user="fraud_admin",
    password="password",
    host="localhost",
    port="5432",
    cursor_factory=RealDictCursor
)
cursor = conn.cursor()

# Création de la table des empreintes utilisateur si elle n'existe pas
cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_fingerprints (
        id UUID PRIMARY KEY,
        user_agent TEXT,
        ip_address TEXT,
        timezone TEXT,
        screen_resolution TEXT,
        language TEXT,
        account_age INT DEFAULT 0,
        average_refund_time FLOAT DEFAULT 0.0,
        payment_attempts INT DEFAULT 0,
        country_ip TEXT DEFAULT 'unknown',
        country_shipping TEXT DEFAULT 'unknown',
        refund_count INT DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()

# Modèle de données pour l'empreinte utilisateur
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
    refund_count: int

# Endpoint pour enregistrer une empreinte utilisateur
@app.post("/collect_fingerprint/")
def collect_fingerprint(fingerprint: UserFingerprint):
    user_id = str(uuid.uuid4())  # Générer un identifiant unique
    created_at = datetime.utcnow()
    cursor.execute('''
        INSERT INTO user_fingerprints (id, user_agent, ip_address, timezone, screen_resolution, language, 
            account_age, average_refund_time, payment_attempts, country_ip, country_shipping, refund_count, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', (user_id, fingerprint.user_agent, fingerprint.ip_address, fingerprint.timezone, 
          fingerprint.screen_resolution, fingerprint.language,
          fingerprint.account_age, fingerprint.average_refund_time,
          fingerprint.payment_attempts, fingerprint.country_ip, fingerprint.country_shipping, fingerprint.refund_count, created_at))
    conn.commit()
    return {"message": "Fingerprint stored successfully", "user_id": user_id, "created_at": created_at}

# Endpoint pour récupérer les empreintes utilisateur
@app.get("/fingerprints/")
def get_fingerprints():
    cursor.execute("SELECT id, user_agent, ip_address, screen_resolution, timezone, language, refund_count, payment_attempts, country_ip, country_shipping, created_at FROM user_fingerprints")
    fingerprints = cursor.fetchall()
    return {"data": fingerprints}

