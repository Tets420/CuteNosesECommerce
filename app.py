import os
import sqlite3
import re

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///cutenoses.db")


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
    """Homepage index"""

    # Check GET method for entering or refreshing page
    if request.method == "GET":
        user_id = session['userID']

        # Query user's name
        user = db.execute("SELECT username FROM users WHERE userID = ?", user_id)
        name = user[0]['username']

        # Query categories for search
        categories = db.execute("SELECT categoryID, name FROM categories")
        category_id = request.args.get('category', None)

        if category_id:
            if category_id == "all":
                products = db.execute("SELECT productID, productname, description, price, quantity, productimageURL FROM products")
            else:
                products = db.execute("SELECT productID, productname, description, price, quantity, productimageURL FROM products WHERE categoryID = ?", category_id)
        else:
            products = db.execute("SELECT productID, productname, description, price, quantity, productimageURL FROM products")

        # Render the index template
        return render_template("index.html", name=name, products=products, categories=categories, selected_category=category_id)


@app.route("/admin", methods=["GET", "POST"])
@login_required
def admin():
    """Admin dashboard for all products and all orders"""
    # Check if the user is an admin
    if not session.get("usercredential") == "admin":
        return apology("You don't have permission to access this page.", 403)

    if request.method == "GET":
        # Query all products
        products = db.execute("SELECT * FROM products")

        # Query all orders
        orders = db.execute("""
            SELECT o.orderID, o.orderDate, u.username, p.productname, o.quantity, o.totalAmount, o.orderStatus
            FROM orders o
            JOIN users u ON o.userID = u.userID
            JOIN products p ON o.productID = p.productID
            ORDER BY o.orderDate DESC
        """)

        return render_template("admin.html", products=products, orders=orders)

    # Add any additional functionality for handling POST requests, if needed

    return apology("Invalid request method", 400)


@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
    """Change user's password"""
    if not session.get("userID"):
        return redirect("/login")

    if request.method == "GET":
        return render_template("changepass.html")

    if request.method == "POST":
        # Get form data
        old_password = request.form.get("old_password")
        new_password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Validate form data
        if not old_password or not new_password or not confirmation:
            return render_template("changepass.html")

        if new_password != confirmation:
            return apology("Passwords don't match")

        # Hash the new password
        hashed_password = generate_password_hash(new_password)

        # Get the current password hash from the database
        current_hash = db.execute("SELECT hash FROM users WHERE id = ?", session["userID"])[0]['hash']

        # Check if the old password matches the current password
        if not check_password_hash(current_hash, old_password):
            return apology("Old password is incorrect")

        try:
            # Update the user's password
            db.execute("UPDATE users SET hash = ? WHERE id = ?", hashed_password, session["userID"])
        except Exception as e:
            return apology(str(e))

        flash("Password changed successfully!")
        return redirect("/")


@app.route("/add_to_cart", methods=["POST"])
@login_required
def add_to_cart():
    """Add a product to the user's cart"""
    # Get the product ID and quantity from the request
    product_id = request.args.get("productID")
    quantity = request.form.get("quantity")
    user_id = session["userID"]

    # Validate form data
    if not product_id or not quantity:
        return apology("Please provide a product ID and quantity.")

    try:
        quantity = int(quantity)
        if quantity <= 0:
            return apology("Quantity must be a positive integer.")
    except ValueError:
        return apology("Invalid quantity value.")

    # Check if the product is already in the user's cart
    existing_cart_item = db.execute(
        "SELECT * FROM shopcart WHERE userID = ? AND productID = ?",
        user_id,
        product_id,
    )

    if existing_cart_item:
        # Update the quantity if the product is already in the cart
        new_quantity = existing_cart_item[0]["quantity"] + quantity
        db.execute(
            "UPDATE shopcart SET quantity = ? WHERE userID = ? AND productID = ?",
            new_quantity,
            user_id,
            product_id,
        )
    else:
        # Add the product to the cart
        db.execute(
            "INSERT INTO shopcart (userID, productID, quantity) VALUES (?, ?, ?)",
            user_id,
            product_id,
            quantity,
        )

    flash("Product added to cart successfully!")
    return redirect("/my_cart")


