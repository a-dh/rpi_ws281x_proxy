# RPi WS281x Userland Proxy

Driving WS281x (NeoPixel) LEDs from a Raspberry Pi needs root, because the
[rpi_ws281x](https://github.com/jgarff/rpi_ws281x) library uses DMA and PWM.
This project splits that into:

- **`rpi-led-proxy`**: a small root daemon (systemd service) that owns the strip
  and listens on a Unix socket.
- **`wsled-ctl`**: an unprivileged CLI that sends colour commands to the daemon.
  It ships in the same `.deb` as the daemon.
- **`WSLEDClient`**: the Python client behind `wsled-ctl`, pip-installable so any
  process, such as a ROS 2 node, can set LEDs without root.

Tested on a Raspberry Pi running Ubuntu 24.04 with a 2-pixel strip.

## Hardware configuration

- Data line on **GPIO 12** (PWM channel 0, physical pin 32), DMA channel 10.
  These are set as constants at the top of `src/wsled_proxy.py`.
- PWM conflicts with onboard audio. Set `dtparam=audio=off` in
  `/boot/firmware/config.txt` and reboot.

## Installation

### 1. The daemon and CLI (Debian package)

Build the Debian package from the repository root on the Pi, then install it:

```bash
sudo apt install python3-rpi-ws281x   # hardware driver used by the daemon
./scripts/build_deb.sh
sudo dpkg -i rpi-led-proxy_*_all.deb
```

The package installs the daemon (`wsled_proxy.py`), the `wsled-ctl` CLI and their
shared modules (`wsled_client.py`, `shared_config.py`) to `/usr/local/bin/`, plus
the `rpi-led-proxy.service` unit, then enables and starts the service. It
starts early in boot (after `local-fs.target`, before `network-pre.target`), so
start-up colours appear quickly.

To remove it (this also stops and disables the service):

```bash
sudo dpkg -r rpi-led-proxy
```

### 2. The Python client (optional)

`wsled-ctl` needs nothing beyond the package. To use `WSLEDClient` from your own
Python code, install it into that code's environment:

```bash
pip install .
```

## Configuration

The daemon reads environment variables from its systemd unit. Override them with
a drop-in (`sudo systemctl edit rpi-led-proxy`) rather than editing the unit:

| Variable | Default | Meaning |
|---|---|---|
| `LED_COUNT` | `2` | Number of pixels on the strip |
| `LED_BRIGHTNESS` | `128` | Global hardware brightness, 0–255 |
| `LED_INIT_COLORS` | *(empty)* | Comma-separated per-pixel colours shown at start-up, e.g. `#00ff00,#ff0000` |

Example drop-in:

```ini
[Service]
Environment="LED_COUNT=8"
Environment="LED_INIT_COLORS=#00ff00,#ff0000"
```

## Usage

```bash
wsled-ctl --poll             # print the pixel count reported by the daemon
wsled-ctl green              # all pixels green
wsled-ctl "#FFA500" -b 0.2   # all pixels orange at 20% intensity
wsled-ctl red -i 1 -b 0.5    # pixel 1 red at 50%
wsled-ctl off
```

Named colours are `red`, `green`, `blue` and `off`; anything else must be a
`#rgb` or `#rrggbb` hex value. An unknown colour is an error, and brightness is
clamped to 0.0–1.0. `wsled-ctl` exits with status 1 if the daemon isn't running.

From Python:

```python
from wsled_client import WSLEDClient

leds = WSLEDClient()
leds.set_intensity_color("green", intensity=0.2, index=0)  # False if the daemon is down
leds.off()
```

`scripts/ros2_example.py` and `scripts/ros2_battery_indicator_node.py` show
the client used from ROS 2 nodes.

### Perceived brightness

The eye perceives brightness roughly logarithmically:

- 0.1–0.2: subtle status indication (recommended)
- 0.33: mid-level
- 1.0: full intensity (alerts, blinking)

## Socket protocol

The daemon listens on `/run/rpi-led-proxy/wsled_socket` (mode 0666). The client
falls back to `/tmp/wsled_socket` when that path doesn't exist. Each connection
carries one text command:

| Command | Effect | Reply |
|---|---|---|
| `#rrggbb` or a colour name | Set every pixel | none |
| `<index>:#rrggbb` | Set one pixel | none |
| `get_count` | Query the pixel count | the count, as text |

The daemon ignores invalid commands and logs them to the journal. Because the
socket is world-writable, any local user can change the LEDs.

## License

MIT. See [LICENSE](LICENSE).
