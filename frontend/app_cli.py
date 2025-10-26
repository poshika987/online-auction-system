import requests
import json
import uuid

# The base URL of your running Flask application
BASE_URL = "http://127.0.0.1:5000"
g_logged_in_user = None

# --- Helper Functions ---

def print_response(response):
    """Helper function to pretty-print a requests response."""
    print(f"\n--- Response ---")
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Body:\n{json.dumps(response.json(), indent=2)}")
    except requests.exceptions.JSONDecodeError:
        print(f"Body: {response.text}")
    print("----------------\n")

def get_int_input(prompt):
    """Helper to safely get an integer from the user."""
    while True:
        num_str = input(prompt)
        try:
            return int(num_str)
        except ValueError:
            print("[Error] Invalid input. Please enter a number.")

def show_help():
    """Prints the available commands from a user's point of view."""
    global g_logged_in_user
    print("\n--- Online Auction System ---")
    if not g_logged_in_user:
        print("\n--- Get Started ---")
        print("  0: Login")
        print("  1: Register as a new customer")
    else:
        print(f"\n--- Logged in as: {g_logged_in_user['name']} ({g_logged_in_user['userID']}) ---")
        print("  logout: Logout")
        print("\n--- Customer Tasks ---")
        print("  2: Update my profile")

        print("\n--- Bidding Tasks ---")
        print("  3: Browse all items for sale")
        print("  4: View details for a single item")
        print("  5: Place a bid on an item")
        print("  6: View my unpaid winnings") 
        print("  7: Pay for a won item")     

        print("\n--- Admin / Auctioneer Tasks ---")
        print("  8: Create a new auction")   
        print("  9: Create a new item")  
        print("  10: Start all scheduled auctions") 
        print("  11: Finalize bidding for an item") 
        print("  12: Cancel an auction")           
        print("  13: Delete a customer")
        print("  14: List all Auctions") 

        print("\n--- Reporting Tasks ---")
        print("  15: List all registered customers")
        print("  16: See all bids from one customer") 
        print("  17: See all items in one auction")  
        print("  18: Count admins & customers") 
        
        print("\n  help: Show this menu")
        print("  quit: Exit the application")
        print("--------------------------------\n")

# --- API Call Functions (User-Centric) ---
def login():
    global g_logged_in_user
    print("--- 0: Login ---")
    
    user_id = input("  Enter your CustomerID: ")
    password = input("  Enter your password: ")
    
    try:
        response = requests.post(f"{BASE_URL}/login", json={"userID": user_id, "password": password})
        print_response(response)
        
        if response.status_code == 200:
            g_logged_in_user = response.json().get("customer")
            print(f"--- Welcome, {g_logged_in_user['name']}! ---")
        else:
            print("Login failed. Please check your credentials.")
            
    except requests.exceptions.ConnectionError:
        print("\n[Error] Could not connect to server.")

def logout():
    global g_logged_in_user
    print(f"--- Logging out {g_logged_in_user['name']}... ---")
    g_logged_in_user = None
    print("Logout successful.")

def register_customer():
    print("--- 1: Register as a new customer ---")
    print("Enter your details (press Enter for default):")
    
    user_id = input("  userID (e.g., C999): ") or f"C{uuid.uuid4().hex[:3]}"
    name = input("  name (e.g., John Doe): ") or "John Doe"
    phone = input("  phone (e.g., 9123456780): ") or "9123456780"
    email = input("  email (e.g., jd@gmail.com): ") or "jd@gmail.com"
    address = input("  address (e.g., 123 Main St): ") or "123 Main St"
    password = input("  password (e.g., pass999): ") or "pass999"

    payload = {
        "userID": user_id, "name": name, "phone": phone,
        "email": email, "address": address, "password": password
    }
    
    print(f"\nSending registration...\n{json.dumps(payload, indent=2)}")
    try:
        response = requests.post(f"{BASE_URL}/customers", json=payload)
        print_response(response)
    except requests.exceptions.ConnectionError:
        print("\n[Error] Could not connect to server. Is app.py running?")

