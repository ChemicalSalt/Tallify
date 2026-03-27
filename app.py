from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from dotenv import load_dotenv
from auth import init_oauth, login_required
from werkzeug.middleware.proxy_fix import ProxyFix
from db import get_or_create_user, save_expense, get_expenses, delete_expense, update_budget, update_category_budgets
from datetime import datetime
import calendar
import logging
import os

load_dotenv()

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.secret_key = os.getenv('SECRET_KEY')
app.config['GOOGLE_CLIENT_ID'] = os.getenv('GOOGLE_CLIENT_ID')
app.config['GOOGLE_CLIENT_SECRET'] = os.getenv('GOOGLE_CLIENT_SECRET')
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

logging.basicConfig(level=logging.DEBUG)

google = init_oauth(app)


def get_shared_context(user, expenses):
    """Compute all the shared stats used across pages."""
    now = datetime.utcnow()
    current_month = now.strftime('%Y-%m')
    current_year = now.strftime('%Y')

    monthly_expenses = [e for e in expenses if e['date'].startswith(current_month)]
    yearly_expenses = [e for e in expenses if e['date'].startswith(current_year)]

    monthly_total = sum(e['amount'] for e in monthly_expenses)
    yearly_total = sum(e['amount'] for e in yearly_expenses)
    monthly_expense_count = len(monthly_expenses)

    day_of_month = now.day
    daily_avg = monthly_total / day_of_month if day_of_month > 0 else 0

    days_in_month = calendar.monthrange(now.year, now.month)[1]
    days_left = days_in_month - now.day

    cat_totals_month = {}
    for e in monthly_expenses:
        cat_totals_month[e['category']] = cat_totals_month.get(e['category'], 0) + e['amount']
    top_category = max(cat_totals_month, key=cat_totals_month.get) if cat_totals_month else None

    # All-time category totals
    category_totals = {}
    for e in expenses:
        category_totals[e['category']] = category_totals.get(e['category'], 0) + e['amount']

    return {
        'monthly_total': monthly_total,
        'yearly_total': yearly_total,
        'monthly_expense_count': monthly_expense_count,
        'daily_avg': daily_avg,
        'days_left': days_left,
        'top_category': top_category,
        'category_totals': category_totals,
        'now_month': now.strftime('%B %Y'),
        'current_month': current_month,
        'monthly_budget': float(session['user'].get('monthly_budget', 0) or 0),
        'yearly_budget': float(session['user'].get('yearly_budget', 0) or 0),
        'category_budgets': session['user'].get('category_budgets', {}),
    }


@app.route('/')
@login_required
def index():
    return redirect(url_for('budget'))


@app.route('/budget')
@login_required
def budget():
    user = session['user']
    expenses = get_expenses(user['google_id'])
    for e in expenses:
        e['_id'] = str(e['_id'])
    ctx = get_shared_context(user, expenses)
    return render_template('budget.html', user=user, **ctx)


@app.route('/expenses')
@login_required
def expenses():
    user = session['user']
    expense_list = get_expenses(user['google_id'])
    for e in expense_list:
        e['_id'] = str(e['_id'])
    ctx = get_shared_context(user, expense_list)
    return render_template('expenses.html', user=user, expenses=expense_list, **ctx)


@app.route('/login')
def login():
    if 'user' in session:
        return redirect(url_for('budget'))
    return render_template('login.html')


@app.route('/auth/google')
def google_login():
    redirect_uri = url_for('google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)


@app.route('/auth/google/callback')
def google_callback():
    try:
        token = google.authorize_access_token()
        userinfo = token['userinfo']
        user = get_or_create_user(
            google_id=userinfo['sub'],
            name=userinfo['name'],
            email=userinfo['email'],
            picture=userinfo.get('picture', '')
        )
        session['user'] = {
            'google_id': userinfo['sub'],
            'name': userinfo['name'],
            'email': userinfo['email'],
            'picture': userinfo.get('picture', ''),
            'monthly_budget': user.get('monthly_budget', 0),
            'yearly_budget': user.get('yearly_budget', 0),
            'category_budgets': user.get('category_budgets', {}),
        }
        return redirect(url_for('budget'))
    except Exception as e:
        import traceback
        return f"<pre>ERROR:\n{traceback.format_exc()}</pre>", 500


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        user = session['user']
        save_expense(
            user_id=user['google_id'],
            amount=request.form['amount'],
            category=request.form['category'],
            note=request.form['note'],
            date=request.form['date']
        )
        return redirect(url_for('expenses'))
    return render_template('add.html')


@app.route('/delete/<expense_id>', methods=['POST'])
@login_required
def delete(expense_id):
    delete_expense(expense_id)
    return redirect(url_for('expenses'))


@app.route('/stats')
@login_required
def stats():
    user = session['user']
    expense_list = get_expenses(user['google_id'])
    for e in expense_list:
        e['_id'] = str(e['_id'])
    ctx = get_shared_context(user, expense_list)

    categories = {}
    monthly = {}
    for e in expense_list:
        categories[e['category']] = categories.get(e['category'], 0) + e['amount']
        month = e['date'][:7]
        monthly[month] = monthly.get(month, 0) + e['amount']

    return render_template('stats.html',
                           user=user,
                           expenses=expense_list,
                           categories=categories,
                           monthly=monthly,
                           **ctx)


@app.route('/budget', methods=['POST'])
@login_required
def set_budget():
    monthly_budget = request.form.get('monthly_budget', 0)
    yearly_budget = request.form.get('yearly_budget', 0)
    update_budget(session['user']['google_id'], monthly_budget, yearly_budget)
    user_data = dict(session['user'])
    user_data['monthly_budget'] = float(monthly_budget or 0)
    user_data['yearly_budget'] = float(yearly_budget or 0)
    session['user'] = user_data
    session.modified = True
    return redirect(url_for('budget'))


@app.route('/category-budgets', methods=['POST'])
@login_required
def set_category_budgets():
    categories_list = ['Food', 'Transport', 'Shopping', 'Health', 'Entertainment', 'Bills', 'Education', 'Other']
    cat_budgets = {}
    for cat in categories_list:
        val = request.form.get(f'cat_{cat}', '')
        if val:
            cat_budgets[cat] = float(val)
    update_category_budgets(session['user']['google_id'], cat_budgets)
    user_data = dict(session['user'])
    user_data['category_budgets'] = cat_budgets
    session['user'] = user_data
    session.modified = True
    return redirect(url_for('budget'))


@app.route('/ping')
def ping():
    return jsonify({"status": "alive"})


@app.errorhandler(500)
def internal_error(error):
    import traceback
    return f"<pre>{traceback.format_exc()}</pre>", 500


if __name__ == '__main__':
    app.run(debug=True)