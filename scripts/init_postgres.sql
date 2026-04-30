-- PostgreSQL Initialization Script for Rescue System
-- Run this script to create database and initial admin user

-- Create database if not exists (run as postgres superuser)
-- DROP DATABASE IF EXISTS rescue_system;
CREATE DATABASE rescue_system
    WITH 
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;

-- Connect to the new database
\c rescue_system

-- Enable UUID extension if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create enum types
DO $$ BEGIN
    CREATE TYPE user_role AS ENUM ('customer', 'company_staff', 'admin');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE request_status AS ENUM ('pending', 'accepted', 'en_route', 'on_site', 'completed', 'cancelled');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    role user_role NOT NULL DEFAULT 'customer',
    is_active BOOLEAN DEFAULT TRUE,
    avatar_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create rescue_companies table
CREATE TABLE IF NOT EXISTS rescue_companies (
    id SERIAL PRIMARY KEY,
    company_name VARCHAR(200) NOT NULL,
    address TEXT NOT NULL,
    hotline VARCHAR(20) NOT NULL,
    license_number VARCHAR(50) UNIQUE NOT NULL,
    latitude FLOAT,
    longitude FLOAT,
    rating_avg FLOAT DEFAULT 0.0,
    status VARCHAR(20) DEFAULT 'active',
    service_radius_km FLOAT DEFAULT 10.0,
    owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create services table
CREATE TABLE IF NOT EXISTS services (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES rescue_companies(id) ON DELETE CASCADE,
    service_name VARCHAR(100) NOT NULL,
    base_price FLOAT NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create rescue_vehicles table
CREATE TABLE IF NOT EXISTS rescue_vehicles (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES rescue_companies(id) ON DELETE CASCADE,
    license_plate VARCHAR(20) NOT NULL,
    vehicle_type VARCHAR(50) NOT NULL,
    capacity INTEGER,
    status VARCHAR(20) DEFAULT 'available',
    current_latitude FLOAT,
    current_longitude FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create rescue_requests table
CREATE TABLE IF NOT EXISTS rescue_requests (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_id INTEGER REFERENCES rescue_companies(id),
    service_id INTEGER NOT NULL REFERENCES services(id),
    vehicle_id INTEGER REFERENCES rescue_vehicles(id),
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    address_description TEXT NOT NULL,
    car_issue_detail TEXT NOT NULL,
    images JSONB DEFAULT '[]'::jsonb,
    status VARCHAR(20) DEFAULT 'pending',
    eta_minutes INTEGER,
    actual_arrival_time TIMESTAMP,
    actual_completion_time TIMESTAMP,
    total_cost FLOAT,
    payment_status VARCHAR(20) DEFAULT 'unpaid',
    payment_method VARCHAR(50),
    feedback TEXT,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create payments table
CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    request_id INTEGER NOT NULL REFERENCES rescue_requests(id) ON DELETE CASCADE,
    amount FLOAT NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    transaction_id VARCHAR(100),
    status VARCHAR(20) DEFAULT 'pending',
    paid_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create reviews table
CREATE TABLE IF NOT EXISTS reviews (
    id SERIAL PRIMARY KEY,
    request_id INTEGER NOT NULL REFERENCES rescue_requests(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_id INTEGER REFERENCES rescue_companies(id),
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create chat_messages table (for chat with image support)
CREATE TABLE IF NOT EXISTS chat_messages (
    id SERIAL PRIMARY KEY,
    request_id INTEGER NOT NULL REFERENCES rescue_requests(id) ON DELETE CASCADE,
    sender_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message_text TEXT,
    image_url VARCHAR(500),
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

CREATE INDEX IF NOT EXISTS idx_rescue_requests_user_id ON rescue_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_rescue_requests_company_id ON rescue_requests(company_id);
CREATE INDEX IF NOT EXISTS idx_rescue_requests_status ON rescue_requests(status);
CREATE INDEX IF NOT EXISTS idx_rescue_requests_created_at ON rescue_requests(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_rescue_companies_owner_id ON rescue_companies(owner_id);
CREATE INDEX IF NOT EXISTS idx_rescue_companies_status ON rescue_companies(status);

CREATE INDEX IF NOT EXISTS idx_services_company_id ON services(company_id);
CREATE INDEX IF NOT EXISTS idx_vehicles_company_id ON rescue_vehicles(company_id);

CREATE INDEX IF NOT EXISTS idx_chat_messages_request_id ON chat_messages(request_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat_messages(created_at DESC);

-- Insert default admin user (password: admin123)
-- Password hash generated using bcrypt for 'admin123'
INSERT INTO users (username, password_hash, full_name, phone, email, role, is_active)
VALUES (
    'admin',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS3MebAJu',
    'System Administrator',
    '0901234567',
    'admin@rescue.com',
    'admin',
    TRUE
)
ON CONFLICT (username) DO NOTHING;

-- Insert sample customer user (password: customer123)
INSERT INTO users (username, password_hash, full_name, phone, email, role, is_active)
VALUES (
    'customer',
    '$2b$12$KIXxKfEhPLWWz8xMJF3o.uxcTiMn6WDLemhN8/LEPKZmLCpCjwIWy',
    'Nguyen Van A',
    '0912345678',
    'customer@example.com',
    'customer',
    TRUE
)
ON CONFLICT (username) DO NOTHING;

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_rescue_companies_updated_at ON rescue_companies;
CREATE TRIGGER update_rescue_companies_updated_at
    BEFORE UPDATE ON rescue_companies
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_services_updated_at ON services;
CREATE TRIGGER update_services_updated_at
    BEFORE UPDATE ON services
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_rescue_vehicles_updated_at ON rescue_vehicles;
CREATE TRIGGER update_rescue_vehicles_updated_at
    BEFORE UPDATE ON rescue_vehicles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_rescue_requests_updated_at ON rescue_requests;
CREATE TRIGGER update_rescue_requests_updated_at
    BEFORE UPDATE ON rescue_requests
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

