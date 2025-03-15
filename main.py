from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import uuid

# Configuration de l'API
app = FastAPI()

# Configuration CORS pour autoriser les requêtes depuis le site web (site1)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Met "*" pour tout autoriser ou spécifie ["https://site1bis.onrender.com"]
    allow_credentials=True,
    allow_methods=["*"],  # Permet toutes les méthodes (GET, POST, etc.)
    allow_headers=["*"],  # Autorise tous les headers
)

# Connexion à la base de données PostgreSQL (NeonDB)
DATABASE_URL = "postgresql://neondb_owner:npg_KXoDg7AWT1yF@ep-late-mouse-a25ew7xn-pooler.eu-central-1.aws.neon.tech/neondb?sslmode=require"

# Création de l'engine SQLAlchemy
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Modèle de données pour recevoir les empreintes numériques
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

# Endpoint pour collecter l'empreinte numérique
@app.post("/collect_fingerprint/")
async def collect_fingerprint(fingerprint: UserFingerprint):
    try:
        user_id = str(uuid.uuid4())  # Génération d'un identifiant unique
        query = text("""
            INSERT INTO user_fingerprints (id, user_agent, ip_address, timezone, screen_resolution, language,
                                           account_age, average_refund_time, payment_attempts, country_ip, country_shipping)
            VALUES (:id, :user_agent, :ip_address, :timezone, :screen_resolution, :language,
                    :account_age, :average_refund_time, :payment_attempts, :country_ip, :country_shipping)
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

# Endpoint pour récupérer les empreintes numériques
@app.get("/fingerprints/")
async def get_fingerprints():
    try:
        query = text("SELECT * FROM user_fingerprints")
        with engine.connect() as conn:
            fingerprints = conn.execute(query).fetchall()
        return {"data": [dict(row) for row in fingerprints]}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des données: {str(e)}")

# Endpoint pour enregistrer une transaction
class TransactionData(BaseModel):
    user_agent: str
    ip_address: str
    amount: float
    payment_method: str
    transaction_status: str

@app.post("/transaction/")
async def record_transaction(transaction: TransactionData):
    try:
        transaction_id = str(uuid.uuid4())
        query = text("""
            INSERT INTO transactions (id, user_agent, ip_address, amount, payment_method, transaction_status)
            VALUES (:id, :user_agent, :ip_address, :amount, :payment_method, :transaction_status)
        """)
        with engine.connect() as conn:
            conn.execute(query, {
                "id": transaction_id,
                "user_agent": transaction.user_agent,
                "ip_address": transaction.ip_address,
                "amount": transaction.amount,
                "payment_method": transaction.payment_method,
                "transaction_status": transaction.transaction_status
            })
            conn.commit()
        return {"message": "Transaction enregistrée avec succès", "transaction_id": transaction_id}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'enregistrement de la transaction: {str(e)}")

# Vérification du bon fonctionnement de l'API
@app.get("/")
async def root():
    return {"message": "API de détection de fraude est en ligne !"}