@app.route("/my_cart")
@login_required
def my_cart():
    """Display the user's cart"""
    if request.method == "GET":
        user_id = session['userID']

        # Get the user's cart items
        cart_items = db.execute(
            """
            SELECT p.productname, p.price, c.quantity, p.productID
            FROM shopcart c
            JOIN products p ON c.productID = p.productID
            WHERE c.userID = ?
            """,
            user_id,
        )

        return render_template("my_cart.html", cart_items=cart_items)


def remove_from_cart(user_id, product_id):
    """Remove a product from the user's cart"""
    db.execute(
        "DELETE FROM shopcart WHERE userID = ? AND productID = ?",
        user_id,
        product_id,
    )


def update_cart_quantity(user_id, product_id, new_quantity):
    """Update the quantity of a product in the user's cart"""
    db.execute(
        "UPDATE shopcart SET quantity = ? WHERE userID = ? AND productID = ?",
        new_quantity,
        user_id,
        product_id,
    )


@app.route("/remove_from_cart", methods=["POST"])
@login_required
def remove_from_cart():
    """Route for removing a product from the user's cart"""

    # Get the product ID from the form data
    product_id = request.form.get("productID")
    user_id = session["userID"]

    # Remove the product from the cart
    remove_from_cart(user_id, product_id)

    # Redirect to the "My Cart" page
    return redirect("/my_cart")


@app.route("/update_cart", methods=["POST"])
@login_required
def update_cart():
    """Route for updating the quantity of a product in the user's cart"""
    # Get the product ID and new quantity from the form data
    product_id = request.form.get("product_id")
    new_quantity = request.form.get("quantity")
    user_id = session["userID"]

    # Update the quantity of the product in the cart
    update_cart_quantity(user_id, product_id, new_quantity)

    # Redirect to the "My Cart" page
    return redirect("/my_cart")


@app.route("/checkout", methods=["POST"])
@login_required
def checkout():
    """Checkout process for the user's cart"""
    user_id = session["userID"]

    # Get the user's cart items
    cart_items = db.execute(
        """
        SELECT p.productID, p.productname, p.price, c.quantity
        FROM shopcart c
        JOIN products p ON c.productID = p.productID
        WHERE c.userID = ?
        """,
        user_id,
    )

    # Get the selected payment method from the form data
    payment_method = request.form.get("payment_method")

    # Calculate the total amount
    total_amount = sum(item["price"] * item["quantity"] for item in cart_items)

    # Get the user's shipping address
    user_shipping_address = db.execute(
        "SELECT shippingAddStreet, shippingAddCity, shippingAddProvince, shippingAddZip FROM users WHERE userID = ?",
        user_id,
    )

    if user_shipping_address:
        shipping_address = f"{user_shipping_address[0]['shippingAddStreet']}, {user_shipping_address[0]['shippingAddCity']}, {user_shipping_address[0]['shippingAddProvince']}, {user_shipping_address[0]['shippingAddZip']}"
    else:
        shipping_address = None

    # Set the payment details based on the selected payment method
    payment_details = None
    if payment_method == "gcash":
        payment_details = "Please send your payment to GCASH number: 9568198521"

    # Process the checkout based on the selected payment method
    if payment_method == "cash_on_delivery":
        # Handle cash on delivery payment
        # will add payment APIs in the future after business is registered
        pass
    elif payment_method == "gcash":
        # Display GCASH number for payment at the checkout screen
        pass

    # Create a new order for each item in the cart
    for item in cart_items:
        db.execute(
            "INSERT INTO orders (userID, productID, quantity, orderStatus, paymentMethod, totalAmount) VALUES (?, ?, ?, 'CheckOut', ?, ?)",
            user_id,
            item["productID"],
            item["quantity"],
            payment_method,
            total_amount,
        )

    # Update the product quantity in the products table
        db.execute(
            "UPDATE products SET quantity = quantity - ? WHERE productID = ?",
            item["quantity"],
            item["productID"],
        )

    # Clear the user's cart
    db.execute("DELETE FROM shopcart WHERE userID = ?", user_id)

    # Render the "Checkout Success" template with the shipping address and payment details
    return render_template("checkout.html", shipping_address=shipping_address, payment_details=payment_details)


