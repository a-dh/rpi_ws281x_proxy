import re
import socket
from shared_config import SOCKET_PATH

class WSLEDClient:
    def __init__(self):
        self.socket_path = SOCKET_PATH
        self.colors = {"red": (255,0,0), "green": (0,255,0), "blue": (0,0,255), "off": (0,0,0)}

    def _send(self, cmd):
        """Send one command. Returns the reply ("" if none), or None if the proxy is unreachable."""
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                client.settimeout(2.0)
                client.connect(self.socket_path)
                client.sendall(cmd.encode())
                return client.recv(1024).decode()
        except OSError:
            return None

    def parse_color(self, color):
        """Return (r, g, b) for a colour name, #rgb or #rrggbb; raise ValueError otherwise."""
        c = color.strip().lower()
        if c in self.colors:
            return self.colors[c]
        if re.fullmatch(r'#[0-9a-f]{3}', c):
            c = '#' + ''.join(ch * 2 for ch in c[1:])
        if re.fullmatch(r'#[0-9a-f]{6}', c):
            return tuple(int(c[i:i+2], 16) for i in (1, 3, 5))
        raise ValueError(f"unknown colour {color!r}: use {', '.join(self.colors)} or #rrggbb")

    def set_intensity_color(self, color, intensity=1.0, index=None):
        """Set all pixels (or one, by index). Returns False if the proxy is unreachable."""
        r, g, b = self.parse_color(color)
        intensity = min(max(intensity, 0.0), 1.0)
        r, g, b = int(r * intensity), int(g * intensity), int(b * intensity)
        hex_val = f"#{r:02x}{g:02x}{b:02x}"
        return self._send(f"{index}:{hex_val}" if index is not None else hex_val) is not None

    def get_count(self):
        res = self._send("get_count")
        return int(res) if res else 0

    def off(self):
        return self.set_intensity_color("off")
