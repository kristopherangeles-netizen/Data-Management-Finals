import os
import sqlite3
import flet as ft

DB_PATH = os.path.join(os.path.dirname(__file__), "restaurant.db")


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

    if conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0] == 0:
        conn.executemany(
            "INSERT INTO customers (first_name, last_name, email, phone, loyalty_points) VALUES (?, ?, ?, ?, ?)",
            [
                ("Alice", "Garcia", "alice@example.com", "555-1001", 185),
                ("Noah", "Patel", "noah@example.com", "555-1002", 92),
                ("Mia", "Johnson", "mia@example.com", "555-1003", 240),
            ],
        )

    if conn.execute("SELECT COUNT(*) FROM reservations").fetchone()[0] == 0:
        conn.execute(
            "INSERT INTO reservations (customer_id, reservation_date, reservation_time, party_size, status, notes) VALUES (?, ?, ?, ?, ?, ?)",
            (1, "2026-07-14", "18:30", 4, "confirmed", "Anniversary dinner"),
        )

    if conn.execute("SELECT COUNT(*) FROM menu_items").fetchone()[0] == 0:
        conn.executemany(
            "INSERT INTO menu_items (name, category, price, description, is_available) VALUES (?, ?, ?, ?, ?)",
            [
                ("Truffle Garlic Bread", "Appetizers", 8.50, "Warm bread with truffle oil", 1),
                ("Grilled Salmon", "Main Course", 24.00, "Served with vegetables", 1),
                ("Chocolate Lava Cake", "Desserts", 9.50, "Warm cake with molten chocolate", 1),
            ],
        )

    if conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 0:
        conn.execute(
            "INSERT INTO orders (customer_id, reservation_id, order_status, total_amount, order_datetime) VALUES (?, ?, ?, ?, ?)",
            (1, 1, "completed", 50.69, "2026-07-01T19:00"),
        )

    conn.commit()
    conn.close()


init_db()


