drop database auction;
create database auction;
use auction;

create table customer
(
userID varchar(10) not null,
name varchar(50) not null,
phone varchar(15) not null,
email varchar(320) not null,
address varchar(100) not null,
password varchar(10) not null,
primary key(userID)
);

create table auction_item(
itemID varchar(10) not null,
description varchar(50),
title varchar(20) not null,
start_price int not null,
status enum('Sold', 'Listed') default 'Listed',
reserve_price int not null,
primary key(itemID)

);

create table payment(
transactionID varchar(10) primary key,
amount int not null,
paymentMethod enum('UPI','Credit/Debit Card','Net Banking') not null,
PaymentDate date,
CustomerId varchar(10),
constraint fk_cust_key foreign key (customerId) references customer(userId) on delete set null on update cascade
);

create table bid(
bidID varchar(36) primary key,
amount int not null,
bid_time timestamp not null default current_timestamp,
custID varchar(10),
itemID varchar(10),
constraint fk_cust_key1 foreign key (custID) references customer(userId) on delete set null on update cascade,
constraint fk_item_key foreign key (itemID) references auction_item(itemID) on delete set null on update cascade
);

create table category (
categoryID varchar(10) primary key,
description varchar(50) not null,
name varchar(20) not null
);

create table auction(
auctionID varchar(10) primary key,
auction_name varchar(20) not null,
start_time datetime not null,
end_time datetime not null,
status enum('Scheduled','Active','Ended','Completed','Cancelled') default 'Scheduled', -- Ended is when bids are no longer accepted and completed is when auctioneer announces highest bid
userID varchar(10),
constraint fk_cust_key2 foreign key (userID) references customer(userID) on delete set null on update cascade
);

alter table auction_item add column transactionID VARCHAR(10) NULL;
alter table auction_item add column categoryID VARCHAR(10);
alter table auction_item add column auctionID VARCHAR(10);

alter table auction_item add constraint fk_transaction foreign key (transactionID) references payment(transactionID) on update cascade on delete restrict; -- no refund policy
alter table auction_item add constraint fk_category foreign key (categoryID) references category(categoryID) on update cascade on delete set null;
alter table auction_item add constraint fk_auction foreign key (auctionID) references auction(auctionID) on update cascade on delete set null;

ALTER TABLE payment ADD COLUMN itemID VARCHAR(10);
ALTER TABLE payment ADD CONSTRAINT fk_payment_item FOREIGN KEY (itemID) REFERENCES auction_item(itemID);

INSERT INTO customer VALUES
('C001','Alice Johnson','9876543210','alice@example.com','Delhi','pass123'),
('C002','Bob Smith','9123456789','bob@example.com','Mumbai','pass234'),
('C003','Charlie Brown','9988776655','charlie@example.com','Bangalore','pass345'),
('C004','Diana Ross','9112233445','diana@example.com','Kolkata','pass456'),
('C005','Evan Lee','9332211445','evan@example.com','Chennai','pass567');

INSERT INTO category VALUES
('CAT01','Electronic devices','Electronics'),
('CAT02','Home furniture items','Furniture'),
('CAT03','Artwork and paintings','Art'),
('CAT04','Books and novels','Books'),
('CAT05','Sports equipment','Sports');

INSERT INTO auction VALUES
('A001','ElectronicsSale','2025-09-01 10:00:00','2025-09-05 18:00:00','Active','C001'),
('A002','ArtAuction','2025-09-02 09:00:00','2025-09-06 17:00:00','Scheduled','C002'),
('A003','BookFair','2025-09-03 12:00:00','2025-09-07 20:00:00','Scheduled','C003'),
('A004','SportsBonanza','2025-09-04 08:00:00','2025-09-08 19:00:00','Scheduled','C004'),
('A005','FurnitureFest','2025-09-05 11:00:00','2025-09-09 21:00:00','Scheduled','C005');

INSERT INTO auction_item VALUES
('I001','iPhone 14','Apple iPhone',40000,'Listed',45000,NULL,'CAT01','A001'),
('I002','Wooden Dining Table','Dining Table',12000,'Listed',15000,NULL,'CAT02','A005'),
('I003','Abstract Art','Modern Painting',3000,'Listed',5000,NULL,'CAT03','A002'),
('I004','Cricket Bat','SS Bat',5000,'Listed',7000,NULL,'CAT05','A004'),
('I005','Harry Potter Set','Book Series',2000,'Listed',3000,NULL,'CAT04','A003');

