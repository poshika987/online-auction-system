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
bidID varchar(20) primary key,
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
('BID003',3500,NOW(),'C004','I003'),
('BID004',5500,NOW(),'C005','I004'),
('BID005',2500,NOW(),'C001','I005');

INSERT INTO payment VALUES
('T001',42000,'UPI','2025-09-06','C002'),   
('T002',12500,'Credit/Debit Card','2025-09-07','C003'),
('T003',3500,'Net Banking','2025-09-07','C004'), 
('T004',5500,'UPI','2025-09-08','C005'),
('T005',2500,'Credit/Debit Card','2025-09-08','C001');
