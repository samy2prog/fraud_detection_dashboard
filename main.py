from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, MetaData, Table, Column, String, Float, DateTime, text
from sqlalchemy.exc import SQLAlchemyError
from fastapi.middleware.cors import CORSMiddleware
import uuid
from datetime import datetime

# 📌 Connexion à la base de données PostgreSQL (NeonDB)
DATABASE_URL = "postgresql://neondb_owner:npg_KXoDg7AWT1yF@ep-late-mouse-a25ew7xn-pooler.eu-central-1.aws.neon.tech/neondb?sslmode=require"
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# 📌 Initialisation de l'application FastAPI
app = FastAPI()

# 📌 Configuration CORS pour accepter les requêtes de site1bis
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tu peux restreindre à ["https://site1bis.onrender.com"] pour plus de sécurité
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 📌 Définition du modèle pour la collecte des empreintes numériques
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

# 📌 Définition du modèle pour les transactions
class Transaction(BaseModel):
    user_agent: str
    ip_address: str
    timezone: str
    screen_resolution: str
    language: str
    transaction_type: str
    amount: float

# 📌 Vérification et création de la table `transactions`
metadata = MetaData()
transactions_table = Table(
    "transactions", metadata,
    Column("id", String, primary_key=True),
    Column("user_agent", String),
    Column("ip_address", String),
    Column("timezone", String),
    Column("screen_resolution", String),
    Column("language", String),
    Column("transaction_type", String),
    Column("amount", Float),
    Column("created_at", DateTime, default=datetime.utcnow)
)

metadata.create_all(engine)

# 📌 Endpoint pour collecter l'empreinte numérique
@app.post("/collect_fingerprint/")
async def collect_fingerprint(fingerprint: UserFingerprint):
    try:
        user_id = str(uuid.uuid4())  # Génération d'un identifiant unique
        query = text("""
            INSERT INTO user_fingerprints (id, user_agent, ip_address, timezone, screen_resolution,
                                           language, account_age, average_refund_time, payment_attempts,
                                           country_ip, country_shipping, created_at)
            VALUES (:id, :user_agent, :ip_address, :timezone, :screen_resolution, :language,
                    :account_age, :average_refund_time, :payment_attempts, :country_ip, :country_shipping, NOW())
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

# 📌 Endpoint pour enregistrer une transaction
@app.post("/transaction/")
async def record_transaction(transaction: Transaction):
    try:
        transaction_id = str(uuid.uuid4())  # Génération d'un identifiant unique
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

# 📌 Endpoint pour récupérer toutes les empreintes numériques
@app.get("/fingerprints/")
async def get_fingerprints():
    try:
        query = text("SELECT * FROM user_fingerprints")
        with engine.connect() as conn:
            fingerprints = conn.execute(query).fetchall()
        return {"data": [dict(row) for row in fingerprints]}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération: {str(e)}")

# 📌 Endpoint pour récupérer toutes les transactions
@app.get("/transactions/")
async def get_transactions():
    try:
        query = text("SELECT * FROM transactions")
        with engine.connect() as conn:
            transactions = conn.execute(query).fetchall()
        return {"data": [dict(row) for row in transactions]}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération: {str(e)}")