INSERT INTO bid VALUES
('BID001',42000,NOW(),'C002','I001'),
('BID002',12500,NOW(),'C003','I002'),
('BID03',3500,NOW(),'C004','I003'),
('BID004',5500,NOW(),'C005','I004'),
('BID005',2500,NOW(),'C001','I005');

INSERT INTO payment (transactionID, amount, paymentMethod, PaymentDate, CustomerId, itemID) VALUES
('T001', 42000, 'UPI', '2025-09-06', 'C002', 'I001'),
('T002', 12500, 'Credit/Debit Card', '2025-09-07', 'C003', 'I002'),
('T003', 3500, 'Net Banking', '2025-09-07', 'C004', 'I003'),
('T004', 5500, 'UPI', '2025-09-08', 'C005', 'I004'),
('T005', 2500, 'Credit/Debit Card', '2025-09-08', 'C001', 'I005');

-- Trigger to prevent deletion of customers with active payments or bids
DELIMITER $$
CREATE TRIGGER before_customer_delete
BEFORE DELETE ON customer
FOR EACH ROW
BEGIN
    DECLARE active_bids INT;
    DECLARE active_payments INT;

    SELECT COUNT(*) INTO active_bids 
    FROM bid 
    WHERE custID = OLD.userID;

    SELECT COUNT(*) INTO active_payments 
    FROM payment 
    WHERE CustomerId = OLD.userID;

    IF active_bids > 0 OR active_payments > 0 THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'Cannot delete customer with active bids or payments.';
    END IF;
END$$
DELIMITER ;

-- Trigger to check for duplicate payments and only allow payments for sold items
DELIMITER $$
CREATE TRIGGER before_payment_insert
BEFORE INSERT ON payment
FOR EACH ROW
BEGIN
    DECLARE v_paid INT;
    DECLARE v_status ENUM('Sold','Listed');

    -- Check for duplicate transaction IDs
    SELECT COUNT(*) INTO v_paid 
    FROM payment 
    WHERE transactionID = NEW.transactionID;

    IF v_paid > 0 THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'Duplicate payment detected.';
    END IF;

    -- Check the status of the *specific item* this payment is for
    SELECT status INTO v_status 
    FROM auction_item 
    WHERE itemID = NEW.itemID; 

    -- Only allow payment if the item is marked as 'Sold'
    IF v_status != 'Sold' THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'Payment only allowed for items marked as ''Sold''.';
    END IF;
END$$
DELIMITER ;

-- Stored procedure to update status of  scheduled auction to active when start time has passed
DELIMITER $$
CREATE PROCEDURE sp_start_auction()
BEGIN
    UPDATE auction
    SET status = 'Active'
    WHERE status = 'Scheduled' 
      AND start_time <= NOW();

    SELECT 'Auctions started successfully.' AS Result;
END$$
DELIMITER ;

-- Stored procedure to cancel auction and reset unsold items
DELIMITER $$
CREATE PROCEDURE sp_cancel_auction(
    IN p_auctionID VARCHAR(10)
)
BEGIN
    UPDATE auction
    SET status = 'Cancelled'
    WHERE auctionID = p_auctionID;

    UPDATE auction_item
    SET status = 'Listed',
        transactionID = NULL
    WHERE auctionID = p_auctionID
      AND status != 'Sold';

    SELECT CONCAT('Auction ', p_auctionID, ' cancelled and items reverted.') AS Result;
END$$
DELIMITER ;

