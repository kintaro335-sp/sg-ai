
from fastapi import HTTPException, status
from variables_env import MONGO_DATABASE
from datetime import datetime as dt
from db.mongo.mongo_generic_repository import MongoGenericRepository

wallets = MongoGenericRepository(MONGO_DATABASE, "wallets")

transactions = MongoGenericRepository(MONGO_DATABASE, "transactions")


errors_http = {
  "wallet_already_exists": HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Wallet already exists"),
  "wallet_not_found": HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found"),
  "transaction_not_found": HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"),
  "not_enough_credits": HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not enough credits")
}

class WalletService:

  def init_wallet(self, user_id: str):
    wallet = wallets.get_by_query({"user_id": user_id})
    if wallet != None:
      raise errors_http["wallet_already_exists"]
    wallets.add({"user_id": user_id, "balance": 0})
    return {"message": "Wallet created"}


  def get_balance(self, user_id: str) -> int:
    wallet = wallets.get_by_query({"user_id": user_id})
    if wallet == None:
      raise errors_http["wallet_not_found"]
    return wallet["balance"]

  def add_credit(self, user_id: str, amount: int):
    wallet = wallets.get_by_query({"user_id": user_id})
    if wallet == None:
      raise errors_http["wallet_not_found"]
    wallets.update_by_query({"user_id": user_id}, {"$inc": {"balance": amount }})
    transactions.add({"user_id": user_id, "amount": amount, "type": "add"})

  def charge_credit(self, user_id: str, amount: int):
    wallet = wallets.get_by_query({"user_id": user_id})
    if wallet == None:
      raise errors_http["wallet_not_found"]
    wallets.update_by_query({"user_id": user_id}, {"$inc": {"balance": (amount*-1) }})
    transactions.add({"user_id": user_id, "amount": amount, "type": "charge", "date": dt.now()})

  def get_transactions(self, user_id: str, page: int = 0, limit: int = 20):
    skip = page * limit
    docs_raw = transactions.get_all({"user_id": user_id}, skip=skip, limit=limit)
    docs = []
    for doc in docs_raw:
      doc['_id'] = str(doc['_id'])
      docs.append(doc)
    return docs

wallet_service = WalletService()
