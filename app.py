from datetime import datetime
import os

from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd
from getUserData import User
from db import db

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# db = SQL("sqlite:///finance.db")

if __name__ == "__main__":
    extra_files = [os.path.join(app.root_path, 'templates')]  # Monitor templates directory
    os.environ["FLASK_RUN_EXTRA_FILES"] = " ".join(extra_files)

    # Run the Flask app with hot reload
    app.run(debug=True)

    # Configure CS50 Library to use SQLite database

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response
            
@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    userData = User(session.get("user_id"))
        
    return render_template(
        "index.html", 
        portifolio=userData.getPortifolio(), 
        cash=userData.getCash(),
        general_total = userData.getGeneralTotal()
    )


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    if request.method == "GET":
        return render_template("buy.html")
    else:
        date = datetime.now()
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")       
        quote = lookup(symbol)
        totalPrice = float(quote["price"]) * int(shares)
        
        user = {}
        user["id"] = session.get("user_id")
        user["cash"] = float(db.execute("select cash from users where id = ?;", user["id"])[0]["cash"])
        
        if quote == "None" or not shares.isdigit() or int(shares) <= 0:
            return apology("Preencha corretamente o formulário")
        elif user["cash"] < totalPrice:
            return apology("insufficient founds")
        else:
            db.execute(
                """
                INSERT INTO purchases(symbol, shares, day, month, year, hour, minute, total_price, user_id)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                symbol,
                shares,
                date.day,
                date.month,
                date.year,
                date.hour,
                date.minute,
                totalPrice,
                user["id"]
            )
            
            db.execute(
                """
                UPDATE users
                SET cash = ?
                WHERE id = ?
                """,
                user["cash"] - totalPrice,
                user["id"]
            )
            return redirect("/?buy=success")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    history = User(session.get("user_id")).getHistory()
    return render_template("history.html", history=history)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()
    
    username = request.form.get("username")
    password = request.form.get("password")
    
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not username:
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not password:
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", username
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], password
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    if request.method == 'GET':
        return render_template('quote.html')
    else:
        symbol = request.form.get("symbol")
        quoted = lookup(symbol)
        print(quoted)
        if not quoted:
            return apology("Symbol not exist", 400)
        else:
            return render_template("quoted.html", quoted=quoted)
            


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmPassword = request.form.get("confirmPassword")
        print(username, password, confirmPassword)
        
        if not username or not password or not confirmPassword or password != confirmPassword:
            return apology("invalid username and/or password", 403)
        
        db.execute("INSERT INTO users(username, hash) VALUES(?, ?);", username, generate_password_hash(password))
        return redirect("/login")
    else:
        return render_template("register.html")
        


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    if request.method == "GET":
        return render_template("sell.html")
    else:
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")
        quote = lookup(symbol)
        date = datetime.now()
        totalPrice = float(quote["price"]) * int(shares)
        operation = 'sell'
        
        userId = session.get("user_id")
        user = User(userId)
        portifolio = user.getPortifolio()
        
        if not symbol or not shares or not quote:
            return apology("Ação inválida")
        if not symbol in portifolio:
            return apology("Você não possui essa ação em seu portifolio")
        if int(shares) > portifolio[symbol]["qtde"]:
            return apology("Você não possui essa quantidade dessa ação")
        
        db.execute(
            """
            INSERT INTO purchases(symbol, shares, total_price, operation, minute, hour, day, month, year, user_id)
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            symbol,
            shares,
            totalPrice,
            operation,
            date.minute,
            date.hour,
            date.day,
            date.month,
            date.year,
            userId
        )
        
        db.execute(
            """
            UPDATE users
            SET cash = ?
            WHERE id = ?
            """,
            user.getCash() + totalPrice,
            userId
        )
        return redirect("/")


