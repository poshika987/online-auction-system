# app.py

from flask import Flask, jsonify, request
from flask_cors import CORS
import mysql.connector
from db_connector import get_connection # Import our connection function

app = Flask(__name__)
CORS(app)

#API Endpoints

@app.route('/')
def home():
    return "Auction Backend Server is running!"

@app.route('/items', methods=['GET'])
def get_all_items():
    """
    Fetches all 'Listed' items and their current price.
    This shows how to use your SQL function 'get_current_price'.
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        if conn is None:
            return jsonify({"error": "Could not connect to database"}), 500
        
        cursor = conn.cursor(dictionary=True)
        
        query = """
        SELECT 
            itemID, 
            title, 
            description, 
            start_price, 
            reserve_price, 
            categoryID, 
            auctionID,
            get_current_price(itemID) AS current_price
        FROM 
            auction_item
        WHERE 
            status = 'Listed';
        """
        cursor.execute(query)
        items = cursor.fetchall()
        
        return jsonify(items), 200

    except mysql.connector.Error as e:
        print(f"Error: {e}")
        return jsonify({"error": "Database error", "details": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/bid', methods=['POST'])
def place_bid():

    data = request.get_json()
    
    if not data or 'custID' not in data or 'itemID' not in data or 'amount' not in data:
        return jsonify({"error": "Missing data. Required: custID, itemID, amount"}), 400
        
    p_custID = data['custID']
    p_itemID = data['itemID']
    p_amount = data['amount']

    conn = None
    cursor = None
    try:
        conn = get_connection()
        if conn is None:
            return jsonify({"error": "Could not connect to database"}), 500
            
        cursor = conn.cursor(dictionary=True)

        cursor.callproc('sp_place_bid', (p_custID, p_itemID, p_amount))
        
        conn.commit()
        
        result = None
        for res in cursor.stored_results():
            result = res.fetchone()
            
        return jsonify({"message": "Bid placed successfully!", "result": result}), 201

    except mysql.connector.Error as e:
        if e.sqlstate == '45000':
            return jsonify({"error": "Bid rejected", "details": e.msg}), 400
        else:
            print(f"Database Error: {e}")
            return jsonify({"error": "Database error", "details": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/customers', methods=['GET'])
def get_customers():
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT userID, name, email, phone FROM customer;")
        customers = cursor.fetchall()
        return jsonify(customers), 200
    except mysql.connector.Error as e:
        print(f"Error: {e}")
        return jsonify({"error": "Database error", "details": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


if __name__ == '__main__':
    # Runs the server on http://127.0.0.1:5000
    app.run(debug=True, port=5000)