-- SQL script for initializing the database
CREATE DATABASE IF NOT EXISTS email_app;
USE email_app;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    full_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create emails table
CREATE TABLE IF NOT EXISTS emails (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sender VARCHAR(120) NOT NULL,
    recipient VARCHAR(120) NOT NULL,
    subject VARCHAR(200) NOT NULL,
    body TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_read BOOLEAN DEFAULT 0,
    is_draft BOOLEAN DEFAULT 0,
    is_favorite BOOLEAN DEFAULT 0
);

-- Insert sample data if needed
INSERT IGNORE INTO users (username, email, password_hash, full_name) VALUES 
('admin', 'admin@email.com', '$2b$12$dummy_hash_for_admin', 'Administrator');
