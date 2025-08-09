# sunucu.py

import socket
import threading

HOST = '127.0.0.1'
PORT = 12345

# Artık sadece bağlantıyı değil, (bağlantı, kullanıcı_adı) ikilisini tutacağız
clients = {}
clients_lock = threading.Lock()

def broadcast_user_list():
    """Tüm istemcilere güncel kullanıcı listesini yollar."""
    with clients_lock:
        user_list = "USERLIST:" + ",".join(clients.values())
        for conn in clients:
            try:
                conn.sendall(user_list.encode('utf-8'))
            except:
                pass

def broadcast_message(message, sender_conn):
    """Ses mesajını, gönderen hariç herkese yollar."""
    with clients_lock:
        for conn in clients:
            if conn != sender_conn:
                try:
                    conn.sendall(message)
                except:
                    pass

def handle_client(conn, addr):
    print(f"➡️ {addr} bağlandı, kullanıcı adı bekleniyor...")
    nickname = ""
    try:
        # İlk gelen mesajın kullanıcı adı olmasını bekliyoruz
        # Bu basit bir protokol, normalde daha sağlam yapılar kullanılır
        initial_data = conn.recv(1024).decode('utf-8')
        if initial_data.startswith("NICK:"):
            nickname = initial_data.split(":", 1)[1]
            with clients_lock:
                clients[conn] = nickname
            print(f"✅ {nickname} ({addr}) odaya katıldı.")
            broadcast_user_list() # Herkese yeni listeyi gönder
        else:
            print(f"❌ Protokol hatası. {addr} bağlantısı kesiliyor.")
            conn.close()
            return

        while True:
            data = conn.recv(1024)
            if not data:
                break
            broadcast_message(data, conn)
            
    except (ConnectionResetError, ConnectionAbortedError):
        print(f"🔌 {nickname} ({addr}) bağlantısı aniden kesildi.")
    finally:
        with clients_lock:
            if conn in clients:
                del clients[conn]
        print(f"🔌 {nickname} ({addr}) odadan ayrıldı.")
        broadcast_user_list() # Herkese güncel listeyi tekrar gönder
        conn.close()

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    print(f"✅ Canlı Sohbet Sunucusu {HOST}:{PORT} adresinde dinlemede...")

    while True:
        conn, addr = server_socket.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()

if __name__ == "__main__":
    start_server()