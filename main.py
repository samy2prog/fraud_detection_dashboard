import uuid
from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel
import os

# Connexion à la base de données PostgreSQL (NeonDB)
DATABASE_URL = "postgresql://neondb_owner:npg_KXoDg7AWT1yF@ep-late-mouse-a25ew7xn-pooler.eu-central-1.aws.neon.tech/neondb?sslmode=require"
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Définition du modèle de données pour les empreintes numériques
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

# Définition du modèle de transaction
class Transaction(BaseModel):
    fingerprint: str
    transaction_type: str
    amount: float

app = FastAPI()

# Endpoint pour collecter les empreintes numériques
@app.post("/collect_fingerprint/")
async def collect_fingerprint(fingerprint: UserFingerprint):
    try:
        user_id = str(uuid.uuid4())  # Génération d'un identifiant unique
        with engine.connect() as conn:
            # Récupération du nombre de remboursements pour cette empreinte
            refund_count_query = text("""
                SELECT COUNT(*) FROM transactions 
                WHERE fingerprint = :fingerprint AND transaction_type = 'refund'
            """)
            refund_count = conn.execute(refund_count_query, {"fingerprint": fingerprint.ip_address}).scalar()

            # Insertion de l'empreinte numérique avec le nombre de remboursements
            query = text("""
                INSERT INTO user_fingerprints (id, user_agent, ip_address, timezone, screen_resolution,
                                               language, account_age, average_refund_time, payment_attempts,
                                               country_ip, country_shipping, refund_requests)
                VALUES (:id, :user_agent, :ip_address, :timezone, :screen_resolution, :language,
                        :account_age, :average_refund_time, :payment_attempts, :country_ip, :country_shipping, :refund_requests)
            """)
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
                "country_shipping": fingerprint.country_shipping,
                "refund_requests": refund_count
            })
            conn.commit()
        return {"message": "Fingerprint stored successfully", "user_id": user_id}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'enregistrement: {str(e)}")

# Endpoint pour enregistrer une transaction
@app.post("/transaction/")
async def store_transaction(transaction: Transaction):
    try:
        transaction_id = str(uuid.uuid4())
        with engine.connect() as conn:
            query = text("""
                INSERT INTO transactions (id, fingerprint, transaction_type, amount)
                VALUES (:id, :fingerprint, :transaction_type, :amount)
            """)
            conn.execute(query, {
                "id": transaction_id,
                "fingerprint": transaction.fingerprint,
                "transaction_type": transaction.transaction_type,
                "amount": transaction.amount
            })
            conn.commit()
        return {"message": "Transaction enregistrée avec succès", "transaction_id": transaction_id}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'enregistrement de la transaction: {str(e)}")
