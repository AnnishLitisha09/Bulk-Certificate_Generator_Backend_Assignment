-- =======================================================
-- Bulk Certificate Generator - MySQL Workbench DDL Schema
-- Execute this entire script in MySQL Workbench Query Editor
-- =======================================================

-- 1. Create and select the database
CREATE DATABASE IF NOT EXISTS `bulk_certificates_db`
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE `bulk_certificates_db`;

-- 2. Drop existing tables if recreating from scratch (Order matters due to foreign keys)
DROP TABLE IF EXISTS `certificates`;
DROP TABLE IF EXISTS `recipients`;
DROP TABLE IF EXISTS `generation_jobs`;

-- 3. Table: generation_jobs
-- Tracks bulk batches, overall status, counts, and timestamps
CREATE TABLE `generation_jobs` (
    `id` VARCHAR(36) NOT NULL,
    `event_name` VARCHAR(255) NOT NULL,
    `organization_name` VARCHAR(255) NOT NULL,
    `certificate_title` VARCHAR(255) NOT NULL,
    `issue_date` VARCHAR(50) NOT NULL,
    `status` VARCHAR(30) NOT NULL DEFAULT 'PENDING',
    `total_recipients` INT NOT NULL DEFAULT 0,
    `successful_count` INT NOT NULL DEFAULT 0,
    `failed_count` INT NOT NULL DEFAULT 0,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `completed_at` DATETIME NULL,
    PRIMARY KEY (`id`),
    INDEX `ix_generation_jobs_status` (`status`),
    INDEX `ix_generation_jobs_status_created` (`status`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Table: recipients
-- Stores recipient records, individual status, error messages, and linked certificate
CREATE TABLE `recipients` (
    `id` VARCHAR(36) NOT NULL,
    `job_id` VARCHAR(36) NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `email` VARCHAR(255) NOT NULL,
    `certificate_text` TEXT NULL,
    `status` VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    `error_message` TEXT NULL,
    `certificate_id` VARCHAR(36) NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `completed_at` DATETIME NULL,
    PRIMARY KEY (`id`),
    INDEX `ix_recipients_job_id` (`job_id`),
    INDEX `ix_recipients_status` (`status`),
    CONSTRAINT `fk_recipients_job`
        FOREIGN KEY (`job_id`)
        REFERENCES `generation_jobs` (`id`)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. Table: certificates
-- Stores metadata and local file paths for successfully generated PDFs
CREATE TABLE `certificates` (
    `id` VARCHAR(36) NOT NULL,
    `recipient_id` VARCHAR(36) NOT NULL,
    `job_id` VARCHAR(36) NOT NULL,
    `file_path` VARCHAR(500) NOT NULL,
    `filename` VARCHAR(255) NOT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_certificates_recipient_id` (`recipient_id`),
    INDEX `ix_certificates_job_id` (`job_id`),
    CONSTRAINT `fk_certificates_job`
        FOREIGN KEY (`job_id`)
        REFERENCES `generation_jobs` (`id`)
        ON DELETE CASCADE,
    CONSTRAINT `fk_certificates_recipient`
        FOREIGN KEY (`recipient_id`)
        REFERENCES `recipients` (`id`)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =======================================================
-- Verification Query
-- =======================================================
SHOW TABLES;