@app.route("/history")
@login_required
def history():
    """Show history of orders for the current user"""
    if request.method == "GET":
        user_id = session['userID']

        # Query order history
        orders = db.execute("""
            SELECT o.orderID, o.orderDate, p.productname, o.quantity, o.totalAmount, o.orderStatus
            FROM orders o
            JOIN products p ON o.productID = p.productID
            WHERE o.userID = ?
            ORDER BY o.orderDate DESC
        """, user_id)

        return render_template("history.html", orders=orders)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    # Clear any existing user session
    session.clear()

    if request.method == "POST":
        # Validate form data
        username = request.form.get("username")
        password = request.form.get("password")

        if not username:
            return apology("Please provide a username.")

        if not password:
            return apology("Please provide a password.")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        # Check if username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            return apology("Invalid username and/or password.")

        # Remember user ID and credential
        session["userID"] = rows[0]["userID"]
        session["usercredential"] = rows[0]["usercredential"]

        # Redirect user to the appropriate page based on their user credential
        if session["usercredential"] == "admin":
            return redirect("/admin")
        else:
            return redirect("/")

    # Render the login template
    return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""
    # Clear user session
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register a new user"""
    if request.method == "POST":
        # Get form data
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        billing_address = {
            "street": request.form.get("billing_street"),
            "city": request.form.get("billing_city"),
            "province": request.form.get("billing_province"),
            "zip": request.form.get("billing_zip"),
        }
        shipping_address = {
            "street": request.form.get("shipping_street"),
            "city": request.form.get("shipping_city"),
            "province": request.form.get("shipping_province"),
            "zip": request.form.get("shipping_zip"),
        }

        # Validate form data
        if not username:
            return apology("Please provide a username.")

        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return apology("Username must contain only letters, numbers, and underscores.")

        if not email:
            return apology("Please provide an email address.")

        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
            return apology("Invalid email address.")

        if not password:
            return apology("Please provide a password.")

        if not confirmation:
            return apology("Please confirm the password.")

        if password != confirmation:
            return apology("Passwords don't match.")

        for field in billing_address.values():
            if not field:
                return apology("Please provide a complete billing address.")

        for field in shipping_address.values():
            if not field:
                return apology("Please provide a complete shipping address.")

        # Hash the password
        hash = generate_password_hash(password)

        try:
            # Check if username or email already exists
            check_for_username = db.execute("SELECT username FROM users WHERE username = ?", (username,))
            if check_for_username:
                return apology("Username already taken.")

            check_for_email = db.execute("SELECT email FROM users WHERE email = ?", (email,))
            if check_for_email:
                return apology("Email already registered.")

            # Insert new user into the database
            db.execute(
                "INSERT INTO users (username, hash, email, usercredential, billingAddStreet, billingAddCity, billingAddProvince, billingAddZip, shippingAddStreet, shippingAddCity, shippingAddProvince, shippingAddZip) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?, ?, ?, ?)",
                username,
                hash,
                email,
                "user",
                billing_address["street"],
                billing_address["city"],
                billing_address["province"],
                billing_address["zip"],
                shipping_address["street"],
                shipping_address["city"],
                shipping_address["province"],
                shipping_address["zip"],
            )
            rows = db.execute("SELECT * FROM users WHERE username = ?", (username,))
            session["userID"] = rows[0]["userID"]
            return redirect("/")
        except Exception as e:
            return apology(str(e), 500)

    # Render the registration template
    return render_template("register.html")


if __name__ == "__main__":
    app.run(debug=True)