def update_profile():
    print("--- 2: Update my profile ---")
    cust_id = input("  Enter CustomerID to update (e.g., C005): ")
    if not cust_id:
        print("[Error] CustomerID is required.")
        return
        
    new_phone = input("  Enter new phone (or press Enter to skip): ")
    new_address = input("  Enter new address (or press Enter to skip): ")
    
    payload = {}
    if new_phone: payload["phone"] = new_phone
    if new_address: payload["address"] = new_address
        
    if not payload:
        print("No new data provided. Aborting.")
        return

    print(f"\nUpdating profile...\n{json.dumps(payload, indent=2)}")
    try:
        response = requests.put(f"{BASE_URL}/customers/{cust_id}", json=payload)
        print_response(response)
    except requests.exceptions.ConnectionError:
        print("\n[Error] Could not connect to server.")

def browse_items():
    print("--- 3: Browsing all items for sale ---")
    try:
        response = requests.get(f"{BASE_URL}/items")
        print_response(response)
    except requests.exceptions.ConnectionError:
        print("\n[Error] Could not connect to server. Is app.py running?")

def view_item_details():
    print("--- 4: View details for a single item ---")
    item_id = input("  Enter itemID (e.g., I001): ")
    if not item_id:
        print("[Error] itemID cannot be empty.")
        return
        
    try:
        response = requests.get(f"{BASE_URL}/items/{item_id}")
        print_response(response)
    except requests.exceptions.ConnectionError:
        print("\n[Error] Could not connect to server.")

def view_unpaid_winnings():
    print("--- 6: View my unpaid winnings ---")
    cust_id = input("  Enter your CustomerID: ")
    if not cust_id:
        print("[Error] CustomerID is required.")
        return
        
    try:
        response = requests.get(f"{BASE_URL}/customers/{cust_id}/winnings")
        print_response(response)
        items = response.json()
        if response.status_code == 200 and not items:
            print("You have no unpaid items. Good job!")
            
    except requests.exceptions.ConnectionError:
        print("\n[Error] Could not connect to server.")
    except Exception as e:
        print(f"An error occurred: {e}")

def place_bid():
    global g_logged_in_user
    if not g_logged_in_user:
        print("[Error] You must be logged in to place a bid.")
        return

    print("--- 5: Place a bid on an item ---")
    cust_id = g_logged_in_user['userID'] 
    item_id = input("  Enter the ItemID (e.g., I001): ")

    if not all([cust_id, item_id]):
        print("[Error] CustomerID and ItemID are required.")
        return
    
    amount_int = get_int_input("  Enter bid amount (e.g., 44000): ")
        
    payload = {
        "custID": cust_id,
        "itemID": item_id,
        "amount": amount_int
    }
    
    print(f"\nPlacing bid...\n{json.dumps(payload, indent=2)}")
    try:
        response = requests.post(f"{BASE_URL}/bid", json=payload)
        print_response(response)
    except requests.exceptions.ConnectionError:
        print("\n[Error] Could not connect to server.")

def pay_for_item():
    print("--- 7: Pay for a won item ---")
    print("NOTE: This will only work if the item is 'Sold'.")
    
    cust_id = input("  Enter your CustomerID: ")
    item_id = input("  Enter the ItemID you want to pay for: ")
    if not all([cust_id, item_id]):
        print("[Error] CustomerID and ItemID are required.")
        return
        
    method = input("  Enter payment method (UPI, Credit/Debit Card, Net Banking): ")

    payload = {
        "paymentMethod": method,
        "CustomerId": cust_id,
        "itemID": item_id
    }
    
    print(f"\nSubmitting payment (amount will be calculated by server)...")
    try:
        response = requests.post(f"{BASE_URL}/payments", json=payload)
        print_response(response)
        if response.status_code == 201:
             print("\nSUCCESS! Check your database. The auction status might now be 'Completed'.")
    except requests.exceptions.ConnectionError:
        print("\n[Error] Could not connect to server.")

