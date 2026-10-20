CREATE TABLE IF NOT EXISTS categories (category_id INT PRIMARY KEY, category_name VARCHAR(30) NOT NULL);
CREATE TABLE IF NOT EXISTS customers (customer_id INT PRIMARY KEY, customer_name VARCHAR(30) NOT NULL, city VARCHAR(30), registered_at DATE NOT NULL);
CREATE TABLE IF NOT EXISTS products (product_id INT PRIMARY KEY, product_name VARCHAR(60) NOT NULL, category_id INT NOT NULL, price DECIMAL(10,2) NOT NULL, FOREIGN KEY (category_id) REFERENCES categories(category_id));
CREATE TABLE IF NOT EXISTS orders (order_id INT PRIMARY KEY, customer_id INT NOT NULL, order_date DATE NOT NULL, status VARCHAR(20) NOT NULL, FOREIGN KEY (customer_id) REFERENCES customers(customer_id));
CREATE TABLE IF NOT EXISTS order_items (item_id INT PRIMARY KEY, order_id INT NOT NULL, product_id INT NOT NULL, quantity INT NOT NULL, unit_price DECIMAL(10,2) NOT NULL, FOREIGN KEY (order_id) REFERENCES orders(order_id), FOREIGN KEY (product_id) REFERENCES products(product_id));
