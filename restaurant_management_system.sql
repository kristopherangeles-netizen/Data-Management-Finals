-- Restaurant Management System (PostgreSQL / Supabase compatible)
-- Designed to be normalized to 3NF and include reservations, ordering, tracking, inventory, and feedback.

DROP TABLE IF EXISTS feedback CASCADE;
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS menu_item_ingredients CASCADE;
DROP TABLE IF EXISTS inventory_items CASCADE;
DROP TABLE IF EXISTS menu_items CASCADE;
DROP TABLE IF EXISTS menu_categories CASCADE;
DROP TABLE IF EXISTS reservations CASCADE;
DROP TABLE IF EXISTS tables CASCADE;
DROP TABLE IF EXISTS staff CASCADE;
DROP TABLE IF EXISTS customers CASCADE;
DROP TABLE IF EXISTS restaurants CASCADE;

CREATE TABLE restaurants (
    restaurant_id BIGSERIAL PRIMARY KEY,
    restaurant_name VARCHAR(100) NOT NULL,
    address VARCHAR(255) NOT NULL,
    city VARCHAR(100) NOT NULL,
    state_province VARCHAR(100) NOT NULL,
    postal_code VARCHAR(20) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    opening_hours VARCHAR(120) NOT NULL
);

CREATE TABLE staff (
    staff_id BIGSERIAL PRIMARY KEY,
    restaurant_id BIGINT NOT NULL REFERENCES restaurants(restaurant_id) ON DELETE CASCADE,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    role VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(20),
    hire_date DATE NOT NULL DEFAULT CURRENT_DATE,
    salary NUMERIC(10,2) NOT NULL CHECK (salary >= 0)
);

CREATE TABLE customers (
    customer_id BIGSERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    date_of_birth DATE,
    loyalty_points INT NOT NULL DEFAULT 0 CHECK (loyalty_points >= 0),
    signup_date DATE NOT NULL DEFAULT CURRENT_DATE
);

CREATE TABLE tables (
    table_id BIGSERIAL PRIMARY KEY,
    restaurant_id BIGINT NOT NULL REFERENCES restaurants(restaurant_id) ON DELETE CASCADE,
    table_number INT NOT NULL,
    capacity INT NOT NULL CHECK (capacity > 0),
    status VARCHAR(20) NOT NULL DEFAULT 'available' CHECK (status IN ('available','occupied','reserved','out_of_service')),
    UNIQUE (restaurant_id, table_number)
);

CREATE TABLE reservations (
    reservation_id BIGSERIAL PRIMARY KEY,
    restaurant_id BIGINT NOT NULL REFERENCES restaurants(restaurant_id) ON DELETE CASCADE,
    customer_id BIGINT NOT NULL REFERENCES customers(customer_id) ON DELETE RESTRICT,
    table_id BIGINT NOT NULL REFERENCES tables(table_id) ON DELETE RESTRICT,
    reservation_date DATE NOT NULL,
    reservation_time TIME NOT NULL,
    party_size INT NOT NULL CHECK (party_size > 0),
    status VARCHAR(20) NOT NULL DEFAULT 'confirmed' CHECK (status IN ('confirmed','checked_in','completed','cancelled')),
    notes VARCHAR(255)
);

CREATE TABLE menu_categories (
    category_id BIGSERIAL PRIMARY KEY,
    restaurant_id BIGINT NOT NULL REFERENCES restaurants(restaurant_id) ON DELETE CASCADE,
    category_name VARCHAR(100) NOT NULL,
    UNIQUE (restaurant_id, category_name)
);

CREATE TABLE menu_items (
    menu_item_id BIGSERIAL PRIMARY KEY,
    category_id BIGINT NOT NULL REFERENCES menu_categories(category_id) ON DELETE RESTRICT,
    item_name VARCHAR(100) NOT NULL,
    description VARCHAR(255),
    price NUMERIC(8,2) NOT NULL CHECK (price >= 0),
    is_available BOOLEAN NOT NULL DEFAULT TRUE,
    preparation_time_minutes INT NOT NULL DEFAULT 10 CHECK (preparation_time_minutes > 0)
);

