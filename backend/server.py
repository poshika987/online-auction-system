from flask import Flask, jsonify, request
from flask_cors import CORS
import mysql.connector
from db_connector import get_user_connection, get_admin_connection
import uuid
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Helper function
def get_proc_result(cursor):
    try:
        for res in cursor.stored_results():
            return res.fetchone()
    except mysql.connector.Error as e:
        print(f"Error fetching stored proc result: {e}")
        return None

# CUSTOMER-FACING ENDPOINTS 

@app.route('/')
def home():
    return "Auction Backend Server is running!"

@app.route('/login', methods=['POST'])
def login():
    """ (NEW) Logs in a customer. """
    data = request.get_json()
    if not data or 'userID' not in data or 'password' not in data:
        return jsonify({"error": "Missing userID or password"}), 400

    conn = None
    cursor = None
    try:
        conn = get_user_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if the user exists and the password is correct
        cursor.execute(
            "SELECT userID, name FROM customer WHERE userID = %s AND password = %s",
            (data['userID'], data['password'])
        )
        customer = cursor.fetchone()
        
        if customer:
            # Can return a JWT token instead of confirming success
            return jsonify({"message": "Login successful", "customer": customer}), 200
        else:
            return jsonify({"error": "Invalid userID or password"}), 401 

    except mysql.connector.Error as e:
        print(f"Error: {e}")
        return jsonify({"error": "Database error", "details": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/items', methods=['GET'])
def get_all_items():
    conn = None
    cursor = None
    try:
        conn = get_user_connection() 
        if conn is None:
            return jsonify({"error": "Could not connect to database"}), 500
        
        cursor = conn.cursor(dictionary=True)
        query = """
        SELECT itemID, title, description, start_price, reserve_price, 
               categoryID, auctionID, get_current_price(itemID) AS current_price
        FROM auction_item WHERE status = 'Listed';
        """
        cursor.execute(query)
        items = cursor.fetchall()
        return jsonify(items), 200
    except mysql.connector.Error as e:
        return jsonify({"error": "Database error", "details": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/bid', methods=['POST'])
def place_bid():
    data = request.get_json()
    if not data or 'custID' not in data or 'itemID' not in data or 'amount' not in data:
        return jsonify({"error": "Missing data"}), 400
    
    if not isinstance(data['amount'], int):
        return jsonify({"error": "Invalid data type. 'amount' must be an integer."}), 400
        
    p_custID, p_itemID, p_amount = data['custID'], data['itemID'], data['amount']
    conn = None
    cursor = None
    try:
        conn = get_user_connection() 
        if conn is None:
            return jsonify({"error": "Could not connect to database"}), 500
            
        cursor = conn.cursor(dictionary=True)
        cursor.callproc('sp_place_bid', (p_custID, p_itemID, p_amount))
        conn.commit()
        result = get_proc_result(cursor)
        return jsonify({"message": "Bid placed successfully!", "result": result}), 201
    except mysql.connector.Error as e:
        if e.sqlstate == '45000': 
            return jsonify({"error": "Bid rejected", "details": e.msg}), 400
        else:
            return jsonify({"error": "Database error", "details": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/customers', methods=['GET'])
def get_customers():
    conn = None
    cursor = None
    try:
        conn = get_user_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT userID, name, email, phone FROM customer;")
        customers = cursor.fetchall()
        return jsonify(customers), 200
    except mysql.connector.Error as e:
        return jsonify({"error": "Database error", "details": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/customers', methods=['POST'])
def create_customer():
    data = request.get_json()
    required = ['userID', 'name', 'phone', 'email', 'address', 'password']
    if not data or not all(field in data for field in required):
        return jsonify({"error": "Missing data"}), 400

    conn = None
    cursor = None
    try:
        conn = get_user_connection()
        cursor = conn.cursor()
        query = "INSERT INTO customer VALUES (%s, %s, %s, %s, %s, %s)"
        cursor.execute(query, (data['userID'], data['name'], data['phone'], 
                               data['email'], data['address'], data['password']))
        conn.commit()
        return jsonify({"message": "Customer created successfully"}), 201
    except mysql.connector.Error as e:
        return jsonify({"error": "Database error", "details": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/items/<string:itemID>', methods=['GET'])
def get_item_by_id(itemID):
    """ (MODIFIED) Gets details for a single item, including current price and winner's name. """
    conn = None
    cursor = None
    try:
        conn = get_user_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
        SELECT 
            ai.itemID, ai.title, ai.description, ai.start_price, 
            ai.status, ai.reserve_price, ai.categoryID, ai.auctionID, 
            ai.winnerID,
            c.name AS winnerName, 
            get_current_price(ai.itemID) AS current_price
        FROM 
            auction_item ai
        LEFT JOIN 
            customer c ON ai.winnerID = c.userID
        WHERE 
            ai.itemID = %s;
        """
        cursor.execute(query, (itemID,))
        item = cursor.fetchone()
        
        if item:
            return jsonify(item), 200
        else:
            return jsonify({"error": "Item not found"}), 404

    except mysql.connector.Error as e:
        print(f"Error: {e}")
        return jsonify({"error": "Database error", "details": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/customers/<string:custID>/bids', methods=['GET'])
def get_bids_by_customer(custID):
    conn = None
    cursor = None
    try:
        conn = get_user_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
        SELECT b.bidID, b.itemID, ai.title, b.amount, b.bid_time
        FROM bid b JOIN auction_item ai ON b.itemID = ai.itemID
        WHERE b.custID = %s ORDER BY b.bid_time DESC;
        """
        cursor.execute(query, (custID,))
        return jsonify(cursor.fetchall()), 200
    except mysql.connector.Error as e:
        return jsonify({"error": "Database error", "details": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/auctions/<string:auctionID>/items', methods=['GET'])
def get_items_by_auction(auctionID):
    conn = None
    cursor = None
    try:
        conn = get_user_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT itemID, title, status, get_current_price(itemID) AS current_price FROM auction_item WHERE auctionID = %s;"
        cursor.execute(query, (auctionID,))
        return jsonify(cursor.fetchall()), 200
    except mysql.connector.Error as e:
        return jsonify({"error": "Database error", "details": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/customers/<string:custID>', methods=['PUT'])
def update_customer(custID):
    data = request.get_json()
    if not data or ('phone' not in data and 'address' not in data):
        return jsonify({"error": "No data to update"}), 400

    conn = None
    cursor = None
    try:
        conn = get_user_connection()
        cursor = conn.cursor()
        if 'phone' in data:
            cursor.execute("UPDATE customer SET phone = %s WHERE userID = %s", (data['phone'], custID))
        if 'address' in data:
            cursor.execute("UPDATE customer SET address = %s WHERE userID = %s", (data['address'], custID))
        conn.commit()
        return jsonify({"message": "Customer updated"}), 200
    except mysql.connector.Error as e:
        return jsonify({"error": "Database error", "details": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/customers/<string:custID>/winnings', methods=['GET'])
def get_unpaid_winnings(custID):
    """
    Fetches all items a user has won but not yet paid for.
    This is what a "cart" or "checkout" page would use.
    """
    conn = None
    cursor = None
    try:
        conn = get_user_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
        SELECT 
            itemID, 
            title, 
            get_current_price(itemID) AS winning_amount
        FROM 
            auction_item
        WHERE 
            itemID IN (
                SELECT ai2.itemID
                FROM auction_item ai2
                WHERE ai2.winnerID = %s
                  AND ai2.transactionID IS NULL
            );
        """
        cursor.execute(query, (custID,))
        items = cursor.fetchall()
        return jsonify(items), 200

    except mysql.connector.Error as e:
        print(f"Error: {e}")
        return jsonify({"error": "Database error", "details": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/payments', methods=['POST'])
def create_payment():
    """
    Creates a payment.
    - User only sends CustomerId, itemID, and paymentMethod.
    - The server auto-detects the winning amount.
    - The server VERIFIES the customer is the actual winner.
    """
    data = request.get_json()
    required_fields = ['paymentMethod', 'CustomerId', 'itemID']
    if not data or not all(field in data for field in required_fields):
        return jsonify({"error": f"Missing data. Required: {', '.join(required_fields)}"}), 400

    conn = None
    cursor = None
    
    new_transactionID = f"T-{uuid.uuid4().hex[:8]}" 
    payment_date = datetime.now().strftime('%Y-%m-%d')
    
    p_custID = data['CustomerId']
    p_itemID = data['itemID']
    p_method = data['paymentMethod']
    
    try:
        conn = get_user_connection()
        cursor = conn.cursor(dictionary=True)
        conn.start_transaction()

        cursor.execute(
            "SELECT winnerID, status, get_current_price(itemID) AS amount FROM auction_item WHERE itemID = %s",
            (p_itemID,)
        )
        item_info = cursor.fetchone()

        if not item_info:
            return jsonify({"error": "Item not found"}), 404

        if item_info['status'] != 'Sold':
            return jsonify({"error": "Payment rejected. This item is not marked as 'Sold'."}), 400

        if item_info['winnerID'] != p_custID:
            return jsonify({"error": "Payment rejected. You are not the winner of this item."}), 403 # 403 Forbidden
            
        v_amount = item_info['amount']

        query_insert_payment = """
        INSERT INTO payment (transactionID, amount, paymentMethod, PaymentDate, CustomerId, itemID)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query_insert_payment, (
            new_transactionID, v_amount, p_method, 
            payment_date, p_custID, p_itemID
        ))

        query_update_item = """
        UPDATE auction_item 
        SET transactionID = %s 
        WHERE itemID = %s
        """
        cursor.execute(query_update_item, (new_transactionID, p_itemID))
        
        conn.commit()
        
        return jsonify({
            "message": f"Payment of ${v_amount} successful!",
            "transactionID": new_transactionID
        }), 201

    except mysql.connector.Error as e:
        if conn: conn.rollback()
        if e.sqlstate == '45000': 
            return jsonify({"error": "Payment rejected by database trigger", "details": e.msg}), 400
        else:
            print(f"Database Error: {e}")
            return jsonify({"error": "Database error", "details": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# ADMIN-ONLY ENDPOINTS

@app.route('/auctions', methods=['POST'])
def create_auction():
    data = request.get_json()
    required = ['auctionID', 'auction_name', 'start_time', 'end_time', 'userID']
    if not data or not all(field in data for field in required):
        return jsonify({"error": "Missing data"}), 400

    conn = None
    cursor = None
    try:
        conn = get_admin_connection()
        cursor = conn.cursor()
        query = "INSERT INTO auction (auctionID, auction_name, start_time, end_time, status, userID) VALUES (%s, %s, %s, %s, 'Scheduled', %s)"
        cursor.execute(query, (data['auctionID'], data['auction_name'], data['start_time'],
                               data['end_time'], data['userID']))
        conn.commit()
        return jsonify({"message": "Auction created"}), 201
    except mysql.connector.Error as e:
        return jsonify({"error": "Database error", "details": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/auctions', methods=['GET'])
def list_auctions():
    """
    Returns a list of all auctions with details.
    Fields: auctionID, auction_name, start_time, end_time, status, userID
    """
    conn = None
    cursor = None
    try:
        conn = get_user_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT auctionID, auction_name, start_time, end_time, status, userID FROM auction ORDER BY start_time;"
        cursor.execute(query)
        auctions = cursor.fetchall()
        for a in auctions:
            if isinstance(a['start_time'], datetime):
                a['start_time'] = a['start_time'].strftime("%a, %d %b %Y %H:%M:%S IST")
            if isinstance(a['end_time'], datetime):
                a['end_time'] = a['end_time'].strftime("%a, %d %b %Y %H:%M:%S IST")
        return jsonify(auctions), 200
    except mysql.connector.Error as e:
        return jsonify({"error": "Database error", "details": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/items', methods=['POST'])
def create_item():
    data = request.get_json()
    required = ['itemID', 'title', 'start_price', 'reserve_price', 'categoryID', 'auctionID']
    if not data or not all(field in data for field in required):
        return jsonify({"error": "Missing data"}), 400
    
    conn = None
    cursor = None
    try:
        conn = get_admin_connection()
        cursor = conn.cursor()
        query = "INSERT INTO auction_item (itemID, description, title, start_price, status, reserve_price, categoryID, auctionID) VALUES (%s, %s, %s, %s, 'Listed', %s, %s, %s)"
        cursor.execute(query, (data['itemID'], data.get('description'), data['title'], data['start_price'],
                               data['reserve_price'], data['categoryID'], data['auctionID']))
        conn.commit()
        return jsonify({"message": "Item created"}), 201
    except mysql.connector.Error as e:
        return jsonify({"error": "Database error", "details": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/customers/<string:custID>', methods=['DELETE'])
def delete_customer(custID):
    conn = None
    cursor = None
    try:
        conn = get_admin_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM customer WHERE userID = %s", (custID,))
        conn.commit()
        return (jsonify({"message": "Customer deleted"}), 200) if cursor.rowcount > 0 else (jsonify({"error": "Customer not found"}), 404)
    except mysql.connector.Error as e:
        if e.sqlstate == '45000':
            return jsonify({"error": "Deletion failed", "details": e.msg}), 400
        return jsonify({"error": "Database error", "details": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/auctions/start-scheduled', methods=['POST'])
def start_scheduled_auctions():
    conn = None
    cursor = None
    try:
        conn = get_admin_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.callproc('sp_start_auction')
        conn.commit()
        result = get_proc_result(cursor)
        return jsonify({"message": "Checked scheduled auctions", "result": result}), 200
    except mysql.connector.Error as e:
        if e.errno == 1370: 
             return jsonify({"error": "Permission denied", "details": e.msg}), 403
        return jsonify({"error": "Database error", "details": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/auctions/<string:auctionID>/cancel', methods=['PUT'])
def cancel_auction(auctionID):
    conn = None
    cursor = None
    try:
        conn = get_admin_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.callproc('sp_cancel_auction', (auctionID,))
        conn.commit()
        result = get_proc_result(cursor)
        return jsonify({"message": f"Canceled auction {auctionID}", "result": result}), 200
    except mysql.connector.Error as e:
        if e.errno == 1370: 
             return jsonify({"error": "Permission denied", "details": e.msg}), 403
        return jsonify({"error": "Database error", "details": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/items/<string:itemID>/finalize', methods=['POST'])
def finalize_item(itemID):
    conn = None
    cursor = None
    try:
        conn = get_admin_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.callproc('sp_finalize_auction_item', (itemID,))
        conn.commit()
        result = get_proc_result(cursor)
        return jsonify({"message": f"Finalized item {itemID}", "result": result}), 200
    except mysql.connector.Error as e:
        if e.errno == 1370: 
             return jsonify({"error": "Permission denied", "details": e.msg}), 403
        return jsonify({"error": "Database error", "details": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/stats/user_counts', methods=['GET'])
def user_counts():
    """
    Returns counts grouped by role:
      - 'customers' => total rows in customer
      - 'admins'    => distinct users referenced as auctioneers in auction.userID
    Uses GROUP BY and COUNT in a derived table.
    """
    conn = None
    cursor = None
    try:
        conn = get_user_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
        SELECT role, COUNT(*) AS count FROM (
            SELECT userID, 'customers' AS role FROM customer
            UNION ALL
            SELECT DISTINCT userID, 'admins' AS role FROM auction
        ) t
        GROUP BY role;
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        return jsonify(rows), 200
    except mysql.connector.Error as e:
        return jsonify({"error": "Database error", "details": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

if __name__ == '__main__':
    app.run(debug=True, port=5000)