-- TRIGGER: before_bid_insert
-- Purpose: Validates all new bids before they are inserted.
-- Checks: 1. Auction is 'Active'. 2. NOW() is within auction time. 3. Bid is high enough.
DELIMITER $$
CREATE TRIGGER before_bid_insert
BEFORE INSERT ON bid
FOR EACH ROW
BEGIN
    DECLARE v_auction_status ENUM('Scheduled','Active','Ended','Completed','Cancelled');
    DECLARE v_auction_start DATETIME;
    DECLARE v_auction_end DATETIME;
    DECLARE v_start_price INT;
    DECLARE v_current_max_bid INT;

    -- 1. Get the auction status, times, and item start price
    SELECT a.status, a.start_time, a.end_time, ai.start_price
    INTO v_auction_status, v_auction_start, v_auction_end, v_start_price
    FROM auction a
    JOIN auction_item ai ON a.auctionID = ai.auctionID
    WHERE ai.itemID = NEW.itemID;

    -- 2. Check if the auction is active and within the time window
    IF v_auction_status != 'Active' OR NOW() NOT BETWEEN v_auction_start AND v_auction_end THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Bidding is not allowed. The auction is not active or is outside the bidding window.';
    END IF;

    -- 3. Get the current highest bid for this item
    SELECT MAX(amount) INTO v_current_max_bid FROM bid WHERE itemID = NEW.itemID;

    -- 4. Check if the new bid is high enough
    IF NEW.amount <= IFNULL(v_current_max_bid, v_start_price) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Your bid is too low. It must be higher than the current highest bid or the start price.';
    END IF;
END$$
DELIMITER ;

-- PROCEDURE: sp_place_bid
-- Purpose: Simplifies the process of placing a bid. Uses UUID() for a unique bidID.
DELIMITER $$
CREATE PROCEDURE sp_place_bid(
    IN p_custID VARCHAR(10),
    IN p_itemID VARCHAR(10),
    IN p_amount INT
)
BEGIN
    INSERT INTO bid (bidID, custID, itemID, amount, bid_time)
    VALUES (UUID(), p_custID, p_itemID, p_amount, NOW());
    
    SELECT 'Bid placed successfully.' AS message;
END$$
DELIMITER ;


-- TEST BLOCK FOR: before_bid_insert
-- SETUP: Make sure Auction A001 is 'Active' and the time is valid.
-- This is needed for the 'before_bid_insert' trigger's first check to pass.
UPDATE auction
SET 
    status = 'Active',
    start_time = NOW() - INTERVAL 1 DAY, 
    end_time = NOW() + INTERVAL 2 DAY  
WHERE 
    auctionID = 'A001';

-- CASE 1.1: 'before_bid_insert' IS CALLED (and FAILS validation)
CALL sp_place_bid('C001', 'I001', 40000); -- This will fail (bid too low)

-- CASE 1.2: 'before_bid_insert' IS CALLED (and PASSES)
CALL sp_place_bid('C005', 'I001', 43000); -- This will work

-- PROCEDURE: sp_finalize_auction_item
-- Purpose: Checks winning bid against reserve price and updates item status to 'Sold'.
-- Run this after an auction status has been manually set to 'Ended'.
DELIMITER $$
CREATE PROCEDURE sp_finalize_auction_item(
    IN p_itemID VARCHAR(10)
)
BEGIN
    DECLARE v_winning_bid INT;
    DECLARE v_winning_custID VARCHAR(10);
    DECLARE v_reserve_price INT;
    DECLARE v_auction_status ENUM('Scheduled','Active','Ended','Completed','Cancelled');

    -- Get the auction status to make sure it's actually over
    SELECT a.status, ai.reserve_price
    INTO v_auction_status, v_reserve_price
    FROM auction_item ai
    JOIN auction a ON ai.auctionID = a.auctionID
    WHERE ai.itemID = p_itemID;

    -- Only proceed if the auction has 'Ended'
    IF v_auction_status = 'Ended' THEN
        -- Find the highest bid and the bidder
        SELECT amount, custID
        INTO v_winning_bid, v_winning_custID
        FROM bid
        WHERE itemID = p_itemID
        ORDER BY amount DESC
        LIMIT 1;

        -- Check if any bids were placed
        IF v_winning_bid IS NOT NULL THEN
            -- Check if the highest bid met the reserve price
            IF v_winning_bid >= v_reserve_price THEN
                UPDATE auction_item
                SET status = 'Sold'
                WHERE itemID = p_itemID;
                
                SELECT CONCAT('Item ', p_itemID, ' sold to ', v_winning_custID, ' for ', v_winning_bid) AS Result;
            ELSE
                SELECT CONCAT('Item ', p_itemID, ' not sold. Reserve price of ', v_reserve_price, ' not met.') AS Result;
            END IF;
        ELSE
            SELECT CONCAT('Item ', p_itemID, ' not sold. No bids received.') AS Result;
        END IF;
    ELSE
        SELECT CONCAT('Cannot finalize item. Auction status is: ', v_auction_status) AS Result;
    END IF;
