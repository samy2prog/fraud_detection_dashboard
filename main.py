from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel
import uuid

# Connexion à la base de données PostgreSQL (Supabase)
DATABASE_URL = "postgresql://neondb_owner:npg_KXoDg7AWT1yF@ep-late-mouse-a25ew7xn-pooler.eu-central-1.aws.neon.tech/neondb?sslmode=require"
# Configuration de SQLAlchemy
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

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
    query = text('''
        INSERT INTO user_fingerprints (id, user_agent, ip_address, timezone, screen_resolution, language, 
        account_age, average_refund_time, payment_attempts, country_ip, country_shipping)
        VALUES (:id, :user_agent, :ip_address, :timezone, :screen_resolution, :language, 
                :account_age, :average_refund_time, :payment_attempts, :country_ip, :country_shipping)
    ''')
    
    db.execute(query, {
        "id": user_id,
        "user_agent": fingerprint.user_agent,
        "ip_address": fingerprint.ip_address,
        "timezone": fingerprint.timezone,
        "screen_resolution": fingerprint.screen_resolution,
        "language": fingerprint.language,
        "account_age": fingerprint.account_age,
        "average_refund_time": fingerprint.average_refund_time,
        "payment_attempts": fingerprint.payment_attempts,
        "country_ip": fingerprint.country_ip,
        "country_shipping": fingerprint.country_shipping
    })
    db.commit()
    return {"message": "Fingerprint stored successfully", "user_id": user_id}

# Endpoint pour récupérer toutes les empreintes numériques
@app.get("/fingerprints/")
def get_fingerprints():
    query = text("SELECT * FROM user_fingerprints")
    result = db.execute(query)
    fingerprints = result.fetchall()
    return {"data": [dict(row) for row in fingerprints]}

# Vérification de l'état de l'API
@app.get("/")
def root():
    return {"message": "Fraud Detection API is running"}
