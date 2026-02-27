-- MySQL 8.x DDL for the ER diagram (Account, Listing, Offer, Comment, Rating)
-- This schema models a simple marketplace where:
-- - Accounts can post listings
-- - Other accounts can make offers on listings
-- - Accounts can comment on listings
-- - A listing can be sold to one buyer, and ONLY that buyer can leave ONE rating

-- Notes / Design decisions:
-- - Primary keys are BIGINT UNSIGNED AUTO_INCREMENT for compact, fast indexing and joins.
-- - All tables use ENGINE=InnoDB to support transactions, row-level locking, and foreign keys.
-- - Foreign keys use ON DELETE CASCADE / ON UPDATE CASCADE so deleting a parent row cleans up related rows.
-- - TEXT is used for fields where we do not want to set an explicit maximum length.
-- - Monetary values use DECIMAL(10,2) to avoid floating-point rounding errors.
-- - Timestamps default to CURRENT_TIMESTAMP for automatic creation time capture.

-- Relationship mappings (cardinality + FK columns):
-- * Account (1) posts Listing (M)
--     listing.seller_id → account.id
--
-- * Listing (1) has Offer (M)
--     offer.listing_id → listing.id
--
-- * Account (1) sends Offer (M)
--     offer.sender_id → account.id
--
-- * Listing (1) has Comment (M)
--     comment.listing_id → listing.id
--
-- * Account (1) writes Comment (M)
--     comment.author_id → account.id
--
-- * Listing (1) gets Rating (0..1)  (one rating per listing, because one buyer)
--     rating.listing_id → listing.id   (UNIQUE on listing_id enforces at most one rating per listing)
--
-- * Account (1) gives Rating (M)
--     rating.rater_id → account.id
--
-- * Listing (0..1) is sold to Account (0..M)
--     listing.sold_to_id → account.id

-- Deletion behavior (due to ON DELETE CASCADE):
-- - Deleting an Account deletes:
--     • Listings they posted (and all offers/comments/ratings under those listings)
--     • Offers they sent
--     • Comments they wrote
--     • Ratings they made
--     • Listings where they were the buyer (sold_to_id) will also be deleted (since it cascades)
--
-- - Deleting a Listing deletes:
--     • All offers on that listing
--     • All comments on that listing
--     • The rating on that listing (if present)
--
-- Business rules enforced by triggers:
-- - A listing cannot be marked sold (is_sold=TRUE) unless sold_to_id is set.
-- - A rating can only be inserted/updated if the listing is sold AND the rater is the buyer.
-- - One rating per listing is enforced by UNIQUE(listing_id).

CREATE TABLE account (
  id        BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  -- Email is VARCHAR so we can enforce uniqueness efficiently with a standard UNIQUE index
  email     VARCHAR(255)    NOT NULL,
  -- Password should store a hash (bcrypt/argon2/etc.), kept as TEXT to avoid max-length constraints
  password  TEXT            NOT NULL,
  fname     TEXT            NOT NULL,
  lname     TEXT            NOT NULL,
  verified  BOOLEAN         NOT NULL DEFAULT FALSE,

  PRIMARY KEY (id),
  UNIQUE KEY uq_account_email (email)
) ENGINE=InnoDB;