END$$
DELIMITER ; 


-- TEST BLOCK FOR: sp_finalize_auction_item

-- CASE 7.1: PROCEDURE IS CALLED (Item NOT sold - Reserve not met)
UPDATE auction SET status = 'Ended' WHERE auctionID = 'A001';

CALL sp_finalize_auction_item('I001');
-- Verify status is unchanged
SELECT status FROM auction_item WHERE itemID = 'I001'; -- Should still be 'Listed'

-- CASE 7.2: PROCEDURE IS CALLED (Item IS sold - Reserve met)
UPDATE auction SET status = 'Active', start_time = NOW() - INTERVAL 1 DAY, end_time = NOW() + INTERVAL 1 DAY WHERE auctionID = 'A004';
CALL sp_place_bid('C001', 'I004', 7500); -- Bid 7500 (is >= reserve of 7000)
-- Now, end the auction
UPDATE auction SET status = 'Ended' WHERE auctionID = 'A004';
-- This call will result in "Item I004 sold"
CALL sp_finalize_auction_item('I004');
-- Verify status is now 'Sold'
SELECT status FROM auction_item WHERE itemID = 'I004'; -- Should now be 'Sold'


-- FUNCTION: get_current_price
-- Purpose: Returns the current highest bid for an item, or its start price if no bids exist.
DELIMITER $$
CREATE FUNCTION get_current_price(
    p_itemID VARCHAR(10)
)
RETURNS INT
READS SQL DATA
BEGIN
    DECLARE v_max_bid INT;
    DECLARE v_start_price INT;

    -- Get the highest bid
    SELECT MAX(amount) INTO v_max_bid FROM bid WHERE itemID = p_itemID;

    -- If no bids, get the start price
    IF v_max_bid IS NULL THEN
        SELECT start_price INTO v_start_price FROM auction_item WHERE itemID = p_itemID;
        RETURN v_start_price;
    ELSE
        RETURN v_max_bid;
    END IF;
END$$

DELIMITER ;

-- TEST BLOCK FOR: get_current_price

SELECT 
    title, 
    get_current_price(itemID) AS current_price
FROM 
    auction_item
WHERE 
    itemID IN ('I001', 'I004', 'I005');
    
    
-- TRIGGER: after_item_payment
-- Purpose: Checks if all items in an auction are paid for after an
--          item's payment is registered (by updating its transactionID).
--          If all items are paid, it updates the parent auction 
--          status to 'Completed'.

DELIMITER $$

