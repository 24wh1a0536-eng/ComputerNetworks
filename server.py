import json
import socket
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext

HOST = "0.0.0.0"
PORT = 5000


class ChatServer:
    def __init__(self, root):
        self.root = root
        self.root.title("Python Chat Application - Server")
        self.root.geometry("760x600")
        self.server_socket = None
        self.running = False
        self.clients = {}  # socket: {"name": name, "lock": send_lock}
        self.clients_lock = threading.Lock()

        tk.Label(root, text="PYTHON CHAT APPLICATION", font=("Arial", 20, "bold")).pack(pady=(12, 4))
        tk.Label(root, text="SERVER", font=("Arial", 12, "bold")).pack()

        top = tk.Frame(root)
        top.pack(fill="x", padx=15, pady=8)
        self.status = tk.Label(top, text="Status: STOPPED", fg="red", font=("Arial", 11, "bold"))
        self.status.pack(side="left")
        self.count = tk.Label(top, text="Connected clients: 0")
        self.count.pack(side="right")

        controls = tk.Frame(root)
        controls.pack(pady=4)
        self.start_button = tk.Button(controls, text="START SERVER", width=16, command=self.start_server)
        self.start_button.pack(side="left", padx=5)
        self.stop_button = tk.Button(controls, text="STOP SERVER", width=16, command=self.stop_server, state="disabled")
        self.stop_button.pack(side="left", padx=5)

        tk.Label(root, text="CHAT", font=("Arial", 11, "bold")).pack(anchor="w", padx=15, pady=(8, 0))
        self.chat = scrolledtext.ScrolledText(root, state="disabled", wrap="word", font=("Arial", 12))
        self.chat.pack(fill="both", expand=True, padx=15, pady=8)

        bottom = tk.Frame(root)
        bottom.pack(fill="x", padx=15, pady=(0, 15))
        self.entry = tk.Entry(bottom, font=("Arial", 13))
        self.entry.pack(side="left", fill="x", expand=True, ipady=8)
        self.entry.bind("<Return>", lambda event: self.send_server_message())
        self.send_button = tk.Button(bottom, text="SEND", width=12, command=self.send_server_message, state="disabled")
        self.send_button.pack(side="left", padx=(8, 0))

        self.root.protocol("WM_DELETE_WINDOW", self.close_window)
        self.add_chat("[System] Click START SERVER to begin.")

    def add_chat_ui(self, message):
        self.chat.config(state="normal")
        self.chat.insert("end", message + "\n")
        self.chat.see("end")
        self.chat.config(state="disabled")

    def add_chat(self, message):
        try:
            self.root.after(0, self.add_chat_ui, message)
        except tk.TclError:
            pass

    def update_count(self):
        with self.clients_lock:
            n = len(self.clients)
        try:
            self.root.after(0, lambda: self.count.config(text=f"Connected clients: {n}"))
        except tk.TclError:
            pass

    def start_server(self):
        if self.running:
            return
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            server.bind((HOST, PORT))
            server.listen(10)
            server.settimeout(1)
        except OSError as exc:
            server.close()
            messagebox.showerror("Server Error", f"Could not start on port {PORT}:\n{exc}\n\nClose any older server window and try again.")
            return

        self.server_socket = server
        self.running = True
        self.status.config(text="Status: RUNNING", fg="green")
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.send_button.config(state="normal")
        self.add_chat(f"[System] Server listening on port {PORT}.")
        threading.Thread(target=self.accept_clients, daemon=True).start()

    def accept_clients(self):
        while self.running:
            try:
                client, address = self.server_socket.accept()
                threading.Thread(target=self.handle_client, args=(client, address), daemon=True).start()
            except socket.timeout:
                continue
            except OSError:
                break

    def send_packet(self, client, packet):
        data = (json.dumps(packet, ensure_ascii=False) + "\n").encode("utf-8")
        with self.clients_lock:
            info = self.clients.get(client)
        if info is None:
            raise OSError("Client is no longer connected")
        with info["lock"]:
            client.sendall(data)

    def handle_client(self, client, address):
        name = None
        buffer = ""
        try:
            while self.running:
                chunk = client.recv(4096)
                if not chunk:
                    break
                buffer += chunk.decode("utf-8")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if not line.strip():
                        continue
                    try:
                        packet = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    if packet.get("type") == "join" and name is None:
                        name = str(packet.get("username", "Guest")).strip()[:25] or "Guest"
                        with self.clients_lock:
                            self.clients[client] = {"name": name, "lock": threading.Lock()}
                        self.add_chat(f"[System] {name} connected from {address[0]}.")
                        self.update_count()
                        self.broadcast({"type": "system", "text": f"{name} joined the chat."}, exclude=client)

                    elif packet.get("type") == "chat" and name is not None:
                        message = str(packet.get("text", "")).strip()
                        if message:
                            self.add_chat(f"{name}: {message}")
                            self.broadcast({"type": "chat", "username": name, "text": message}, exclude=client)
        except (OSError, UnicodeDecodeError):
            pass
        finally:
            self.remove_client(client, name)

    def broadcast(self, packet, exclude=None):
        with self.clients_lock:
            recipients = [sock for sock in self.clients if sock is not exclude]
        for sock in recipients:
            try:
                self.send_packet(sock, packet)
            except OSError:
                self.remove_client(sock)

    def send_server_message(self):
        message = self.entry.get().strip()
        if not message:
            return
        if not self.running:
            self.add_chat("[System] Start the server before sending.")
            return
        self.entry.delete(0, "end")
        self.add_chat(f"Server: {message}")
        self.broadcast({"type": "chat", "username": "Server", "text": message})

    def remove_client(self, client, fallback_name=None):
        with self.clients_lock:
            info = self.clients.pop(client, None)
        try:
            client.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            client.close()
        except OSError:
            pass
        if info:
            name = info["name"]
            self.add_chat(f"[System] {name} disconnected.")
            self.update_count()
            if self.running:
                self.broadcast({"type": "system", "text": f"{name} disconnected."})

    def stop_server(self):
        if not self.running:
            return
        self.running = False
        try:
            self.server_socket.close()
        except OSError:
            pass
        with self.clients_lock:
            sockets = list(self.clients.keys())
            self.clients.clear()
        for sock in sockets:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                sock.close()
            except OSError:
                pass
        self.status.config(text="Status: STOPPED", fg="red")
        self.count.config(text="Connected clients: 0")
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.send_button.config(state="disabled")
        self.add_chat("[System] Server stopped; clients disconnected.")

    def close_window(self):
        self.stop_server()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = ChatServer(root)
    root.mainloop()
