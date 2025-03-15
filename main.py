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
    allow_origins=["*"],  # À restreindre pour plus de sécurité si nécessaire
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

# 📌 Endpoint pour collecter l'empreinte numérique
@app.post("/collect_fingerprint/")
async def collect_fingerprint(fingerprint: UserFingerprint):
    try:
        user_fingerprint_id = str(uuid.uuid4())  # Génération d'un identifiant unique
        query = text("""
            INSERT INTO user_fingerprints (id, user_agent, ip_address, timezone, screen_resolution,
                                           language, account_age, average_refund_time, payment_attempts,
                                           country_ip, country_shipping, created_at)
            VALUES (:id, :user_agent, :ip_address, :timezone, :screen_resolution, :language,
                    :account_age, :average_refund_time, :payment_attempts, :country_ip, :country_shipping, NOW())
        """)
        with engine.connect() as conn:
            conn.execute(query, {
                "id": user_fingerprint_id,
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
        return {"message": "Fingerprint stored successfully", "user_fingerprint_id": user_fingerprint_id}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'enregistrement: {str(e)}")

# 📌 Endpoint pour enregistrer une transaction
@app.post("/transaction/")
async def record_transaction(transaction: Transaction):
    try:
        # Trouver l'empreinte correspondant à l'IP et au User-Agent
        search_query = text("""
            SELECT id FROM user_fingerprints 
            WHERE ip_address = :ip_address AND user_agent = :user_agent
            ORDER BY created_at DESC LIMIT 1
        """)
        with engine.connect() as conn:
            result = conn.execute(search_query, {
                "ip_address": transaction.ip_address,
                "user_agent": transaction.user_agent
            }).fetchone()

        if result is None:
            raise HTTPException(status_code=404, detail="Empreinte numérique non trouvée pour cette transaction")

        user_fingerprint_id = result[0]

        transaction_id = str(uuid.uuid4())  # Génération d'un identifiant unique
        insert_query = text("""
            INSERT INTO transactions (
                id, user_fingerprint_id, user_agent, ip_address, timezone, screen_resolution, language, 
                transaction_type, amount, created_at
            ) VALUES (
                :id, :user_fingerprint_id, :user_agent, :ip_address, :timezone, :screen_resolution, :language,
                :transaction_type, :amount, NOW()
            )
        """)
        with engine.connect() as conn:
            conn.execute(insert_query, {
                "id": transaction_id,
                "user_fingerprint_id": user_fingerprint_id,
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

# 📌 Endpoint pour récupérer toutes les empreintes numériques avec les remboursements et transactions associés
@app.get("/fingerprints/")
async def get_fingerprints():
    try:
        query = text("""
            SELECT uf.id, uf.user_agent, uf.ip_address, uf.screen_resolution, uf.timezone, uf.language, 
                   uf.payment_attempts, uf.country_ip, uf.country_shipping, uf.created_at, 
                   COALESCE(SUM(CASE WHEN t.transaction_type = 'refund' THEN 1 ELSE 0 END), 0) AS refund_count,
                   COALESCE(SUM(t.amount), 0) AS total_spent,
                   COUNT(t.id) AS total_transactions
            FROM user_fingerprints uf
            LEFT JOIN transactions t ON uf.id = t.user_fingerprint_id
            GROUP BY uf.id
        """)
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