# --- Admin Functions ---

def create_auction():
    print("--- 7: Create a new auction ---")
    print("NOTE: 'userID' is the CustomerID of the auctioneer (admin).")
    auction_id = input("  AuctionID (e.g., A100): ")
    name = input("  Auction Name (e.g., Vintage Watch Sale): ")
    start = input("  Start Time (YYYY-MM-DD HH:MM:SS): ")
    end = input("  End Time (YYYY-MM-DD HH:MM:SS): ")
    user_id = input("  Auctioneer's UserID (e.g., C001): ")
    
    if not all([auction_id, name, start, end, user_id]):
        print("[Error] All fields are required.")
        return
        
    payload = {
        "auctionID": auction_id, "auction_name": name,
        "start_time": start, "end_time": end, "userID": user_id
    }
    print(f"\nCreating auction...\n{json.dumps(payload, indent=2)}")
    try:
        response = requests.post(f"{BASE_URL}/auctions", json=payload)
        print_response(response)
    except requests.exceptions.ConnectionError:
        print("\n[Error] Could not connect to server.")

def create_item():
    print("--- 8: Create a new item for auction ---")
    item_id = input("  ItemID (e.g., I100): ")
    title = input("  Title (e.g., Rolex Watch): ")
    desc = input("  Description (optional): ")
    start_price = get_int_input("  Start Price (e.g., 5000): ")
    reserve_price = get_int_input("  Reserve Price (e.g., 7500): ")
    cat_id = input("  CategoryID (e.g., CAT01): ")
    auction_id = input("  AuctionID (e.g., A100): ")

    if not all([item_id, title, cat_id, auction_id]):
        print("[Error] ItemID, Title, CategoryID, and AuctionID are required.")
        return
        
    payload = {
        "itemID": item_id, "title": title, "description": desc,
        "start_price": start_price, "reserve_price": reserve_price,
        "categoryID": cat_id, "auctionID": auction_id
    }
    print(f"\nCreating item...\n{json.dumps(payload, indent=2)}")
    try:
        response = requests.post(f"{BASE_URL}/items", json=payload)
        print_response(response)
    except requests.exceptions.ConnectionError:
        print("\n[Error] Could not connect to server.")

def start_auctions():
    print("--- 9: Start all scheduled auctions ---")
    print("This will call 'sp_start_auction' to find and activate any due auctions.")
    input("Press Enter to continue...")
    try:
        response = requests.post(f"{BASE_URL}/auctions/start-scheduled")
        print_response(response)
    except requests.exceptions.ConnectionError:
        print("\n[Error] Could not connect to server.")

def finalize_item():
    print("--- 10: Finalize bidding for an item ---")
    print("NOTE: The auction must be 'Ended' for this to work.")
    
    item_id = input("  Enter itemID to finalize (e.g., I100): ")
    if not item_id:
        print("[Error] itemID cannot be empty.")
        return
    
    print(f"Finalizing {item_id}...")
    try:
        response = requests.post(f"{BASE_URL}/items/{item_id}/finalize")
        print_response(response)
        print("\nIf successful, the item's status is now 'Sold'.")
    except requests.exceptions.ConnectionError:
        print("\n[Error] Could not connect to server.")

def cancel_auction():
    print("--- 11: Cancel an auction ---")
    auction_id = input("  Enter auctionID to cancel (e.g., A003): ")
    if not auction_id:
        print("[Error] auctionID cannot be empty.")
        return
        
    print(f"Cancelling {auction_id}...")
    try:
        response = requests.put(f"{BASE_URL}/auctions/{auction_id}/cancel")
        print_response(response)
    except requests.exceptions.ConnectionError:
        print("\n[Error] Could not connect to server.")