def main(page: ft.Page):
    page.title = "Restaurant Manager"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
    page.padding = 10
    page.scroll = ft.ScrollMode.AUTO
    page.window.width = 430
    page.window.height = 960
    page.window.resizable = True

    state = {
        "editing_customer_id": None,
        "editing_reservation_id": None,
        "editing_menu_id": None,
        "editing_order_id": None,
        "active_tab": 0,
    }

    def load_data():
        conn = get_db()
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
        return customers, reservations, menu_items, orders

    def build_page():
        customers, reservations, menu_items, orders = load_data()

        customer_first_name = ft.TextField(label="First name", value="", expand=1)
        customer_last_name = ft.TextField(label="Last name", value="", expand=1)
        customer_email = ft.TextField(label="Email", value="", expand=1)
        customer_phone = ft.TextField(label="Phone", value="", expand=1)
        customer_points = ft.TextField(label="Loyalty points", value="0", keyboard_type=ft.KeyboardType.NUMBER, expand=1)

        if state["editing_customer_id"] is not None:
            for customer in customers:
                if customer["customer_id"] == state["editing_customer_id"]:
                    customer_first_name.value = customer["first_name"]
                    customer_last_name.value = customer["last_name"]
                    customer_email.value = customer["email"]
                    customer_phone.value = customer["phone"] or ""
                    customer_points.value = str(customer["loyalty_points"])
                    break

        def save_customer(e):
            first_name = customer_first_name.value.strip()
            last_name = customer_last_name.value.strip()
            email = customer_email.value.strip()
            phone = customer_phone.value.strip() or None
            points = int(customer_points.value or 0)
            if not (first_name and last_name and email):
                page.dialog = ft.AlertDialog(title=ft.Text("Please fill required customer fields"))
                page.open = True
                page.update()
                return
            conn = get_db()
            if state["editing_customer_id"] is None:
                conn.execute("INSERT INTO customers (first_name, last_name, email, phone, loyalty_points) VALUES (?, ?, ?, ?, ?)", (first_name, last_name, email, phone, points))
            else:
                conn.execute("UPDATE customers SET first_name=?, last_name=?, email=?, phone=?, loyalty_points=? WHERE customer_id=?", (first_name, last_name, email, phone, points, state["editing_customer_id"]))
            conn.commit()
            conn.close()
            state["editing_customer_id"] = None
            refresh_page()

        def cancel_customer(e):
            state["editing_customer_id"] = None
            refresh_page()

        customer_cards = []
        for customer in customers:
            customer_cards.append(
                ft.Card(
                    content=ft.Container(
                        padding=10,
                        content=ft.Column(
                            [
                                ft.Text(f"{customer['first_name']} {customer['last_name']}", weight="bold"),
                                ft.Text(customer['email']),
                                ft.Text(f"Points: {customer['loyalty_points']}"),
                                ft.Row(
                                    [
                                        ft.TextButton("Edit", on_click=lambda e, cid=customer['customer_id']: edit_customer(cid)),
                                        ft.TextButton("Delete", on_click=lambda e, cid=customer['customer_id']: delete_customer(cid)),
                                    ],
                                    spacing=5,
                                ),
                            ],
                            spacing=4,
                        ),
                    )
                )
            )

        def edit_customer(customer_id):
            state["editing_customer_id"] = customer_id
            refresh_page()

        def delete_customer(customer_id):
            conn = get_db()
            conn.execute("DELETE FROM customers WHERE customer_id=?", (customer_id,))
            conn.commit()
            conn.close()
            refresh_page()

        reservation_customer = ft.Dropdown(label="Customer", width=300, value="")
        reservation_customer.options = [ft.dropdown.Option("", "Select customer")]
        for customer in customers:
            reservation_customer.options.append(ft.dropdown.Option(str(customer["customer_id"]), f"{customer['first_name']} {customer['last_name']}"))

        reservation_date = ft.TextField(label="Date", value="", hint_text="YYYY-MM-DD")
        reservation_time = ft.TextField(label="Time", value="", hint_text="HH:MM")
        reservation_size = ft.TextField(label="Party size", value="2", keyboard_type=ft.KeyboardType.NUMBER)
        reservation_status = ft.Dropdown(label="Status", value="confirmed", width=300)
        reservation_status.options = [
            ft.dropdown.Option("confirmed", "Confirmed"),
            ft.dropdown.Option("checked_in", "Checked In"),
            ft.dropdown.Option("completed", "Completed"),
            ft.dropdown.Option("cancelled", "Cancelled"),
        ]
        reservation_notes = ft.TextField(label="Notes", value="")

        if state["editing_reservation_id"] is not None:
            for reservation in reservations:
                if reservation["reservation_id"] == state["editing_reservation_id"]:
                    reservation_customer.value = str(reservation["customer_id"])
                    reservation_date.value = reservation["reservation_date"]
                    reservation_time.value = reservation["reservation_time"]
                    reservation_size.value = str(reservation["party_size"])
                    reservation_status.value = reservation["status"]
                    reservation_notes.value = reservation["notes"] or ""
                    break

        def save_reservation(e):
            customer_id = int(reservation_customer.value) if reservation_customer.value else None
            if not customer_id:
                page.dialog = ft.AlertDialog(title=ft.Text("Select a customer first"))
                page.open = True
                page.update()
                return
            conn = get_db()
            if state["editing_reservation_id"] is None:
                conn.execute("INSERT INTO reservations (customer_id, reservation_date, reservation_time, party_size, status, notes) VALUES (?, ?, ?, ?, ?, ?)", (customer_id, reservation_date.value.strip(), reservation_time.value.strip(), int(reservation_size.value or 2), reservation_status.value or "confirmed", reservation_notes.value.strip() or None))
            else:
                conn.execute("UPDATE reservations SET customer_id=?, reservation_date=?, reservation_time=?, party_size=?, status=?, notes=? WHERE reservation_id=?", (customer_id, reservation_date.value.strip(), reservation_time.value.strip(), int(reservation_size.value or 2), reservation_status.value or "confirmed", reservation_notes.value.strip() or None, state["editing_reservation_id"]))
            conn.commit()
            conn.close()
            state["editing_reservation_id"] = None
            refresh_page()

        def cancel_reservation(e):
            state["editing_reservation_id"] = None
            refresh_page()

        def edit_reservation(reservation_id):
            state["editing_reservation_id"] = reservation_id
            refresh_page()

        def delete_reservation(reservation_id):
            conn = get_db()
            conn.execute("DELETE FROM reservations WHERE reservation_id=?", (reservation_id,))
            conn.commit()
            conn.close()
            refresh_page()

        reservation_cards = []
        for reservation in reservations:
            reservation_cards.append(
                ft.Card(
                    content=ft.Container(
                        padding=10,
                        content=ft.Column(
                            [
                                ft.Text(reservation['customer_name'] or "Unknown", weight="bold"),
                                ft.Text(f"{reservation['reservation_date']} • {reservation['reservation_time']}"),
                                ft.Text(f"Party: {reservation['party_size']} • {reservation['status']}"),
                                ft.Row(
                                    [
                                        ft.TextButton("Edit", on_click=lambda e, rid=reservation['reservation_id']: edit_reservation(rid)),
                                        ft.TextButton("Delete", on_click=lambda e, rid=reservation['reservation_id']: delete_reservation(rid)),
                                    ],
                                    spacing=5,
                                ),
                            ],
                            spacing=4,
                        ),
                    )
                )
            )

        menu_name = ft.TextField(label="Item name", value="")
        menu_category = ft.TextField(label="Category", value="")
        menu_price = ft.TextField(label="Price", value="0", keyboard_type=ft.KeyboardType.NUMBER)
        menu_description = ft.TextField(label="Description", value="")
        menu_available = ft.Dropdown(label="Available", value="1", width=300)
        menu_available.options = [ft.dropdown.Option("1", "Yes"), ft.dropdown.Option("0", "No")]

        if state["editing_menu_id"] is not None:
            for item in menu_items:
                if item["menu_item_id"] == state["editing_menu_id"]:
                    menu_name.value = item["name"]
                    menu_category.value = item["category"]
                    menu_price.value = str(item["price"])
                    menu_description.value = item["description"] or ""
                    menu_available.value = "1" if item["is_available"] else "0"
                    break

        def save_menu(e):
            conn = get_db()
            if state["editing_menu_id"] is None:
                conn.execute("INSERT INTO menu_items (name, category, price, description, is_available) VALUES (?, ?, ?, ?, ?)", (menu_name.value.strip(), menu_category.value.strip(), float(menu_price.value or 0), menu_description.value.strip() or None, int(menu_available.value or 1)))
            else:
                conn.execute("UPDATE menu_items SET name=?, category=?, price=?, description=?, is_available=? WHERE menu_item_id=?", (menu_name.value.strip(), menu_category.value.strip(), float(menu_price.value or 0), menu_description.value.strip() or None, int(menu_available.value or 1), state["editing_menu_id"]))
            conn.commit()
            conn.close()
            state["editing_menu_id"] = None
            refresh_page()

        def cancel_menu(e):
            state["editing_menu_id"] = None
            refresh_page()

        def edit_menu(menu_id):
            state["editing_menu_id"] = menu_id
            refresh_page()

        def delete_menu(menu_id):
            conn = get_db()
            conn.execute("DELETE FROM menu_items WHERE menu_item_id=?", (menu_id,))
            conn.commit()
            conn.close()
            refresh_page()

        menu_cards = []
        for item in menu_items:
            menu_cards.append(
                ft.Card(
                    content=ft.Container(
                        padding=10,
                        content=ft.Column(
                            [
                                ft.Text(item['name'], weight="bold"),
                                ft.Text(item['category']),
                                ft.Text(f"${item['price']:.2f} • {'Available' if item['is_available'] else 'Hidden'}"),
                                ft.Row(
                                    [
                                        ft.TextButton("Edit", on_click=lambda e, mid=item['menu_item_id']: edit_menu(mid)),
                                        ft.TextButton("Delete", on_click=lambda e, mid=item['menu_item_id']: delete_menu(mid)),
                                    ],
                                    spacing=5,
                                ),
                            ],
                            spacing=4,
                        ),
                    )
                )
            )

        order_customer = ft.Dropdown(label="Customer", width=300, value="")
        order_customer.options = [ft.dropdown.Option("", "Select customer")]
        for customer in customers:
            order_customer.options.append(ft.dropdown.Option(str(customer["customer_id"]), f"{customer['first_name']} {customer['last_name']}"))
        order_reservation = ft.Dropdown(label="Reservation", width=300, value="")
        order_reservation.options = [ft.dropdown.Option("", "No reservation")]
        for reservation in reservations:
            order_reservation.options.append(ft.dropdown.Option(str(reservation["reservation_id"]), f"#{reservation['reservation_id']} - {reservation['customer_name']}"))
        order_status = ft.Dropdown(label="Status", value="received", width=300)
        order_status.options = [
            ft.dropdown.Option("received", "Received"),
            ft.dropdown.Option("preparing", "Preparing"),
            ft.dropdown.Option("served", "Served"),
            ft.dropdown.Option("completed", "Completed"),
            ft.dropdown.Option("cancelled", "Cancelled"),
        ]
        order_total = ft.TextField(label="Total amount", value="0", keyboard_type=ft.KeyboardType.NUMBER)
        order_time = ft.TextField(label="Order time", value="", hint_text="YYYY-MM-DDTHH:MM")

        if state["editing_order_id"] is not None:
            for order in orders:
                if order["order_id"] == state["editing_order_id"]:
                    order_customer.value = str(order["customer_id"])
                    order_reservation.value = str(order["reservation_id"]) if order["reservation_id"] else ""
                    order_status.value = order["order_status"]
                    order_total.value = str(order["total_amount"])
                    order_time.value = order["order_datetime"]
                    break

        def save_order(e):
            customer_id = int(order_customer.value) if order_customer.value else None
            if not customer_id:
                page.dialog = ft.AlertDialog(title=ft.Text("Select a customer first"))
                page.open = True
                page.update()
                return
            reservation_id = int(order_reservation.value) if order_reservation.value else None
            conn = get_db()
            if state["editing_order_id"] is None:
                conn.execute("INSERT INTO orders (customer_id, reservation_id, order_status, total_amount, order_datetime) VALUES (?, ?, ?, ?, ?)", (customer_id, reservation_id, order_status.value or "received", float(order_total.value or 0), order_time.value.strip() or ""))
            else:
                conn.execute("UPDATE orders SET customer_id=?, reservation_id=?, order_status=?, total_amount=?, order_datetime=? WHERE order_id=?", (customer_id, reservation_id, order_status.value or "received", float(order_total.value or 0), order_time.value.strip() or "", state["editing_order_id"]))
            conn.commit()
            conn.close()
            state["editing_order_id"] = None
            refresh_page()

        def cancel_order(e):
            state["editing_order_id"] = None
            refresh_page()

        def edit_order(order_id):
            state["editing_order_id"] = order_id
            refresh_page()

        def delete_order(order_id):
            conn = get_db()
            conn.execute("DELETE FROM orders WHERE order_id=?", (order_id,))
            conn.commit()
            conn.close()
            refresh_page()

        order_cards = []
        for order in orders:
            order_cards.append(
                ft.Card(
                    content=ft.Container(
                        padding=10,
                        content=ft.Column(
                            [
                                ft.Text(order['customer_name'] or "Unknown", weight="bold"),
                                ft.Text(f"Status: {order['order_status']}") ,
                                ft.Text(f"Total: ${order['total_amount']:.2f}"),
                                ft.Row(
                                    [
                                        ft.TextButton("Edit", on_click=lambda e, oid=order['order_id']: edit_order(oid)),
                                        ft.TextButton("Delete", on_click=lambda e, oid=order['order_id']: delete_order(oid)),
                                    ],
                                    spacing=5,
                                ),
                            ],
                            spacing=4,
                        ),
                    )
                )
            )

        def refresh_page():
            page.controls.clear()
            page.add(build_page())
            page.update()

        def switch_tab(index):
            state["active_tab"] = index
            refresh_page()

        customer_view = ft.Container(
            padding=5,
            content=ft.Column(
                [
                    ft.Text("Customer details", size=18, weight="bold"),
                    ft.ResponsiveRow([ft.Container(customer_first_name, expand=True, padding=2), ft.Container(customer_last_name, expand=True, padding=2)]),
                    ft.ResponsiveRow([ft.Container(customer_email, expand=True, padding=2), ft.Container(customer_phone, expand=True, padding=2)]),
                    ft.Container(customer_points, padding=2),
                    ft.Row(
                        [
                            ft.ElevatedButton("Save", on_click=save_customer),
                            ft.OutlinedButton("Cancel", on_click=cancel_customer),
                        ],
                        spacing=8,
                    ),
                    ft.Divider(),
                    ft.Text("Customer list", size=16, weight="bold"),
                    ft.Column(customer_cards, spacing=8),
                ],
                spacing=8,
            ),
        )

        reservation_view = ft.Container(
            padding=5,
            content=ft.Column(
                [
                    ft.Text("Create or update a reservation", size=18, weight="bold"),
                    ft.Container(reservation_customer, padding=2),
                    ft.ResponsiveRow([ft.Container(reservation_date, expand=True, padding=2), ft.Container(reservation_time, expand=True, padding=2)]),
                    ft.ResponsiveRow([ft.Container(reservation_size, expand=True, padding=2), ft.Container(reservation_status, expand=True, padding=2)]),
                    ft.Container(reservation_notes, padding=2),
                    ft.Row([ft.ElevatedButton("Save", on_click=save_reservation), ft.OutlinedButton("Cancel", on_click=cancel_reservation)], spacing=8),
                    ft.Divider(),
                    ft.Text("Reservation list", size=16, weight="bold"),
                    ft.Column(reservation_cards, spacing=8),
                ],
                spacing=8,
            ),
        )

        menu_view = ft.Container(
            padding=5,
            content=ft.Column(
                [
                    ft.Text("Menu item management", size=18, weight="bold"),
                    ft.Container(menu_name, padding=2),
                    ft.ResponsiveRow([ft.Container(menu_category, expand=True, padding=2), ft.Container(menu_price, expand=True, padding=2)]),
                    ft.Container(menu_description, padding=2),
                    ft.Container(menu_available, padding=2),
                    ft.Row([ft.ElevatedButton("Save", on_click=save_menu), ft.OutlinedButton("Cancel", on_click=cancel_menu)], spacing=8),
                    ft.Divider(),
                    ft.Text("Menu items", size=16, weight="bold"),
                    ft.Column(menu_cards, spacing=8),
                ],
                spacing=8,
            ),
        )

        order_view = ft.Container(
            padding=5,
            content=ft.Column(
                [
                    ft.Text("Order management", size=18, weight="bold"),
                    ft.Container(order_customer, padding=2),
                    ft.Container(order_reservation, padding=2),
                    ft.ResponsiveRow([ft.Container(order_status, expand=True, padding=2), ft.Container(order_total, expand=True, padding=2)]),
                    ft.Container(order_time, padding=2),
                    ft.Row([ft.ElevatedButton("Save", on_click=save_order), ft.OutlinedButton("Cancel", on_click=cancel_order)], spacing=8),
                    ft.Divider(),
                    ft.Text("Recent orders", size=16, weight="bold"),
                    ft.Column(order_cards, spacing=8),
                ],
                spacing=8,
            ),
        )

        tab_views = [customer_view, reservation_view, menu_view, order_view]
        active_view = tab_views[state["active_tab"]]

        content = ft.Container(
            content=ft.Column(
                [
                    ft.Text("Restaurant Manager", size=24, weight="bold"),
                    ft.Text("Mobile-friendly dashboard for customers, reservations, menu items, and orders.", color="bluegrey700"),
                    ft.Divider(),
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Choose a section", size=14, weight="bold"),
                            ft.Row([
                                ft.TextButton("Customers", on_click=lambda e: switch_tab(0)),
                                ft.TextButton("Reservations", on_click=lambda e: switch_tab(1)),
                                ft.TextButton("Menu", on_click=lambda e: switch_tab(2)),
                                ft.TextButton("Orders", on_click=lambda e: switch_tab(3)),
                            ], wrap=True),
                            ft.Divider(),
                            active_view,
                        ], spacing=8),
                        padding=2,
                    ),
                ],
                spacing=10,
            ),
            padding=8,
            expand=True,
        )
        return content

    page.add(build_page())


if __name__ == "__main__":
    ft.app(target=main)
