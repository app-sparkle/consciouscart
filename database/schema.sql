CREATE DATABASE IF NOT EXISTS consciouscart_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
USE consciouscart_db;

-- 1. Users
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(120) NOT NULL,
    email VARCHAR(190) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_users_email (email)
) ENGINE=InnoDB;

-- 2. User Preferences
CREATE TABLE user_preferences (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    currency_symbol VARCHAR(8) NOT NULL DEFAULT '₹',
    default_safety_reserve_pct DECIMAL(5,2) NOT NULL DEFAULT 20.00,
    theme_mode ENUM('light', 'dark') NOT NULL DEFAULT 'light',
    priority_mode ENUM('balanced', 'organic', 'budget', 'packaging') NOT NULL DEFAULT 'balanced',
    location_notifications_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    reminder_cooldown_minutes INT NOT NULL DEFAULT 120,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_pref_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 3. Product Categories
CREATE TABLE product_categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    slug VARCHAR(80) NOT NULL UNIQUE,
    name VARCHAR(120) NOT NULL,
    icon_name VARCHAR(60) NOT NULL DEFAULT 'leaf',
    description TEXT
) ENGINE=InnoDB;

-- 4. Brands
CREATE TABLE brands (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL UNIQUE,
    transparency_rating DECIMAL(4,2) DEFAULT NULL,
    sourcing_notes TEXT,
    website VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 5. Products
CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category_id INT NOT NULL,
    brand_id INT NOT NULL,
    search_keyword VARCHAR(100) NOT NULL,
    name VARCHAR(200) NOT NULL,
    variant_label VARCHAR(100) NOT NULL,
    tier_category ENUM('premium_organic', 'conscious_choice', 'budget_conscious', 'economy_choice') NOT NULL,
    quantity_value DECIMAL(10,2) NOT NULL,
    quantity_unit VARCHAR(30) NOT NULL,
    image_url VARCHAR(500) NOT NULL,
    packaging_material VARCHAR(120) NOT NULL,
    packaging_recyclable BOOLEAN DEFAULT NULL,
    packaging_notes TEXT,
    environmental_summary TEXT,
    manufacturer_claims TEXT,
    safety_compliance_notes TEXT,
    ingredient_transparency_level ENUM('full', 'partial', 'basic', 'unavailable') NOT NULL DEFAULT 'partial',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_products_keyword (search_keyword),
    INDEX idx_products_category (category_id),
    CONSTRAINT fk_prod_category FOREIGN KEY (category_id) REFERENCES product_categories(id),
    CONSTRAINT fk_prod_brand FOREIGN KEY (brand_id) REFERENCES brands(id)
) ENGINE=InnoDB;

-- 6. Ingredients
CREATE TABLE ingredients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    inci_name VARCHAR(180) NOT NULL UNIQUE,
    common_name VARCHAR(180),
    origin_type ENUM('plant_derived', 'mineral', 'synthetic', 'biotech', 'unknown') NOT NULL DEFAULT 'unknown',
    primary_function VARCHAR(200) NOT NULL,
    environmental_consideration TEXT,
    safety_note TEXT
) ENGINE=InnoDB;

