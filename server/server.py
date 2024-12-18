import socket
import redis
from threading import Thread

HOST = '127.0.0.1'  
PORT = 8080         

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def initialize_products():
    if not redis_client.exists("categories"):
        categories = {
            "1": "T-Shirt",
            "2": "Pantolon",
            "3": "Ceket"
        }
        redis_client.hset("categories", mapping=categories)

        tshirts = {
            "T-Shirt 1": 15,
            "T-Shirt 2": 20,
            "T-Shirt 3": 25,
            "T-Shirt 4": 30
        }
        pantolons = {
            "Pantolon 1": 40,
            "Pantolon 2": 50,
            "Pantolon 3": 60,
            "Pantolon 4": 70
        }
        cekets = {
            "Ceket 1": 80,
            "Ceket 2": 100,
            "Ceket 3": 120,
            "Ceket 4": 150
        }
        redis_client.hset("products:T-Shirt", mapping=tshirts)
        redis_client.hset("products:Pantolon", mapping=pantolons)
        redis_client.hset("products:Ceket", mapping=cekets)

def handle_client(conn, addr):
    print(f"Client connected: {addr}")
    
    try:
        conn.sendall(b"Welcome to the Shopping Cart Server!\n")
        
        session_id = f"session:{conn.fileno()}"
        
        redis_client.hset(session_id, mapping={
            "balance": 200,
            "purchased_items": "" 
        })
        
        redis_client.delete(f"{session_id}:cart")  
        
        conn.sendall(f"Your starting money is ${redis_client.hget(session_id, 'balance').decode()}\n".encode('utf-8'))

        while True:
            try:
                conn.sendall(b"\n1. List Products\n2. View Cart\n3. Checkout\n4. Exit\nChoose an option: ")
                request = conn.recv(1024).decode('utf-8').strip()

                if request == "1":  
                    categories = redis_client.hgetall("categories")
                    while True:
                        categories_list = "\nCategories:\n"
                        for idx, value in enumerate(categories.values(), start=1):
                            categories_list += f"{idx}. {value.decode()}\n"
                        categories_list += "0. Back to Main Menu\n"
                        conn.sendall(categories_list.encode('utf-8'))

                        category_choice = conn.recv(1024).decode('utf-8').strip()
                        
                        if category_choice == "0":
                            break
                        
                        if category_choice.isdigit() and 1 <= int(category_choice) <= len(categories):
                            category_name = list(categories.values())[int(category_choice) - 1].decode()
                            products = redis_client.hgetall(f"products:{category_name}")

                            while True:
                                products_list = f"\n{category_name} Products:\n"
                                for idx, (product, price) in enumerate(products.items(), start=1):
                                    products_list += f"{idx}. {product.decode()} - ${price.decode()}\n"
                                products_list += "0. Back to Categories\n"
                                conn.sendall(products_list.encode('utf-8'))

                                product_choice = conn.recv(1024).decode('utf-8').strip()
                                
                                if product_choice == "0":
                                    break

                                if product_choice.isdigit() and 1 <= int(product_choice) <= len(products):
                                    product_name = list(products.keys())[int(product_choice) - 1].decode()
                                    product_price = float(list(products.values())[int(product_choice) - 1].decode())

                                    cart_item = f"{product_name}:${product_price}"
                                    redis_client.rpush(f"{session_id}:cart", cart_item)
                                    
                                    conn.sendall(f"{product_name} added to cart.\n".encode('utf-8'))
                                else:
                                    conn.sendall(b"Invalid product choice.\n")
                        else:
                            conn.sendall(b"Invalid category choice.\n")

                elif request == "2":  
                    cart_items = redis_client.lrange(f"{session_id}:cart", 0, -1)
                    
                    if cart_items:
                        response = "Your cart:\n"
                        total_cost = 0
                        for item in cart_items:
                            item_decoded = item.decode()
                            response += f"{item_decoded}\n"
                            total_cost += float(item_decoded.split('$')[1])
                        response += f"Total cost: ${total_cost}\n"
                        conn.sendall(response.encode('utf-8'))
                    else:
                        conn.sendall(b"Your cart is empty.\n")

                elif request == "3":  
                    balance = float(redis_client.hget(session_id, "balance").decode())
                    cart_items = redis_client.lrange(f"{session_id}:cart", 0, -1)
                    
                    if cart_items:
                        cart_total = sum(float(item.decode().split('$')[1]) for item in cart_items)
                        
                        if cart_total <= balance:
                            new_balance = balance - cart_total
                            redis_client.hset(session_id, "balance", new_balance)
                            
                            purchased_items = redis_client.hget(session_id, "purchased_items").decode()
                            for item in cart_items:
                                item_decoded = item.decode()
                                purchased_items += f"{item_decoded}; "
                            
                            redis_client.hset(session_id, "purchased_items", purchased_items)
                            redis_client.delete(f"{session_id}:cart")
                            
                            conn.sendall(f"Purchase successful! Remaining balance: ${new_balance}\n".encode('utf-8'))
                        else:
                            conn.sendall(f"Insufficient balance. Your current balance is ${balance}\n".encode('utf-8'))
                    else:
                        conn.sendall(b"Your cart is empty.\n")

                elif request == "4":  
                    try:
                        conn.sendall(b"Goodbye!\n")
                        print(f"Client disconnected: {addr}")
                    except:
                        pass
                    break

                else:
                    conn.sendall(b"Invalid option. Try again.\n")
            
            except (ConnectionResetError, ConnectionAbortedError):
                print(f"Client disconnected: {addr}")
                break
            except Exception as e:
                print(f"Error: {e}")
                try:
                    conn.sendall(b"An error occurred. Please try again.\n")
                except:
                    pass

    except Exception as e:
        print(f"Initial connection error: {e}")
    
    finally:
        try:
            conn.close()
        except:
            pass

def start_server():
    initialize_products()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT))
        server_socket.listen(5)
        print(f"Server is listening on {HOST}:{PORT}")

        while True:
            conn, addr = server_socket.accept()
            Thread(target=handle_client, args=(conn, addr)).start()

if __name__ == "__main__":
    start_server()