-- MySQL 8.x DDL for the ER diagram (Account, Listing, Offer, Comment, Rating)
-- Notes:
-- - Account uses UUID as CHAR(36)
-- - Listing/Offer/Comment/Rating use BIGINT auto-increment IDs
-- - Relationship diamonds map to FKs:
--   * Account (1) posts Listing (M)  -> listing.seller_uuid
--   * Listing (1) has Offer (M)      -> offer.listing_id
--   * Account (1) sends Offer (M)    -> offer.sender_uuid
--   * Account (1) writes Comment (M) -> comment.author_uuid
--   * Listing (1) has Comment (M)    -> comment.listing_id
--   * Listing (1) gets Rating (M)    -> rating.listing_id

CREATE TABLE account (
  uuid         CHAR(36)     NOT NULL,
  email        VARCHAR(255) NOT NULL,
  passwords    VARCHAR(255) NOT NULL,   -- store a password hash, not plaintext
  fname        VARCHAR(80)  NOT NULL,
  lname        VARCHAR(80)  NOT NULL,
  verified     BOOLEAN      NOT NULL DEFAULT FALSE,
  PRIMARY KEY (uuid),
  UNIQUE KEY uq_account_email (email)
) ENGINE=InnoDB;

CREATE TABLE listing (
  id          BIGINT        NOT NULL AUTO_INCREMENT,
  title       VARCHAR(200)  NOT NULL,
  description TEXT          NULL,
  image_url   TEXT          NULL,
  price       DECIMAL(10,2) NOT NULL,
  location    VARCHAR(200)  NULL,
  created_at  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  is_sold     BOOLEAN       NOT NULL DEFAULT FALSE,

  -- Posts relationship: Account (1) -> Listing (M)
  seller_uuid CHAR(36)      NOT NULL,

  PRIMARY KEY (id),
  KEY idx_listing_seller (seller_uuid),
  CONSTRAINT fk_listing_seller
    FOREIGN KEY (seller_uuid) REFERENCES account(uuid)
    ON DELETE RESTRICT
    ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE offer (
  id               BIGINT        NOT NULL AUTO_INCREMENT,
  offered_price    DECIMAL(10,2) NOT NULL,
  location_offered VARCHAR(200)  NULL,
  created_date     DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  seen             BOOLEAN       NOT NULL DEFAULT FALSE,
  accepted         BOOLEAN       NOT NULL DEFAULT FALSE,

  -- Has relationship: Listing (1) -> Offer (M)
  listing_id       BIGINT        NOT NULL,

  -- Send relationship: Account (1) -> Offer (M)
  sender_uuid      CHAR(36)      NOT NULL,

  PRIMARY KEY (id),
  KEY idx_offer_listing (listing_id),
  KEY idx_offer_sender (sender_uuid),

  CONSTRAINT fk_offer_listing
    FOREIGN KEY (listing_id) REFERENCES listing(id)
    ON DELETE CASCADE
    ON UPDATE CASCADE,

  CONSTRAINT fk_offer_sender
    FOREIGN KEY (sender_uuid) REFERENCES account(uuid)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE comment (
  id          BIGINT    NOT NULL AUTO_INCREMENT,
  created_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

  -- (Body/text wasn’t shown clearly on the diagram, but comments usually need it.
  --  Remove this column if you truly don’t want comment text.)
  body        TEXT      NULL,

  -- Listing has Comment (M)
  listing_id  BIGINT    NOT NULL,

  -- Account writes Comment (M)
  author_uuid CHAR(36)  NOT NULL,

  PRIMARY KEY (id),
  KEY idx_comment_listing (listing_id),
  KEY idx_comment_author (author_uuid),

  CONSTRAINT fk_comment_listing
    FOREIGN KEY (listing_id) REFERENCES listing(id)
    ON DELETE CASCADE
    ON UPDATE CASCADE,

  CONSTRAINT fk_comment_author
    FOREIGN KEY (author_uuid) REFERENCES account(uuid)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE rating (
  id                 BIGINT    NOT NULL AUTO_INCREMENT,
  created_at         DATETIME  NOT NULL DEFAULT CURRENT_TIMESTAMP,
  transaction_rating INT       NOT NULL,

  -- Listing gets Rating (M)
  listing_id         BIGINT    NOT NULL,

  PRIMARY KEY (id),
  KEY idx_rating_listing (listing_id),

  CONSTRAINT chk_rating_range
    CHECK (transaction_rating BETWEEN 1 AND 5),

  CONSTRAINT fk_rating_listing
    FOREIGN KEY (listing_id) REFERENCES listing(id)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB;