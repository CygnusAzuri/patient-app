CREATE DATABASE patient_db;
USE patient_db;

CREATE TABLE patients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    age INT NOT NULL,
    gender VARCHAR(10) NOT NULL,
    contact VARCHAR(15) NOT NULL,
    kyc VARCHAR(255),
    concern TEXT
);
