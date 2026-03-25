from datetime import datetime

def expense_doc(user_id, amount, category, note, date):
    return {
        "user_id": user_id,
        "amount": float(amount),
        "category": category,
        "note": note,
        "date": date,
        "created_at": datetime.utcnow()
    }

def user_doc(google_id, name, email, picture):
    return {
        "google_id": google_id,
        "name": name,
        "email": email,
        "picture": picture,
        "monthly_budget": 0,
        "created_at": datetime.utcnow()
    }