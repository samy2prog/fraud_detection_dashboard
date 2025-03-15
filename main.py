import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel

# Connexion à la base de données PostgreSQL (NeonDB)
DATABASE_URL = "postgresql://neondb_owner:npg_KXoDg7AWT1yF@ep-late-mouse-a25ew7xn-pooler.eu-central-1.aws.neon.tech/neondb?sslmode=require"
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

app = FastAPI()

# Activer CORS pour permettre les requêtes depuis site1
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Autoriser toutes les origines (tu peux restreindre à ton domaine)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# Modèle de données pour les transactions
class Transaction(BaseModel):
    user_agent: str
    ip_address: str
    timezone: str
    screen_resolution: str
    language: str
    transaction_type: str  # purchase ou refund
    amount: float

@app.get("/")
def root():
    return {"message": "Fraud Detection API is running!"}

# Endpoint pour collecter l'empreinte numérique
@app.post("/collect_fingerprint/")
async def collect_fingerprint(fingerprint: UserFingerprint):
    try:
        user_id = str(uuid.uuid4())
        query = text("""
            INSERT INTO user_fingerprints (
                id, user_agent, ip_address, timezone, screen_resolution, language,
                account_age, average_refund_time, payment_attempts, country_ip, country_shipping
            ) VALUES (
                :id, :user_agent, :ip_address, :timezone, :screen_resolution, :language,
                :account_age, :average_refund_time, :payment_attempts, :country_ip, :country_shipping
            )
        """)
        with engine.connect() as conn:
            conn.execute(query, {
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
            conn.commit()
        return {"message": "Fingerprint stored successfully", "user_id": user_id}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'enregistrement: {str(e)}")

# Endpoint pour enregistrer une transaction
@app.post("/transaction/")
async def record_transaction(transaction: Transaction):
    try:
        transaction_id = str(uuid.uuid4())
        query = text("""
            INSERT INTO transactions (
                id, user_agent, ip_address, timezone, screen_resolution, language, 
                transaction_type, amount, created_at
            ) VALUES (
                :id, :user_agent, :ip_address, :timezone, :screen_resolution, :language,
                :transaction_type, :amount, NOW()
            )
        """)
        with engine.connect() as conn:
            conn.execute(query, {
                "id": transaction_id,
                "user_agent": transaction.user_agent,
                "ip_address": transaction.ip_address,
                "timezone": transaction.timezone,
                "screen_resolution": transaction.screen_resolution,
                "language": transaction.language,
                "transaction_type": transaction.transaction_type,
                "amount": transaction.amount
            })
            conn.commit()
        return {"message": "Transaction enregistrée avec succès", "transaction_id": transaction_id}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'enregistrement de la transaction: {str(e)}")

# Endpoint pour récupérer les empreintes numériques
@app.get("/fingerprints/")
def get_fingerprints():
    try:
        query = text("SELECT * FROM user_fingerprints")
        with engine.connect() as conn:
            fingerprints = conn.execute(query).fetchall()
        return {"data": [dict(row) for row in fingerprints]}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des données: {str(e)}")

# Endpoint pour récupérer les transactions
@app.get("/transactions/")
def get_transactions():
    try:
        query = text("SELECT * FROM transactions")
        with engine.connect() as conn:
            transactions = conn.execute(query).fetchall()
        return {"data": [dict(row) for row in transactions]}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des transactions: {str(e)}")
