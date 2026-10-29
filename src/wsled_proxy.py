import os
import socket
import sys
import re
from rpi_ws281x import PixelStrip, Color
from shared_config import SOCKET_PATH

LED_COUNT      = int(os.environ.get("LED_COUNT", 2))
LED_BRIGHTNESS = int(os.environ.get("LED_BRIGHTNESS", 128))
# Optional colours shown as soon as the strip is up, one per index: "#00ff00,#ff0000"
LED_INIT_COLORS = os.environ.get("LED_INIT_COLORS", "")
LED_PIN        = 12      
LED_FREQ_HZ    = 800000  
LED_DMA        = 10      
LED_INVERT     = False   
LED_CHANNEL    = 0       

def get_color(val):
    if not re.match(r'^#[0-9a-fA-F]{6}$|^[a-z]+$', val):
        return None
    colors = {"red": (255,0,0), "green": (0,255,0), "blue": (0,0,255), "off": (0,0,0)}
    if val in colors: return Color(*colors[val])
    if val.startswith('#'):
        c = val.lstrip('#')
        return Color(*tuple(int(c[i:i+2], 16) for i in (0, 2, 4)))
    return None

def main():
    if os.geteuid() != 0:
        print("Error: DMA access requires root.")
        sys.exit(1)

    strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    strip.begin()

    for i, col in enumerate(LED_INIT_COLORS.split(",")[:LED_COUNT]):
        color = get_color(col.strip().lower())
        if color is not None:
            strip.setPixelColor(i, color)
    strip.show()

    if os.path.exists(SOCKET_PATH): os.remove(SOCKET_PATH)
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(SOCKET_PATH)
    os.chmod(SOCKET_PATH, 0o666)
    server.listen(5)

    while True:
        conn, _ = server.accept()
        # A client that connects but never sends must not block the daemon
        conn.settimeout(1.0)
        try:
            data = conn.recv(1024).decode().strip().lower()
            if data == "get_count":
                conn.sendall(str(LED_COUNT).encode())
            elif ":" in data:
                idx, col = data.split(":", 1)
                color = get_color(col)
                if 0 <= int(idx) < LED_COUNT and color:
                    strip.setPixelColor(int(idx), color)
                    strip.show()
            else:
                color = get_color(data)
                if color:
                    for i in range(strip.numPixels()): strip.setPixelColor(i, color)
                    strip.show()
        except (OSError, ValueError) as e:
            # Bad input or a client gone away: log it and keep serving
            print(f"wsled_proxy: ignoring request: {e}", file=sys.stderr, flush=True)
        finally: conn.close()

if __name__ == '__main__':
    main()