CREATE TRIGGER after_item_payment
AFTER UPDATE ON auction_item
FOR EACH ROW
BEGIN
    DECLARE v_total_items INT;
    DECLARE v_paid_items INT;
    DECLARE v_auction_id_to_check VARCHAR(10);

    -- This logic only runs if the transactionID was just added
    -- (i.e., the item's status changed from unpaid to paid)
    IF NEW.transactionID IS NOT NULL AND OLD.transactionID IS NULL THEN
    
        SET v_auction_id_to_check = NEW.auctionID;

        -- 1. Count the total number of items in this auction
        SELECT COUNT(*)
        INTO v_total_items
        FROM auction_item
        WHERE auctionID = v_auction_id_to_check;

        -- 2. Count the number of items in this auction that have a payment
        SELECT COUNT(*)
        INTO v_paid_items
        FROM auction_item
        WHERE auctionID = v_auction_id_to_check
        AND transactionID IS NOT NULL;

        -- 3. If all items in the auction are paid for,
        --    mark the entire auction as 'Completed'.
        IF v_total_items = v_paid_items THEN
            UPDATE auction
            SET status = 'Completed'
            WHERE auctionID = v_auction_id_to_check;
        END IF;

    END IF;
END$$

DELIMITER ;

-- TEST BLOCK FOR: after_item_payment

-- CASE 2.1: TRIGGER IS CALLED
-- We simulate a payment by setting the transactionID from NULL to 'T001'.

UPDATE auction_item 
SET transactionID = 'T004' 
WHERE itemID = 'I004';

SELECT status FROM auction WHERE auctionID = 'A004'; -- The status should now be 'Completed'


-- TEST BLOCK FOR: before_customer_delete


-- CASE 3.1: TRIGGER IS CALLED (and FAILS validation)
-- Customer 'C001' has bids ('BID005', etc.) and payments ('T005').
-- The trigger will count these and block the DELETE.
DELETE FROM customer WHERE userID = 'C001'; -- This will fail

-- CASE 3.2: TRIGGER IS CALLED (and PASSES)
-- We create a new customer with no history, then delete them.
INSERT INTO customer VALUES
('C999','Test User','1111111111','test@example.com','Test Address','testpass');
-- This DELETE fires the trigger. The trigger finds 0 bids and 0 payments
-- and allows the DELETE to proceed.
DELETE FROM customer WHERE userID = 'C999';

-- TEST BLOCK FOR: before_payment_insert

-- CASE 4.1: TRIGGER IS CALLED (and FAILS - Duplicate payment)
-- We try to insert a payment with transactionID 'T001', which already exists.
-- The trigger's first check will catch this and raise an error.
-- (We use 'I004' as it's 'Sold', so we pass the *second* check)
INSERT INTO payment (transactionID, amount, paymentMethod, PaymentDate, CustomerId, itemID) 
VALUES ('T001', 99, 'UPI', NOW(), 'C001', 'I004'); -- This will fail (Duplicate transactionID)

-- CASE 4.2: TRIGGER IS CALLED (and FAILS - Item not Sold)
-- We try to insert a payment for item 'I002', which is still 'Listed'.
-- We use a new transactionID 'T998' to pass the *first* check.
INSERT INTO payment (transactionID, amount, paymentMethod, PaymentDate, CustomerId, itemID) 
VALUES ('T998', 99, 'UPI', NOW(), 'C001', 'I002'); -- This will fail (I002 is 'Listed')

-- CASE 4.3: TRIGGER IS CALLED (and SUCCEEDS)
-- We use item 'I004' which was marked 'Sold' in test 7.2.
-- We use a new transactionID 'T999'.
-- NOTE: We already added payment 'T004' for item 'I004', but the trigger
-- doesn't prevent multiple payments for the same item, only duplicate Transaction IDs.
INSERT INTO payment (transactionID, amount, paymentMethod, PaymentDate, CustomerId, itemID) 
VALUES ('T1000', 99, 'UPI', CURDATE(), 'C001', 'I004'); -- This will succeed 

-- Verify insert
SELECT * FROM payment WHERE transactionID = 'T1000';


-- TEST BLOCK FOR: sp_start_auction

-- CASE 5.1: PROCEDURE IS CALLED
-- SETUP: Auction 'A002' is 'Scheduled' for a future date.
-- We update it to be in the past so the procedure will find it.
UPDATE auction 
SET start_time = NOW() - INTERVAL 1 DAY 
WHERE auctionID = 'A002';
-- Check status before:
SELECT status FROM auction WHERE auctionID = 'A002'; -- Should be 'Scheduled'
-- CALL the procedure
CALL sp_start_auction();
-- Check status after:
SELECT status FROM auction WHERE auctionID = 'A002'; -- Should now be 'Active'


-- TEST BLOCK FOR: sp_cancel_auction


-- CASE 6.1: PROCEDURE IS CALLED
-- We will cancel Auction 'A003', which contains item 'I005'.
-- Check status before:
SELECT status FROM auction WHERE auctionID = 'A003'; -- Should be 'Scheduled'
SELECT status FROM auction_item WHERE itemID = 'I005'; -- Should be 'Listed'
-- CALL the procedure
CALL sp_cancel_auction('A003');
-- Check status after:
SELECT status FROM auction WHERE auctionID = 'A003'; -- Should be 'Cancelled'
SELECT status FROM auction_item WHERE itemID = 'I005'; -- Should still be 'Listed'

-- Test for sp_place_bid
UPDATE auction
SET 
    status = 'Active',
    start_time = NOW() - INTERVAL 1 DAY,
    end_time = NOW() + INTERVAL 1 DAY
WHERE 
    auctionID = 'A005';
CALL sp_place_bid('C001', 'I002', 13000);
SELECT * FROM bid WHERE amount = 13000;