def delete_customer():
    print("--- 12: (DANGEROUS) Delete a customer ---")
    cust_id = input("  Enter CustomerID to delete (e.g., C001): ")
    if not cust_id:
        print("[Error] CustomerID is required.")
        return
        
    print(f"\nWARNING: Attempting to delete '{cust_id}'.")
    print("This will be BLOCKED by the database trigger if they have active bids or payments.")
    input("Press Enter to confirm...")
    
    try:
        response = requests.delete(f"{BASE_URL}/customers/{cust_id}")
        print_response(response)
    except requests.exceptions.ConnectionError:
        print("\n[Error] Could not connect to server.")

# --- Reporting Functions ---

def list_all_customers():
    print("--- 13: List all registered customers ---")
    try:
        response = requests.get(f"{BASE_URL}/customers")
        print_response(response)
    except requests.exceptions.ConnectionError:
        print("\n[Error] Could not connect to server.")

def list_all_auctions():
    print("--- 17: See all auctions (list details) ---")
    try:
        response = requests.get(f"{BASE_URL}/auctions")
        print_response(response)
        if response.status_code == 200:
            try:
                auctions = response.json()
                if isinstance(auctions, list) and auctions:
                    print("\n--- Auction Details ---")
                    for a in auctions:
                        print(f"AuctionID: {a.get('auctionID')} | Name: {a.get('auction_name')} | "
                              f"Start: {a.get('start_time')} | End: {a.get('end_time')} | "
                              f"Status: {a.get('status')} | Auctioneer: {a.get('userID')}")
                    print("------------------------\n")
            except Exception:
                pass
    except requests.exceptions.ConnectionError:
        print("\n[Error] Could not connect to server.")

def list_bids_by_customer():
    print("--- 14: See all bids from one customer ---")
    cust_id = input("  Enter CustomerID (e.g., C001): ")
    if not cust_id:
        print("[Error] CustomerID is required.")
        return
        
    try:
        response = requests.get(f"{BASE_URL}/customers/{cust_id}/bids")
        print_response(response)
    except requests.exceptions.ConnectionError:
        print("\n[Error] Could not connect to server.")

def list_items_in_auction():
    print("--- 15: See all items in one auction ---")
    auction_id = input("  Enter AuctionID (e.g., A001): ")
    if not auction_id:
        print("[Error] AuctionID is required.")
        return
        
    try:
        response = requests.get(f"{BASE_URL}/auctions/{auction_id}/items")
        print_response(response)
    except requests.exceptions.ConnectionError:
        print("\n[Error] Could not connect to server.")


def list_user_counts():
    print("--- 18: Count admins & customers ---")
    try:
        response = requests.get(f"{BASE_URL}/stats/user_counts")
        print_response(response)
        if response.status_code == 200:
            counts = response.json()
            print("\n--- Counts ---")
            for row in counts:
                print(f"  {row.get('role')}: {row.get('count')}")
            print("--------------\n")
    except requests.exceptions.ConnectionError:
        print("\n[Error] Could not connect to server.")

# --- Main Loop ---

def main():    
    command_map = {
        '0': login,    
        'logout': logout,
        '1': register_customer,
        '2': update_profile,
        '3': browse_items,
        '4': view_item_details,
        '5': place_bid,
        '6': view_unpaid_winnings,  
        '7': pay_for_item,
        '8': create_auction,
        '9': create_item,
        '10': start_auctions,
        '11': finalize_item,
        '12': cancel_auction,
        '13': delete_customer,
        '14': list_all_auctions,
        '15': list_all_customers,
        '16': list_bids_by_customer,
        '17': list_items_in_auction,
        '18': list_user_counts,
        'help': show_help
    }
    
    while True:
        show_help()
        command = input("Enter command (or 'help'/'quit'): ").strip().lower()
        
        if command == 'quit':
            print("Exiting.")
            break
        
        action = command_map.get(command)
        if action:
            action()
        else:
            print(f"Unknown command: '{command}'. Type 'help' for a list.")

if __name__ == "__main__":
    main()