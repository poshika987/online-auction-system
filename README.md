# Online Auction System

## 1. Introduction
The **Online Auction System** is a comprehensive database application designed to manage the complete lifecycle of online auctions. Built with a **MySQL** backend and a secure **Python (Flask)** API, it streamlines user management, item listing, bidding, payments, and administrative oversight. The system ensures data integrity and fairness through the extensive use of database-level constraints, triggers, and stored procedures.

## 2. Purpose and Scope
The primary purpose of this project is to automate and secure the operations of an auction platform. It aims to eliminate manual errors, prevent invalid transactions (like duplicate payments or low bids), and enforce business rules directly within the database.

## 3. Features
* **User Authentication:** Secure registration and login for customers.
* **Auction Management:** Admins can schedule, start, and cancel auctions.
* **Item Listing:** Items can be added to specific auctions with descriptions and reserve prices.
* **Secure Bidding:** Bids are validated by SQL triggers to ensure they exceed the current highest bid and occur during active auction hours.
* **Automated Lifecycle:** Stored procedures manage auction states (Scheduled -> Active -> Ended -> Completed).
* **Winner Determination:** Automatic identification of the highest bidder meeting the reserve price upon auction closure via stored procedures.
* **Smart Payments:** Winners can view unpaid items and make payments, which automatically updates the auction status to 'Completed'.
* **Database Security:** The system utilizes MySQL Roles to strictly limit database privileges. 

## 4. Technology Stack
* **Database:** MySQL
* **Backend Framework:** Python (Flask)
* **Frontend/Interface:** Command-Line Interface (CLI) built with Python
* **Database Connector:** `mysql-connector-python`
* **HTTP Client:** `requests` library

## 6. Setup and Installation
1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/poshika987/online-auction-system.git
    cd online-auction-system
    ```
2.  **Database Setup:**
    * Open your MySQL client.
    * Run the `Online_Auction.sql` script. This will:
        * Create the database and tables.
        * Setup triggers, procedures, and functions.
        * Create the required database users and roles.
3.  **Backend Setup:**
    * Navigate to the `backend` folder.
    * Install dependencies: `pip install flask mysql-connector-python python-dotenv flask-cors`
    * Configure your `.env` file with your database credentials.
    * Run the server: `python server.py`
4.  **Frontend Setup:**
    * Open a new terminal.
    * Navigate to the `frontend` folder.
    * Run the CLI app: `python app_cli.py`
