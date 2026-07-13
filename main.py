import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "restaurant-secret-key"

DB_PATH = os.path.join(os.path.dirname(__file__), "restaurant.db")
DB_TYPE = "sqlite"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            loyalty_points INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS reservations (
            reservation_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            reservation_date TEXT NOT NULL,
            reservation_time TEXT NOT NULL,
            party_size INTEGER NOT NULL,
            status TEXT NOT NULL,
            notes TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        );

        CREATE TABLE IF NOT EXISTS menu_items (
            menu_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT,
            is_available INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            reservation_id INTEGER,
            order_status TEXT NOT NULL,
            total_amount REAL NOT NULL,
            order_datetime TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
            FOREIGN KEY (reservation_id) REFERENCES reservations(reservation_id)
        );
        """
    )

    customer_count = conn.execute("SELECT COUNT(*) AS count FROM customers").fetchone()["count"]
    if customer_count == 0:
        conn.executemany(
            """
            INSERT INTO customers (first_name, last_name, email, phone, loyalty_points)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                ("Alice", "Garcia", "alice@example.com", "555-1001", 185),
                ("Noah", "Patel", "noah@example.com", "555-1002", 92),
                ("Mia", "Johnson", "mia@example.com", "555-1003", 240),
            ],
        )

    reservation_count = conn.execute("SELECT COUNT(*) AS count FROM reservations").fetchone()["count"]
    if reservation_count == 0:
        conn.execute(
            """
            INSERT INTO reservations (customer_id, reservation_date, reservation_time, party_size, status, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (1, "2026-07-14", "18:30", 4, "confirmed", "Anniversary dinner"),
        )

    menu_count = conn.execute("SELECT COUNT(*) AS count FROM menu_items").fetchone()["count"]
    if menu_count == 0:
        conn.executemany(
            """
            INSERT INTO menu_items (name, category, price, description, is_available)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                ("Truffle Garlic Bread", "Appetizers", 8.50, "Warm bread with truffle oil", 1),
                ("Grilled Salmon", "Main Course", 24.00, "Served with vegetables", 1),
                ("Chocolate Lava Cake", "Desserts", 9.50, "Warm cake with molten chocolate", 1),
            ],
        )

    order_count = conn.execute("SELECT COUNT(*) AS count FROM orders").fetchone()["count"]
    if order_count == 0:
        conn.execute(
            """
            INSERT INTO orders (customer_id, reservation_id, order_status, total_amount, order_datetime)
            VALUES (?, ?, ?, ?, ?)
            """,
            (1, 1, "completed", 50.69, "2026-07-01T19:00"),
        )

    conn.commit()
    conn.close()


init_db()


@app.route('/')
def index():
    edit_customer_id = request.args.get('edit_customer_id', type=int)
    edit_reservation_id = request.args.get('edit_reservation_id', type=int)
    edit_menu_item_id = request.args.get('edit_menu_item_id', type=int)
    edit_order_id = request.args.get('edit_order_id', type=int)

    conn = get_db()
    edit_customer = conn.execute("SELECT * FROM customers WHERE customer_id = ?", (edit_customer_id,)).fetchone() if edit_customer_id else None
    edit_reservation = conn.execute("SELECT * FROM reservations WHERE reservation_id = ?", (edit_reservation_id,)).fetchone() if edit_reservation_id else None
    edit_menu_item = conn.execute("SELECT * FROM menu_items WHERE menu_item_id = ?", (edit_menu_item_id,)).fetchone() if edit_menu_item_id else None
    edit_order = conn.execute("SELECT * FROM orders WHERE order_id = ?", (edit_order_id,)).fetchone() if edit_order_id else None

    customers = conn.execute("SELECT * FROM customers ORDER BY customer_id").fetchall()
    reservations = conn.execute(
        """
        SELECT r.*, c.first_name || ' ' || c.last_name AS customer_name
        FROM reservations r
        LEFT JOIN customers c ON c.customer_id = r.customer_id
        ORDER BY r.reservation_id
        """
    ).fetchall()
    menu_items = conn.execute("SELECT * FROM menu_items ORDER BY menu_item_id").fetchall()
    orders = conn.execute(
        """
        SELECT o.*, c.first_name || ' ' || c.last_name AS customer_name
        FROM orders o
        LEFT JOIN customers c ON c.customer_id = o.customer_id
        ORDER BY o.order_id
        """
    ).fetchall()
    conn.close()

    return render_template(
        'index.html',
        customers=customers,
        reservations=reservations,
        menu_items=menu_items,
        orders=orders,
        edit_customer=edit_customer,
        edit_reservation=edit_reservation,
        edit_menu_item=edit_menu_item,
        edit_order=edit_order,
        db_type=DB_TYPE,
    )


@app.route('/customers', methods=['POST'])
def save_customer():
    customer_id = request.form.get('customer_id', '').strip()
    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    email = request.form.get('email', '').strip()
    phone = request.form.get('phone', '').strip() or None
    loyalty_points = int(request.form.get('loyalty_points', 0) or 0)

    if not (first_name and last_name and email):
        flash('Please fill in the required customer fields.', 'error')
        return redirect(url_for('index'))

    conn = get_db()
    if customer_id:
        conn.execute(
            """
            UPDATE customers
            SET first_name = ?, last_name = ?, email = ?, phone = ?, loyalty_points = ?
            WHERE customer_id = ?
            """,
            (first_name, last_name, email, phone, loyalty_points, int(customer_id)),
        )
        flash('Customer updated.', 'success')
    else:
        conn.execute(
            """
            INSERT INTO customers (first_name, last_name, email, phone, loyalty_points)
            VALUES (?, ?, ?, ?, ?)
            """,
            (first_name, last_name, email, phone, loyalty_points),
        )
        flash('Customer added.', 'success')
    conn.commit()
    conn.close()
    return redirect(url_for('index'))


