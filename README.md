# ComputerNetworks
**PYTHON CHAT APPLICATION - TWO-WAY GUI**

FILES
- server.py: Run on Laptop 1. Server has a full chat interface.
- client.py: Run on Laptop 2. Client has the same style of chat interface.

RUN ON LAPTOP 1
1. Open Command Prompt in this folder.
2. Run: python server.py
3. Click START SERVER and keep the window open.
4. Find Laptop 1's Wi-Fi IPv4 address using ipconfig.

RUN ON LAPTOP 2
1. Run: python client.py
2. Enter Laptop 1's Wi-Fi IPv4 address (not 127.0.0.1).
3. Enter your display name.

Both windows have a chat display, a message input, and a SEND button.
Both sides can send and receive messages independently. Press Enter or click SEND.

TROUBLESHOOTING
- Start the server before the client.
- Use the server laptop's Wi-Fi IPv4 address on Laptop 2.
- Allow Python through Windows Firewall on the Private network.
- Do not disable the firewall.
- Close old copies of server.py before starting this version.
- Both laptops must be on the same Wi-Fi network; router client/AP isolation
  can prevent laptop-to-laptop communication.

This is an educational LAN demo, without encryption or user authentication.