CREATE TABLE inventory_items (
    inventory_item_id BIGSERIAL PRIMARY KEY,
    restaurant_id BIGINT NOT NULL REFERENCES restaurants(restaurant_id) ON DELETE CASCADE,
    item_name VARCHAR(100) NOT NULL,
    unit VARCHAR(20) NOT NULL,
    stock_on_hand NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (stock_on_hand >= 0),
    reorder_level NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (reorder_level >= 0),
    last_restock_date DATE
);

CREATE TABLE menu_item_ingredients (
    menu_item_id BIGINT NOT NULL REFERENCES menu_items(menu_item_id) ON DELETE CASCADE,
    inventory_item_id BIGINT NOT NULL REFERENCES inventory_items(inventory_item_id) ON DELETE RESTRICT,
    quantity_required NUMERIC(8,2) NOT NULL CHECK (quantity_required > 0),
    PRIMARY KEY (menu_item_id, inventory_item_id)
);

CREATE TABLE orders (
    order_id BIGSERIAL PRIMARY KEY,
    restaurant_id BIGINT NOT NULL REFERENCES restaurants(restaurant_id) ON DELETE CASCADE,
    customer_id BIGINT REFERENCES customers(customer_id) ON DELETE SET NULL,
    staff_id BIGINT NOT NULL REFERENCES staff(staff_id) ON DELETE RESTRICT,
    table_id BIGINT REFERENCES tables(table_id) ON DELETE SET NULL,
    reservation_id BIGINT REFERENCES reservations(reservation_id) ON DELETE SET NULL,
    order_datetime TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    order_status VARCHAR(20) NOT NULL DEFAULT 'received' CHECK (order_status IN ('received','preparing','served','completed','cancelled')),
    subtotal NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (subtotal >= 0),
    tax_amount NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (tax_amount >= 0),
    total_amount NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (total_amount >= 0)
);

CREATE TABLE order_items (
    order_item_id BIGSERIAL PRIMARY KEY,
    order_id BIGINT NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    menu_item_id BIGINT NOT NULL REFERENCES menu_items(menu_item_id) ON DELETE RESTRICT,
    quantity INT NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(8,2) NOT NULL CHECK (unit_price >= 0),
    line_total NUMERIC(10,2) NOT NULL CHECK (line_total >= 0)
);

