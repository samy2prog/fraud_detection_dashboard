from fastapi import FastAPI, HTTPException
import psycopg2
from psycopg2.extras import RealDictCursor
import uuid
from pydantic import BaseModel
import os

# Initialisation de l'application FastAPI
app = FastAPI()

# Connexion à la base de données PostgreSQL (NeonDB)
DATABASE_URL = "postgresql://neondb_owner:npg_KXoDg7AWT1yF@ep-late-mouse-a25ew7xn-pooler.eu-central-1.aws.neon.tech/neondb?sslmode=require"

def get_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de connexion à la base de données: {e}")

# Modèle Pydantic pour validation des entrées
class UserFingerprint(BaseModel):
    user_agent: str
    ip_address: str
    timezone: str
    screen_resolution: str
    language: str
    account_age: int = 0
    average_refund_time: float = 0.0
    payment_attempts: int = 0
    country_ip: str = "unknown"
    country_shipping: str = "unknown"

@app.post("/collect_fingerprint/")
def collect_fingerprint(fingerprint: UserFingerprint):
    user_id = str(uuid.uuid4())
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO user_fingerprints (id, user_agent, ip_address, timezone, screen_resolution, language, 
                                           account_age, average_refund_time, payment_attempts, country_ip, country_shipping)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (user_id, fingerprint.user_agent, fingerprint.ip_address, fingerprint.timezone, fingerprint.screen_resolution, 
               fingerprint.language, fingerprint.account_age, fingerprint.average_refund_time, fingerprint.payment_attempts, 
               fingerprint.country_ip, fingerprint.country_shipping))
        conn.commit()
        return {"message": "Fingerprint stored successfully", "user_id": user_id}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'enregistrement: {e}")
    finally:
        cursor.close()
        conn.close()

@app.get("/fingerprints/")
def get_fingerprints():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM user_fingerprints")
        fingerprints = cursor.fetchall()
        return {"data": [dict(row) for row in fingerprints]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des données: {e}")
    finally:
        cursor.close()
        conn.close()
