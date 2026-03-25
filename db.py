from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI"))
db = client["tally"]

users_col = db["users"]
expenses_col = db["expenses"]

def get_or_create_user(google_id, name, email, picture):
    user = users_col.find_one({"google_id": google_id})
    if not user:
        from models import user_doc
        users_col.insert_one(user_doc(google_id, name, email, picture))
        user = users_col.find_one({"google_id": google_id})
    return user

def save_expense(user_id, amount, category, note, date):
    from models import expense_doc
    expenses_col.insert_one(expense_doc(user_id, amount, category, note, date))

def get_expenses(user_id):
    return list(expenses_col.find(
        {"user_id": user_id},
        sort=[("date", -1)]
    ))

def delete_expense(expense_id):
    from bson import ObjectId
    expenses_col.delete_one({"_id": ObjectId(expense_id)})

def update_budget(user_id, budget):
    users_col.update_one(
        {"google_id": user_id},
        {"$set": {"monthly_budget": float(budget)}}
    )