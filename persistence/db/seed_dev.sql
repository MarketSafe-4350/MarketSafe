-- =========================================
-- SEED DATA FOR MARKETPLACE DATABASE
-- MySQL 8.x
-- =========================================

SET FOREIGN_KEY_CHECKS = 0;

TRUNCATE TABLE rating;
TRUNCATE TABLE comment;
TRUNCATE TABLE offer;
TRUNCATE TABLE listing;
TRUNCATE TABLE account;

SET FOREIGN_KEY_CHECKS = 1;

-- =========================================
-- ACCOUNTS
-- =========================================

INSERT INTO account (uuid, email, passwords, fname, lname, verified) VALUES
(UUID(), 'alice@example.com',   SHA2('password123',256), 'Alice',   'Johnson', TRUE),
(UUID(), 'bob@example.com',     SHA2('password123',256), 'Bob',     'Smith', TRUE),
(UUID(), 'carol@example.com',   SHA2('password123',256), 'Carol',   'Brown', FALSE),
(UUID(), 'david@example.com',   SHA2('password123',256), 'David',   'Wilson', TRUE),
(UUID(), 'emma@example.com',    SHA2('password123',256), 'Emma',    'Taylor', TRUE),
(UUID(), 'mohamed@example.com', SHA2('password123',256), 'Mohamed', 'Youssef', TRUE),
(UUID(), 'liam@example.com',    SHA2('password123',256), 'Liam',    'Miller', FALSE),
(UUID(), 'olivia@example.com',  SHA2('password123',256), 'Olivia',  'Davis', TRUE),
(UUID(), 'noah@example.com',    SHA2('password123',256), 'Noah',    'Clark', TRUE),
(UUID(), 'sophia@example.com',  SHA2('password123',256), 'Sophia',  'Lewis', TRUE);

-- =========================================
-- LISTINGS
-- =========================================

INSERT INTO listing (title, description, image_url, price, location, seller_uuid)
SELECT
    'iPhone 13 Pro',
    'Great condition, barely used.',
    'https://example.com/img1.jpg',
    850.00,
    'Winnipeg',
    uuid
FROM account ORDER BY RAND() LIMIT 1;

INSERT INTO listing (title, description, image_url, price, location, seller_uuid)
SELECT
    'Gaming Laptop',
    'RTX graphics, 16GB RAM.',
    'https://example.com/img2.jpg',
    1200.00,
    'Toronto',
    uuid
FROM account ORDER BY RAND() LIMIT 1;

INSERT INTO listing (title, description, image_url, price, location, seller_uuid)
SELECT
    'Office Chair',
    'Ergonomic and comfortable.',
    'https://example.com/img3.jpg',
    150.00,
    'Vancouver',
    uuid
FROM account ORDER BY RAND() LIMIT 1;

INSERT INTO listing (title, description, image_url, price, location, seller_uuid)
SELECT
    'Mountain Bike',
    'Lightweight aluminum frame.',
    'https://example.com/img4.jpg',
    600.00,
    'Calgary',
    uuid
FROM account ORDER BY RAND() LIMIT 1;

-- =========================================
-- OFFERS
-- =========================================

INSERT INTO offer (offered_price, location_offered, listing_id, sender_uuid)
SELECT
    ROUND(l.price * (0.7 + RAND()*0.2), 2),
    l.location,
    l.id,
    a.uuid
FROM listing l
JOIN account a ON a.uuid != l.seller_uuid
ORDER BY RAND()
LIMIT 8;

-- =========================================
-- COMMENTS
-- =========================================

INSERT INTO comment (body, listing_id, author_uuid)
SELECT
    'Is this still available?',
    l.id,
    a.uuid
FROM listing l
JOIN account a ON a.uuid != l.seller_uuid
ORDER BY RAND()
LIMIT 6;

INSERT INTO comment (body, listing_id, author_uuid)
SELECT
    'Can you lower the price?',
    l.id,
    a.uuid
FROM listing l
JOIN account a ON a.uuid != l.seller_uuid
ORDER BY RAND()
LIMIT 6;

-- =========================================
-- RATINGS
-- =========================================

INSERT INTO rating (transaction_rating, listing_id)
SELECT
    FLOOR(1 + RAND()*5),
    id
FROM listing;

-- =========================================
-- OPTIONAL: MARK RANDOM LISTING AS SOLD
-- =========================================

UPDATE listing
SET is_sold = TRUE
ORDER BY RAND()
LIMIT 1;