CREATE TABLE listing (
  id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  -- Seller (poster) account id
  seller_id   BIGINT UNSIGNED NOT NULL,

  title       TEXT NOT NULL,
  description TEXT NOT NULL,
  image_url   TEXT,
  price       DECIMAL(10,2) NOT NULL,
  location    TEXT,
  created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  -- Marks whether the listing has been sold
  is_sold     BOOLEAN NOT NULL DEFAULT FALSE,

  -- Buyer account id (must be set when is_sold is TRUE; enforced by trigger)
  sold_to_id  BIGINT UNSIGNED NULL,

  PRIMARY KEY (id),

  -- Indexes to speed up common queries:
  -- - Fetch all listings by seller
  -- - Fetch all listings bought by a buyer
  -- - Sort or filter by created time and sold state
  KEY idx_listing_seller_id (seller_id),
  KEY idx_listing_sold_to_id (sold_to_id),
  KEY idx_listing_created_at (created_at),
  KEY idx_listing_is_sold (is_sold),

  -- If a seller account is deleted, delete their listings
  CONSTRAINT fk_listing_seller
    FOREIGN KEY (seller_id) REFERENCES account(id)
    ON DELETE CASCADE
    ON UPDATE CASCADE,

  -- If a buyer account is deleted, delete listings where they were the recorded buyer
  CONSTRAINT fk_listing_sold_to
    FOREIGN KEY (sold_to_id) REFERENCES account(id)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE offer (
  id               BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  offered_price    DECIMAL(10,2)   NOT NULL,
  location_offered TEXT            NULL,
  created_date     DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  seen             BOOLEAN         NOT NULL DEFAULT FALSE,
  -- Tri-state:
  --   NULL  = pending
  --   TRUE  = accepted
  --   FALSE = rejected
  accepted         BOOLEAN         NULL DEFAULT NULL,

  -- Offer belongs to exactly one listing (Listing 1 -> Offer M)
  listing_id       BIGINT UNSIGNED NOT NULL,

  -- Offer is sent by exactly one account (Account 1 -> Offer M)
  sender_id        BIGINT UNSIGNED NOT NULL,

  PRIMARY KEY (id),

  -- Indexes for fast lookups by listing and sender
  KEY idx_offer_listing (listing_id),
  KEY idx_offer_sender (sender_id),

  -- If a listing is deleted, delete its offers
  CONSTRAINT fk_offer_listing
    FOREIGN KEY (listing_id) REFERENCES listing(id)
    ON DELETE CASCADE
    ON UPDATE CASCADE,

  -- If a sender account is deleted, delete offers they sent
  CONSTRAINT fk_offer_sender
    FOREIGN KEY (sender_id) REFERENCES account(id)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE comment (
  id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  created_date DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

  -- Comment text/body
  body         TEXT            NULL,

  -- Comment belongs to exactly one listing (Listing 1 -> Comment M)
  listing_id   BIGINT UNSIGNED NOT NULL,

  -- Comment is authored by exactly one account (Account 1 -> Comment M)
  author_id    BIGINT UNSIGNED NOT NULL,

  PRIMARY KEY (id),

  -- Indexes for fast lookups by listing and author
  KEY idx_comment_listing (listing_id),
  KEY idx_comment_author (author_id),

  -- If a listing is deleted, delete its comments
  CONSTRAINT fk_comment_listing
    FOREIGN KEY (listing_id) REFERENCES listing(id)
    ON DELETE CASCADE
    ON UPDATE CASCADE,

  -- If an author account is deleted, delete their comments
  CONSTRAINT fk_comment_author
    FOREIGN KEY (author_id) REFERENCES account(id)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE rating (
  id                 BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  created_at         DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  transaction_rating INT             NOT NULL,

  -- Rating is associated with a listing
  listing_id         BIGINT UNSIGNED NOT NULL,
  -- Rating is created by an account (must be the buyer; enforced by trigger)
  rater_id           BIGINT UNSIGNED NOT NULL,

  PRIMARY KEY (id),

  -- Enforces ONE rating per listing (since there is only one buyer for a listing)
  UNIQUE KEY uq_rating_one_per_listing (listing_id),
  -- Helps query "all ratings by a user"
  KEY idx_rating_rater (rater_id),

  -- If a listing is deleted, delete its rating
  CONSTRAINT fk_rating_listing
    FOREIGN KEY (listing_id) REFERENCES listing(id)
    ON DELETE CASCADE
    ON UPDATE CASCADE,

  -- If the rater account is deleted, delete their rating(s)
  CONSTRAINT fk_rating_rater
    FOREIGN KEY (rater_id) REFERENCES account(id)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB;

-- =========================================================
-- Triggers for business rules enforcement
-- =========================================================

DELIMITER $$

-- Enforce: listing must be sold AND rater must be the buyer before inserting a rating
CREATE TRIGGER trg_rating_only_buyer_ins
BEFORE INSERT ON rating
FOR EACH ROW
BEGIN
  DECLARE buyer_id BIGINT UNSIGNED;
  DECLARE sold_flag BOOLEAN;

  -- Look up the buyer and sold state from the listing
  SELECT sold_to_id, is_sold
    INTO buyer_id, sold_flag
  FROM listing
  WHERE id = NEW.listing_id;

  -- Cannot rate an unsold listing
  IF sold_flag = FALSE OR buyer_id IS NULL THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Cannot rate: listing not sold';
  END IF;

  -- Only the buyer can rate the listing
  IF NEW.rater_id <> buyer_id THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Only the buyer can rate this listing';
  END IF;
END$$

-- Enforce the same rule on updates (prevents changing rater_id to someone else, etc.)
CREATE TRIGGER trg_rating_only_buyer_upd
BEFORE UPDATE ON rating
FOR EACH ROW
BEGIN
  DECLARE buyer_id BIGINT UNSIGNED;
  DECLARE sold_flag BOOLEAN;

  SELECT sold_to_id, is_sold
    INTO buyer_id, sold_flag
  FROM listing
  WHERE id = NEW.listing_id;

  IF sold_flag = FALSE OR buyer_id IS NULL THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Cannot rate: listing not sold';
  END IF;

  IF NEW.rater_id <> buyer_id THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Only the buyer can rate this listing';
  END IF;
END$$

DELIMITER ;

CREATE TABLE email_verification_tokens (
  id             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  account_id     BIGINT UNSIGNED NOT NULL,
  token_hash     VARCHAR(255)    NOT NULL,
  created_at     DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  expires_at     DATETIME        NOT NULL,
  used           BOOLEAN         NOT NULL DEFAULT FALSE,
  used_at        DATETIME        NULL,

  PRIMARY KEY (id),

  -- Index for fast token lookups
  KEY idx_email_token_hash (token_hash),
  -- Index for finding unused tokens by account
  KEY idx_email_token_account (account_id, used),

  -- Foreign key to account table
  CONSTRAINT fk_email_token_account
    FOREIGN KEY (account_id) REFERENCES account(id)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB;

DELIMITER $$

-- Enforce: if a listing is marked sold, a buyer must be provided
CREATE TRIGGER trg_listing_sold_requires_buyer
BEFORE UPDATE ON listing
FOR EACH ROW
BEGIN
  IF NEW.is_sold = TRUE AND NEW.sold_to_id IS NULL THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'sold_to_id must be set when is_sold is TRUE';
  END IF;
END$$

DELIMITER ;
