import socket, hashlib, base64, select
from utils.helpers import Helpers

MAGIC_STRING = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


def main():
    configs = Helpers.load_app_config()

    ws_proxy_port = int(configs["wsproxy_port"])
    dropbear_port = int(configs["dropbear_port"])

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", ws_proxy_port))
    server.listen(128)

    print(f"WebSocket Proxy listening on 127.0.0.1:{ws_proxy_port}")

    while True:
        client = None
        dropbear = None

        try:
            client, address = server.accept()
            print(f"Incoming connection: {address}")

            headers = client.recv(4096).decode(errors="ignore").split("\r\n")

            sec_websocket_key = extract_header_value(
                extract_header(headers, "Sec-WebSocket-Key")
            )

            if not sec_websocket_key:
                client.close()
                continue

            accept_key = generate_accept_key(sec_websocket_key)

            response = (
                "HTTP/1.1 101 Switching Protocols\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                f"Sec-WebSocket-Accept: {accept_key}\r\n"
                "\r\n"
            )

            client.sendall(response.encode())

            print("WebSocket connected")

            dropbear = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            dropbear.connect(("127.0.0.1", dropbear_port))

            while True:

                readable, _, _ = select.select(
                    [client, dropbear],
                    [],
                    []
                )

                for sock in readable:

                    if sock == client:

                        payload = receive_frame(client)

                        if payload is None:
                            raise ConnectionError("Client disconnected")

                        # Ignore Ping/Pong frames
                        if payload == b"":
                            continue

                        dropbear.sendall(payload)

                    elif sock == dropbear:

                        payload = dropbear.recv(4096)

                        if not payload:
                            raise ConnectionError("Dropbear disconnected")

                        send_frame(client, payload)

        except Exception as e:
            print(f"Connection closed: {e}")

        finally:
            if client:
                try:
                    client.close()
                except:
                    pass

            if dropbear:
                try:
                    dropbear.close()
                except:
                    pass

def generate_accept_key(client_key:str):
    client_key +=  MAGIC_STRING
    sha1_hash = hashlib.sha1(client_key.encode())
    digest = sha1_hash.digest()
    return base64.b64encode(digest).decode()

def extract_header(headers: list, header_name:str):
    for header in headers:
        if header.startswith(header_name):
            return header

def extract_header_value(header:str):
    return header.split(":", 1)[1].strip() if header is not None else None

def decode_frame_header(first_byte: int, second_byte: int):
    fin = (first_byte & 0b10000000) >> 7
    opcode = first_byte & 0b00001111
    masked = (second_byte & 0b10000000) >> 7
    payload_length = second_byte & 0b01111111
    
    return {
        "fin": fin,
        "opcode": opcode,
        "masked": masked,
        "payload_length": payload_length
    }

def unmask_payload(masking_key: bytes, payload: bytes):
    decoded = bytearray()

    for i in range(len(payload)):
        decoded.append(payload[i] ^ masking_key[i % 4])

    return decoded

def recv_exact(sock, length):
    data = bytearray()

    while len(data) < length:
        chunk = sock.recv(length - len(data))

        if not chunk:
            return None

        data.extend(chunk)

    return data

def receive_frame(client):
    frame_header = recv_exact(client, 2)

    if frame_header is None:
        return None

    first_byte = frame_header[0]
    second_byte = frame_header[1]

    frame = decode_frame_header(first_byte, second_byte)

    # Reject fragmented frames
    if frame["fin"] == 0:
        raise NotImplementedError("Fragmented frames are not supported.")

    # Handle control frames
    if frame["opcode"] == 0x8:  # Close
        return None

    if frame["opcode"] == 0x9:  # Ping
        send_pong(client)
        return b""

    if frame["opcode"] == 0xA:  # Pong
        return b""

    payload_length = frame["payload_length"]

    if payload_length == 126:
        extended_length = recv_exact(client, 2)

        if extended_length is None:
            return None

        payload_length = int.from_bytes(extended_length, "big")

    elif payload_length == 127:
        extended_length = recv_exact(client, 8)

        if extended_length is None:
            return None

        payload_length = int.from_bytes(extended_length, "big")

    masking_key = recv_exact(client, 4)

    if masking_key is None:
        return None

    payload = recv_exact(client, payload_length)

    if payload is None:
        return None

    return unmask_payload(masking_key, payload)

def send_pong(client):
    frame = bytes([0x8A, 0x00])
    client.sendall(frame)

def send_frame(client, payload: bytes):
    first_byte = 0x82

    payload_length = len(payload)

    if payload_length <= 125:
        header = bytes([
            first_byte,
            payload_length
        ])

    elif payload_length <= 65535:
        header = bytes([
            first_byte,
            126
        ]) + payload_length.to_bytes(2, "big")

    else:
        header = bytes([
            first_byte,
            127
        ]) + payload_length.to_bytes(8, "big")

    client.sendall(header + payload)

main()