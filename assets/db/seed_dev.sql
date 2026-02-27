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
-- - id is AUTO_INCREMENT (do NOT insert it)
-- - email is UNIQUE
-- - password stored as TEXT (demo only)
-- =========================================

INSERT INTO account (email, password, fname, lname, verified) VALUES
('alice@example.com',   'password123', 'Alice',   'Johnson', TRUE),
('bob@example.com',     'password123', 'Bob',     'Smith',   TRUE),
('carol@example.com',   'password123', 'Carol',   'Brown',   FALSE),
('david@example.com',   'password123', 'David',   'Wilson',  TRUE),
('emma@example.com',    'password123', 'Emma',    'Taylor',  TRUE),
('mohamed@example.com', 'password123', 'Mohamed', 'Youssef', TRUE),
('liam@example.com',    'password123', 'Liam',    'Miller',  FALSE),
('olivia@example.com',  'password123', 'Olivia',  'Davis',   TRUE),
('noah@example.com',    'password123', 'Noah',    'Clark',   TRUE),
('sophia@example.com',  'password123', 'Sophia',  'Lewis',   TRUE);


-- =========================================
-- LISTINGS
-- - seller_id references account(id)
-- - sold_to_id is NULL initially (not sold yet)
-- =========================================

INSERT INTO listing (title, description, image_url, price, location, seller_id)
SELECT
  'iPhone 13 Pro',
  'Great condition, barely used.',
  'https://example.com/img1.jpg',
  850.00,
  'Winnipeg',
  a.id
FROM account a
ORDER BY RAND()
LIMIT 1;

INSERT INTO listing (title, description, image_url, price, location, seller_id)
SELECT
  'Gaming Laptop',
  'RTX graphics, 16GB RAM.',
  'https://example.com/img2.jpg',
  1200.00,
  'Toronto',
  a.id
FROM account a
ORDER BY RAND()
LIMIT 1;

INSERT INTO listing (title, description, image_url, price, location, seller_id)
SELECT
  'Office Chair',
  'Ergonomic and comfortable.',
  'https://example.com/img3.jpg',
  150.00,
  'Vancouver',
  a.id
FROM account a
ORDER BY RAND()
LIMIT 1;

INSERT INTO listing (title, description, image_url, price, location, seller_id)
SELECT
  'Mountain Bike',
  'Lightweight aluminum frame.',
  'https://example.com/img4.jpg',
  600.00,
  'Calgary',
  a.id
FROM account a
ORDER BY RAND()
LIMIT 1;

-- =========================================
-- OFFERS
-- - offer.sender_id references account(id)
-- - sender must NOT be the seller
-- - accepted is tri-state: NULL = pending
-- =========================================

INSERT INTO offer (offered_price, location_offered, listing_id, sender_id, accepted)
SELECT
  ROUND(l.price * (0.7 + RAND()*0.2), 2),
  l.location,
  l.id,
  a.id,
  NULL
FROM listing l
JOIN account a ON a.id <> l.seller_id
ORDER BY RAND()
LIMIT 8;

-- =========================================
-- COMMENTS
-- - comment.author_id references account(id)
-- - author must NOT be the seller (optional rule, but realistic)
-- =========================================

INSERT INTO comment (body, listing_id, author_id)
SELECT
  'Is this still available?',
  l.id,
  a.id
FROM listing l
JOIN account a ON a.id <> l.seller_id
ORDER BY RAND()
LIMIT 6;

INSERT INTO comment (body, listing_id, author_id)
SELECT
  'Can you lower the price?',
  l.id,
  a.id
FROM listing l
JOIN account a ON a.id <> l.seller_id
ORDER BY RAND()
LIMIT 6;

-- =========================================
-- MARK SOME LISTINGS AS SOLD
-- IMPORTANT:
-- - trigger requires: if is_sold=TRUE then sold_to_id IS NOT NULL
-- - Buyer must be different from seller (logical)
-- =========================================

UPDATE listing l
JOIN (
  SELECT
    l2.id AS listing_id,
    a2.id AS buyer_id
  FROM listing l2
  JOIN account a2 ON a2.id <> l2.seller_id
  ORDER BY RAND()
  LIMIT 2
) t ON t.listing_id = l.id
SET
  l.is_sold = TRUE,
  l.sold_to_id = t.buyer_id;

-- =========================================
-- RATINGS (buyer-only)
-- IMPORTANT:
-- - UNIQUE(listing_id) => at most one rating per listing
-- - Trigger requires:
--     1) listing is sold
--     2) rater_id = listing.sold_to_id
-- So we ONLY insert ratings for sold listings and set rater_id = sold_to_id
-- =========================================

INSERT INTO rating (transaction_rating, listing_id, rater_id)
SELECT
  FLOOR(1 + RAND()*5),
  l.id,
  l.sold_to_id
FROM listing l
WHERE l.is_sold = TRUE
  AND l.sold_to_id IS NOT NULL;