@app.route('/customers/<int:customer_id>/delete', methods=['POST'])
def delete_customer(customer_id):
    conn = get_db()
    conn.execute("DELETE FROM customers WHERE customer_id = ?", (customer_id,))
    conn.commit()
    conn.close()
    flash('Customer removed.', 'success')
    return redirect(url_for('index'))


@app.route('/reservations', methods=['POST'])
def save_reservation():
    reservation_id = request.form.get('reservation_id', '').strip()
    customer_id = int(request.form.get('customer_id', 0) or 0)
    reservation_date = request.form.get('reservation_date', '').strip()
    reservation_time = request.form.get('reservation_time', '').strip()
    party_size = int(request.form.get('party_size', 0) or 0)
    status = request.form.get('status', 'confirmed').strip()
    notes = request.form.get('notes', '').strip() or None

    if not (customer_id and reservation_date and reservation_time and party_size):
        flash('Please provide complete reservation details.', 'error')
        return redirect(url_for('index'))

    conn = get_db()
    if reservation_id:
        conn.execute(
            """
            UPDATE reservations
            SET customer_id = ?, reservation_date = ?, reservation_time = ?, party_size = ?, status = ?, notes = ?
            WHERE reservation_id = ?
            """,
            (customer_id, reservation_date, reservation_time, party_size, status, notes, int(reservation_id)),
        )
        flash('Reservation updated.', 'success')
    else:
        conn.execute(
            """
            INSERT INTO reservations (customer_id, reservation_date, reservation_time, party_size, status, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (customer_id, reservation_date, reservation_time, party_size, status, notes),
        )
        flash('Reservation added.', 'success')
    conn.commit()
    conn.close()
    return redirect(url_for('index'))


@app.route('/reservations/<int:reservation_id>/delete', methods=['POST'])
def delete_reservation(reservation_id):
    conn = get_db()
    conn.execute("DELETE FROM reservations WHERE reservation_id = ?", (reservation_id,))
    conn.commit()
    conn.close()
    flash('Reservation removed.', 'success')
    return redirect(url_for('index'))


@app.route('/menu-items', methods=['POST'])
def save_menu_item():
    menu_item_id = request.form.get('menu_item_id', '').strip()
    name = request.form.get('name', '').strip()
    category = request.form.get('category', '').strip()
    price = float(request.form.get('price', 0) or 0)
    description = request.form.get('description', '').strip() or None
    is_available = 1 if request.form.get('is_available') == '1' else 0

    if not (name and category):
        flash('Please provide a menu item name and category.', 'error')
        return redirect(url_for('index'))

    conn = get_db()
    if menu_item_id:
        conn.execute(
            """
            UPDATE menu_items
            SET name = ?, category = ?, price = ?, description = ?, is_available = ?
            WHERE menu_item_id = ?
            """,
            (name, category, price, description, is_available, int(menu_item_id)),
        )
        flash('Menu item updated.', 'success')
    else:
        conn.execute(
            """
            INSERT INTO menu_items (name, category, price, description, is_available)
            VALUES (?, ?, ?, ?, ?)
            """,
            (name, category, price, description, is_available),
        )
        flash('Menu item added.', 'success')
    conn.commit()
    conn.close()
    return redirect(url_for('index'))


@app.route('/menu-items/<int:menu_item_id>/delete', methods=['POST'])
def delete_menu_item(menu_item_id):
    conn = get_db()
    conn.execute("DELETE FROM menu_items WHERE menu_item_id = ?", (menu_item_id,))
    conn.commit()
    conn.close()
    flash('Menu item removed.', 'success')
    return redirect(url_for('index'))


@app.route('/orders', methods=['POST'])
def save_order():
    order_id = request.form.get('order_id', '').strip()
    customer_id = int(request.form.get('customer_id', 0) or 0)
    reservation_id = int(request.form.get('reservation_id', 0) or 0) or None
    order_status = request.form.get('order_status', 'received').strip()
    total_amount = float(request.form.get('total_amount', 0) or 0)
    order_datetime = request.form.get('order_datetime', '').strip() or datetime.now().strftime('%Y-%m-%dT%H:%M')

    if not customer_id:
        flash('Please select a customer for the order.', 'error')
        return redirect(url_for('index'))

    conn = get_db()
    if order_id:
        conn.execute(
            """
            UPDATE orders
            SET customer_id = ?, reservation_id = ?, order_status = ?, total_amount = ?, order_datetime = ?
            WHERE order_id = ?
            """,
            (customer_id, reservation_id, order_status, total_amount, order_datetime, int(order_id)),
        )
        flash('Order updated.', 'success')
    else:
        conn.execute(
            """
            INSERT INTO orders (customer_id, reservation_id, order_status, total_amount, order_datetime)
            VALUES (?, ?, ?, ?, ?)
            """,
            (customer_id, reservation_id, order_status, total_amount, order_datetime),
        )
        flash('Order added.', 'success')
    conn.commit()
    conn.close()
    return redirect(url_for('index'))


@app.route('/orders/<int:order_id>/delete', methods=['POST'])
def delete_order(order_id):
    conn = get_db()
    conn.execute("DELETE FROM orders WHERE order_id = ?", (order_id,))
    conn.commit()
    conn.close()
    flash('Order removed.', 'success')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
