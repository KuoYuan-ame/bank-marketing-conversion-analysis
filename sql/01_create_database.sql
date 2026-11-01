-- UCI Bank Marketing (legacy bank-full.csv)
-- Source: https://archive.ics.uci.edu/dataset/222/bank+marketing
-- This schema stores marketing OBSERVATIONS, not unique customers.
-- First run 02_prepare_mysql_import.py to create data/bank_mysql_import.csv.

CREATE DATABASE IF NOT EXISTS bank_marketing_project
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE bank_marketing_project;

-- Safe for re-running: it will not drop existing imported rows.
CREATE TABLE IF NOT EXISTS bank_marketing (
    record_id INT NOT NULL,
    age SMALLINT UNSIGNED NOT NULL,
    job VARCHAR(32) NOT NULL,
    marital VARCHAR(16) NOT NULL,
    education VARCHAR(16) NOT NULL,
    `default` VARCHAR(3) NOT NULL,
    balance INT NOT NULL,
    housing VARCHAR(3) NOT NULL,
    loan VARCHAR(3) NOT NULL,
    contact VARCHAR(16) NOT NULL,
    `day` TINYINT UNSIGNED NOT NULL,
    `month` VARCHAR(3) NOT NULL,
    duration INT UNSIGNED NOT NULL,
    campaign INT UNSIGNED NOT NULL,
    pdays INT NOT NULL,
    previous INT UNSIGNED NOT NULL,
    poutcome VARCHAR(16) NOT NULL,
    y VARCHAR(3) NOT NULL,
    PRIMARY KEY (record_id)
) ENGINE=InnoDB;

SHOW TABLES;
DESCRIBE bank_marketing;