-- 7. Product Ingredients (Junction)
CREATE TABLE product_ingredients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    ingredient_id INT NOT NULL,
    position_order INT NOT NULL DEFAULT 1,
    is_certified_organic_input BOOLEAN NOT NULL DEFAULT FALSE,
    verification_status ENUM('verified', 'manufacturer_claim', 'unverified') NOT NULL DEFAULT 'manufacturer_claim',
    UNIQUE KEY uq_prod_ing (product_id, ingredient_id),
    CONSTRAINT fk_pi_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    CONSTRAINT fk_pi_ingredient FOREIGN KEY (ingredient_id) REFERENCES ingredients(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 8. Organic Certifications
CREATE TABLE organic_certifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    certifier_name VARCHAR(150) NOT NULL,
    certificate_code VARCHAR(120),
    scope ENUM('100_organic', 'organic_ingredients', 'eco_label', 'unverified_claim', 'none') NOT NULL DEFAULT 'none',
    verified_status BOOLEAN NOT NULL DEFAULT FALSE,
    evidence_url VARCHAR(500),
    CONSTRAINT fk_cert_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 9. Product Scores (Transparent Rule-Based Cache)
CREATE TABLE product_scores (
    product_id INT PRIMARY KEY,
    ingredient_score DECIMAL(5,2) NOT NULL,
    organic_score DECIMAL(5,2) NOT NULL,
    environmental_score DECIMAL(5,2) NOT NULL,
    packaging_score DECIMAL(5,2) NOT NULL,
    affordability_score DECIMAL(5,2) NOT NULL,
    total_weighted_score DECIMAL(5,2) NOT NULL,
    ranking_explanation TEXT NOT NULL,
    missing_data_flags JSON,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_score_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 10. Product Prices
CREATE TABLE product_prices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    currency VARCHAR(8) NOT NULL DEFAULT 'INR',
    effective_date DATE NOT NULL,
    is_current BOOLEAN NOT NULL DEFAULT TRUE,
    INDEX idx_price_prod_current (product_id, is_current),
    CONSTRAINT fk_price_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 11. Shopping Lists
CREATE TABLE shopping_lists (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(150) NOT NULL,
    status ENUM('active', 'locked', 'completed', 'archived') NOT NULL DEFAULT 'active',
    is_locked BOOLEAN NOT NULL DEFAULT FALSE,
    planned_subtotal DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    safety_reserve DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    recommended_budget DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_lists_user_status (user_id, status),
    CONSTRAINT fk_list_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 12. Shopping List Items
CREATE TABLE shopping_list_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    shopping_list_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    unit_price_snapshot DECIMAL(10,2) NOT NULL,
    need_classification ENUM('planned_need', 'occasional_purchase') NOT NULL DEFAULT 'planned_need',
    is_purchased BOOLEAN NOT NULL DEFAULT FALSE,
    actual_paid_price DECIMAL(10,2) DEFAULT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_list_product (shopping_list_id, product_id),
    CONSTRAINT fk_sli_list FOREIGN KEY (shopping_list_id) REFERENCES shopping_lists(id) ON DELETE CASCADE,
    CONSTRAINT fk_sli_product FOREIGN KEY (product_id) REFERENCES products(id)
) ENGINE=InnoDB;

-- 13. Saved Locations
CREATE TABLE saved_locations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    location_name VARCHAR(120) NOT NULL,
    location_type ENUM('home', 'supermarket', 'local_grocery', 'other') NOT NULL DEFAULT 'supermarket',
    address_text VARCHAR(300) NOT NULL,
    latitude DECIMAL(10,7) NOT NULL,
    longitude DECIMAL(10,7) NOT NULL,
    radius_meters INT NOT NULL DEFAULT 250,
    reminders_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_loc_user (user_id),
    CONSTRAINT fk_loc_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 14. Location Reminder Logs
CREATE TABLE location_reminder_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    location_id INT NOT NULL,
    triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    distance_meters DECIMAL(8,2) NOT NULL,
    message_sent TEXT NOT NULL,
    INDEX idx_rem_user_loc (user_id, location_id, triggered_at),
    CONSTRAINT fk_rem_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_rem_loc FOREIGN KEY (location_id) REFERENCES saved_locations(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 15. Purchase History
CREATE TABLE purchase_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    shopping_list_id INT DEFAULT NULL,
    store_name VARCHAR(150),
    purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    planned_subtotal DECIMAL(10,2) NOT NULL,
    recommended_budget DECIMAL(10,2) NOT NULL,
    actual_expenditure DECIMAL(10,2) NOT NULL,
    budget_variance DECIMAL(10,2) NOT NULL,
    INDEX idx_ph_user_date (user_id, purchased_at),
    CONSTRAINT fk_ph_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_ph_list FOREIGN KEY (shopping_list_id) REFERENCES shopping_lists(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- 16. Purchase Items
CREATE TABLE purchase_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    purchase_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    line_total DECIMAL(10,2) NOT NULL,
    was_planned BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT fk_phi_purchase FOREIGN KEY (purchase_id) REFERENCES purchase_history(id) ON DELETE CASCADE,
    CONSTRAINT fk_phi_product FOREIGN KEY (product_id) REFERENCES products(id)
) ENGINE=InnoDB;

-- 17. Wishlist
CREATE TABLE wishlist (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    product_id INT NOT NULL,
    reason_note VARCHAR(255) DEFAULT 'Just browsing – evaluating need first',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_wish_user_prod (user_id, product_id),
    CONSTRAINT fk_wish_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_wish_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 18. Pantry Items
CREATE TABLE pantry_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    item_name VARCHAR(150) NOT NULL,
    category_id INT DEFAULT NULL,
    quantity_remaining DECIMAL(10,2) NOT NULL DEFAULT 1.00,
    unit VARCHAR(30) NOT NULL DEFAULT 'units',
    expiry_date DATE DEFAULT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_pantry_user (user_id),
    CONSTRAINT fk_pantry_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 19. Notifications
CREATE TABLE notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    category ENUM('budget', 'location', 'pantry', 'consumption') NOT NULL,
    title VARCHAR(160) NOT NULL,
    body TEXT NOT NULL,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_notif_user_read (user_id, is_read),
    CONSTRAINT fk_notif_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;