CREATE TABLE feedback (
    feedback_id BIGSERIAL PRIMARY KEY,
    restaurant_id BIGINT NOT NULL REFERENCES restaurants(restaurant_id) ON DELETE CASCADE,
    customer_id BIGINT REFERENCES customers(customer_id) ON DELETE SET NULL,
    order_id BIGINT REFERENCES orders(order_id) ON DELETE SET NULL,
    rating INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comments VARCHAR(500),
    feedback_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_staff_restaurant ON staff(restaurant_id);
CREATE INDEX idx_reservations_date_time ON reservations(reservation_date, reservation_time);
CREATE INDEX idx_orders_status ON orders(order_status);
CREATE INDEX idx_feedback_restaurant ON feedback(restaurant_id);

-- Seed data
INSERT INTO restaurants (restaurant_id, restaurant_name, address, city, state_province, postal_code, phone, email, opening_hours) VALUES
(1, 'Cedar & Oak Bistro', '128 Willow Street', 'Chicago', 'Illinois', '60611', '+1-312-555-0198', 'info@cedaroakbistro.com', 'Mon-Sun: 11:00 AM - 11:00 PM');

INSERT INTO staff (staff_id, restaurant_id, first_name, last_name, role, email, phone, hire_date, salary) VALUES
(1, 1, 'Maya', 'Lopez', 'Manager', 'maya.lopez@cedaroakbistro.com', '+1-312-555-0101', '2022-03-15', 6800.00),
(2, 1, 'Daniel', 'Kim', 'Head Chef', 'daniel.kim@cedaroakbistro.com', '+1-312-555-0102', '2021-08-01', 6200.00),
(3, 1, 'Sofia', 'Martinez', 'Server', 'sofia.martinez@cedaroakbistro.com', '+1-312-555-0103', '2023-05-20', 3200.00),
(4, 1, 'Ethan', 'Brooks', 'Server', 'ethan.brooks@cedaroakbistro.com', '+1-312-555-0104', '2023-07-12', 3200.00),
(5, 1, 'Priya', 'Singh', 'Host', 'priya.singh@cedaroakbistro.com', '+1-312-555-0105', '2024-01-09', 2800.00),
(6, 1, 'Liam', 'Chen', 'Bartender', 'liam.chen@cedaroakbistro.com', '+1-312-555-0106', '2022-11-21', 3000.00);

INSERT INTO customers (customer_id, first_name, last_name, email, phone, date_of_birth, loyalty_points, signup_date) VALUES
(1, 'Alice', 'Garcia', 'alice.garcia@email.com', '+1-773-555-1001', '1989-04-18', 185, '2023-01-12'),
(2, 'Noah', 'Patel', 'noah.patel@email.com', '+1-773-555-1002', '1992-11-02', 92, '2023-03-08'),
(3, 'Mia', 'Johnson', 'mia.johnson@email.com', '+1-773-555-1003', '1995-07-21', 240, '2022-11-30'),
(4, 'Owen', 'Davis', 'owen.davis@email.com', '+1-773-555-1004', '1987-02-14', 67, '2024-02-19'),
(5, 'Sophia', 'Nguyen', 'sophia.nguyen@email.com', '+1-773-555-1005', '1991-09-05', 310, '2022-08-10'),
(6, 'Luca', 'Brown', 'luca.brown@email.com', '+1-773-555-1006', '1984-12-27', 41, '2023-06-04'),
(7, 'Emma', 'Wilson', 'emma.wilson@email.com', '+1-773-555-1007', '1998-01-15', 125, '2024-04-01'),
(8, 'James', 'Taylor', 'james.taylor@email.com', '+1-773-555-1008', '1990-06-23', 88, '2023-09-17'),
(9, 'Ava', 'Martinez', 'ava.martinez@email.com', '+1-773-555-1009', '1993-10-08', 154, '2022-12-22'),
(10, 'Benjamin', 'Lee', 'benjamin.lee@email.com', '+1-773-555-1010', '1986-05-11', 205, '2024-01-27');

INSERT INTO tables (table_id, restaurant_id, table_number, capacity, status) VALUES
(1, 1, 1, 2, 'available'),
(2, 1, 2, 4, 'available'),
(3, 1, 3, 2, 'available'),
(4, 1, 4, 6, 'reserved'),
(5, 1, 5, 4, 'available'),
(6, 1, 6, 2, 'available'),
(7, 1, 7, 8, 'occupied'),
(8, 1, 8, 4, 'available');

INSERT INTO reservations (reservation_id, restaurant_id, customer_id, table_id, reservation_date, reservation_time, party_size, status, notes) VALUES
(1, 1, 1, 4, '2026-07-01', '18:30:00', 4, 'confirmed', 'Anniversary dinner'),
(2, 1, 3, 2, '2026-07-02', '19:00:00', 2, 'checked_in', 'Window seating requested'),
(3, 1, 5, 7, '2026-07-03', '20:00:00', 6, 'confirmed', 'Birthday party'),
(4, 1, 8, 6, '2026-07-05', '17:45:00', 2, 'completed', 'Quiet corner table'),
(5, 1, 2, 5, '2026-07-08', '18:15:00', 4, 'confirmed', 'Business dinner'),
(6, 1, 7, 3, '2026-07-10', '19:30:00', 2, 'confirmed', 'First date'),
(7, 1, 10, 8, '2026-07-12', '20:15:00', 3, 'confirmed', 'Friends gathering'),
(8, 1, 6, 1, '2026-07-14', '18:00:00', 2, 'cancelled', 'Customer cancelled');

INSERT INTO menu_categories (category_id, restaurant_id, category_name) VALUES
(1, 1, 'Appetizers'),
(2, 1, 'Main Course'),
(3, 1, 'Desserts'),
(4, 1, 'Beverages');

INSERT INTO menu_items (menu_item_id, category_id, item_name, description, price, is_available, preparation_time_minutes) VALUES
(1, 1, 'Truffle Garlic Bread', 'Toasted sourdough with garlic herb butter and truffle oil', 8.50, TRUE, 10),
(2, 1, 'Crispy Calamari', 'Lightly fried calamari with lemon aioli', 12.00, TRUE, 12),
(3, 2, 'Grilled Salmon', 'Served with roasted vegetables and lemon herb sauce', 24.00, TRUE, 20),
(4, 2, 'Filet Mignon', 'Tender beef filet with red wine reduction', 34.00, TRUE, 25),
(5, 2, 'Wild Mushroom Risotto', 'Creamy arborio rice with parmesan and roasted mushrooms', 21.00, TRUE, 18),
(6, 2, 'Chicken Alfredo Pasta', 'Creamy pasta with grilled chicken and parmesan', 19.50, TRUE, 15),
(7, 3, 'Chocolate Lava Cake', 'Warm cake with molten chocolate center', 9.50, TRUE, 10),
(8, 3, 'Lemon Tart', 'Buttery tart with citrus custard', 8.00, TRUE, 10),
(9, 4, 'Sparkling Citrus Lemonade', 'Fresh citrus lemonade with sparkling water', 5.50, TRUE, 5),
(10, 4, 'House Red Wine', 'Glass of house red blend', 9.00, TRUE, 5);

INSERT INTO inventory_items (inventory_item_id, restaurant_id, item_name, unit, stock_on_hand, reorder_level, last_restock_date) VALUES
(1, 1, 'Sourdough Loaf', 'loaf', 20, 8, '2026-07-10'),
(2, 1, 'Garlic', 'kg', 3.5, 1.5, '2026-07-11'),
(3, 1, 'Butter', 'kg', 5.0, 2.0, '2026-07-09'),
(4, 1, 'Truffle Oil', 'bottle', 2, 1, '2026-07-08'),
(5, 1, 'Salmon Fillet', 'kg', 4.2, 2.0, '2026-07-10'),
(6, 1, 'Beef Filet', 'kg', 3.8, 1.5, '2026-07-09'),
(7, 1, 'Arborio Rice', 'kg', 6.0, 2.5, '2026-07-11'),
(8, 1, 'Chicken Breast', 'kg', 4.6, 2.0, '2026-07-10'),
(9, 1, 'Pasta', 'kg', 8.0, 3.0, '2026-07-12'),
(10, 1, 'Chocolate', 'kg', 2.5, 1.0, '2026-07-10'),
(11, 1, 'Lemons', 'kg', 2.0, 1.0, '2026-07-12'),
(12, 1, 'Red Wine', 'bottle', 18, 6, '2026-07-11');

INSERT INTO menu_item_ingredients (menu_item_id, inventory_item_id, quantity_required) VALUES
(1, 1, 1),
(1, 2, 0.2),
(1, 3, 0.1),
(1, 4, 0.05),
(3, 5, 0.3),
(4, 6, 0.25),
(5, 7, 0.25),
(6, 8, 0.3),
(6, 9, 0.2),
(7, 10, 0.2),
(8, 11, 0.15),
(10, 12, 1);

INSERT INTO orders (order_id, restaurant_id, customer_id, staff_id, table_id, reservation_id, order_datetime, order_status, subtotal, tax_amount, total_amount) VALUES
(1, 1, 1, 3, 4, 1, '2026-07-01 19:00:00', 'completed', 46.50, 4.19, 50.69),
(2, 1, 3, 4, 2, 2, '2026-07-02 19:30:00', 'completed', 33.00, 2.97, 35.97),
(3, 1, 5, 3, 7, 3, '2026-07-03 20:30:00', 'served', 87.50, 7.88, 95.38),
(4, 1, 8, 4, 6, 4, '2026-07-05 18:10:00', 'completed', 24.50, 2.21, 26.71),
(5, 1, 2, 3, 5, 5, '2026-07-08 18:45:00', 'preparing', 58.00, 5.22, 63.22),
(6, 1, 7, 4, 3, 6, '2026-07-10 20:00:00', 'completed', 38.00, 3.42, 41.42),
(7, 1, 10, 3, 8, 7, '2026-07-12 20:45:00', 'received', 41.50, 3.74, 45.24),
(8, 1, 6, 6, 1, NULL, '2026-07-13 18:20:00', 'served', 16.00, 1.44, 17.44),
(9, 1, 9, 4, 2, NULL, '2026-07-13 20:00:00', 'preparing', 29.50, 2.66, 32.16),
(10, 1, 4, 3, 5, NULL, '2026-07-13 21:10:00', 'received', 53.50, 4.82, 58.32);

INSERT INTO order_items (order_item_id, order_id, menu_item_id, quantity, unit_price, line_total) VALUES
(1, 1, 1, 2, 8.50, 17.00),
(2, 1, 6, 1, 19.50, 19.50),
(3, 1, 9, 2, 5.50, 11.00),
(4, 2, 2, 1, 12.00, 12.00),
(5, 2, 8, 1, 8.00, 8.00),
(6, 2, 10, 1, 9.00, 9.00),
(7, 3, 4, 2, 34.00, 68.00),
(8, 3, 7, 1, 9.50, 9.50),
(9, 4, 1, 1, 8.50, 8.50),
(10, 4, 9, 3, 5.50, 16.50),
(11, 5, 3, 1, 24.00, 24.00),
(12, 5, 5, 1, 21.00, 21.00),
(13, 5, 10, 1, 9.00, 9.00),
(14, 6, 2, 1, 12.00, 12.00),
(15, 6, 6, 1, 19.50, 19.50),
(16, 6, 8, 1, 8.00, 8.00),
(17, 7, 3, 1, 24.00, 24.00),
(18, 7, 7, 1, 9.50, 9.50),
(19, 7, 9, 2, 5.50, 11.00),
(20, 8, 1, 1, 8.50, 8.50),
(21, 8, 2, 1, 12.00, 12.00),
(22, 9, 5, 1, 21.00, 21.00),
(23, 9, 8, 1, 8.00, 8.00),
(24, 10, 4, 1, 34.00, 34.00),
(25, 10, 7, 1, 9.50, 9.50),
(26, 10, 10, 1, 9.00, 9.00);

INSERT INTO feedback (feedback_id, restaurant_id, customer_id, order_id, rating, comments, feedback_date) VALUES
(1, 1, 1, 1, 5, 'Excellent service and the pasta was outstanding.', '2026-07-01 21:00:00'),
(2, 1, 3, 2, 4, 'Food arrived quickly and the staff were friendly.', '2026-07-02 20:30:00'),
(3, 1, 5, 3, 5, 'Loved the filet mignon and the ambiance was perfect.', '2026-07-03 22:00:00'),
(4, 1, 8, 4, 4, 'Great lemonade and fast service.', '2026-07-05 18:45:00'),
(5, 1, 2, 5, 3, 'The food was good, but the wait was a bit long.', '2026-07-08 19:30:00'),
(6, 1, 10, 7, 5, 'Fantastic dessert and very attentive server.', '2026-07-12 21:30:00');

-- Useful reporting views
CREATE VIEW restaurant_order_summary AS
SELECT
    o.order_id,
    c.first_name || ' ' || c.last_name AS customer_name,
    s.first_name || ' ' || s.last_name AS staff_name,
    o.order_datetime,
    o.order_status,
    o.total_amount
FROM orders o
LEFT JOIN customers c ON o.customer_id = c.customer_id
LEFT JOIN staff s ON o.staff_id = s.staff_id;
