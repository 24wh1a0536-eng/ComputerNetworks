import json
import socket
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext, simpledialog

PORT = 5000


class ChatClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Python Chat Application - Client")
        self.root.geometry("760x600")
        self.sock = None
        self.running = False
        self.send_lock = threading.Lock()
        self.username = "Guest"

        tk.Label(root, text="PYTHON CHAT APPLICATION", font=("Arial", 20, "bold")).pack(pady=(15, 4))
        tk.Label(root, text="CLIENT", font=("Arial", 12, "bold")).pack()

        top = tk.Frame(root)
        top.pack(fill="x", padx=15, pady=10)
        self.status = tk.Label(top, text="Status: NOT CONNECTED", fg="red", font=("Arial", 11, "bold"))
        self.status.pack(side="left")

        self.chat = scrolledtext.ScrolledText(root, state="disabled", wrap="word", font=("Arial", 12))
        self.chat.pack(fill="both", expand=True, padx=15, pady=8)

        bottom = tk.Frame(root)
        bottom.pack(fill="x", padx=15, pady=(0, 15))
        self.entry = tk.Entry(bottom, font=("Arial", 13))
        self.entry.pack(side="left", fill="x", expand=True, ipady=8)
        self.entry.bind("<Return>", lambda event: self.send_message())
        self.send_button = tk.Button(bottom, text="SEND", width=12, command=self.send_message, state="disabled")
        self.send_button.pack(side="left", padx=(8, 0))

        self.root.protocol("WM_DELETE_WINDOW", self.close_window)
        self.root.after(150, self.connect_to_server)

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

    def set_status(self, message, color):
        try:
            self.root.after(0, lambda: self.status.config(text=message, fg=color))
        except tk.TclError:
            pass

    def set_send_enabled(self, enabled):
        try:
            self.root.after(0, lambda: self.send_button.config(state="normal" if enabled else "disabled"))
        except tk.TclError:
            pass

    def connect_to_server(self):
        host = simpledialog.askstring(
            "Server IP",
            "Enter Laptop 1 Wi-Fi IPv4 address (use 127.0.0.1 only on the server laptop):",
            initialvalue="127.0.0.1",
            parent=self.root
        )
        if not host:
            self.add_chat("[System] Connection cancelled.")
            return

        name = simpledialog.askstring("Display Name", "Enter your name:", initialvalue="Client", parent=self.root)
        if name is None:
            self.add_chat("[System] Connection cancelled.")
            return
        self.username = name.strip()[:25] or "Guest"

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(8)
            sock.connect((host.strip(), PORT))
            sock.settimeout(None)
            self.sock = sock
            self.send_packet({"type": "join", "username": self.username})
            self.running = True
            self.set_status(f"Status: CONNECTED TO {host.strip()}", "green")
            self.set_send_enabled(True)
            self.add_chat(f"[System] Connected as {self.username}.")
            threading.Thread(target=self.receive_messages, daemon=True).start()
        except (OSError, ValueError) as exc:
            self.set_status("Status: NOT CONNECTED", "red")
            self.add_chat(f"[System] Connection failed: {exc}")
            messagebox.showerror(
                "Connection Failed",
                f"Could not connect to {host.strip()} on port {PORT}.\n\n{exc}\n\n"
                "Check that the server is running, the IP is correct, and Python is allowed through Windows Firewall on the Private network."
            )

    def send_packet(self, packet):
        data = (json.dumps(packet, ensure_ascii=False) + "\n").encode("utf-8")
        with self.send_lock:
            if self.sock is None:
                raise OSError("No server connection")
            self.sock.sendall(data)

    def receive_messages(self):
        buffer = ""
        try:
            while self.running:
                chunk = self.sock.recv(4096)
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
                    if packet.get("type") == "chat":
                        self.add_chat(f'{packet.get("username", "Server")}: {packet.get("text", "")}')
                    elif packet.get("type") == "system":
                        self.add_chat(f'[System] {packet.get("text", "")}')
        except (OSError, UnicodeDecodeError):
            pass
        finally:
            was_running = self.running
            self.running = False
            self.set_send_enabled(False)
            self.set_status("Status: DISCONNECTED", "red")
            if was_running:
                self.add_chat("[System] Server connection closed.")

    def send_message(self):
        message = self.entry.get().strip()
        if not message:
            return
        if not self.running:
            self.add_chat("[System] Not connected. Connect to the server first.")
            return
        try:
            self.send_packet({"type": "chat", "text": message})
            self.entry.delete(0, "end")
            self.add_chat(f"{self.username}: {message}")
        except OSError as exc:
            self.add_chat(f"[System] Send failed: {exc}")
            self.running = False
            self.set_send_enabled(False)
            self.set_status("Status: DISCONNECTED", "red")

    def close_window(self):
        self.running = False
        self.set_send_enabled(False)
        if self.sock:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                self.sock.close()
            except OSError:
                pass
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = ChatClient(root)
    root.mainloop()
