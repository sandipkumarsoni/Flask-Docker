CREATE DATABASE IF NOT EXISTS product_api
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE product_api;

CREATE TABLE IF NOT EXISTS products (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    description TEXT NULL,
    price DECIMAL(10, 2) NOT NULL,
    stock_quantity INT UNSIGNED NOT NULL DEFAULT 0,
    PRIMARY KEY (id)
);
