import os

# The package/service name used for directory paths
APP_NAME = "rpi-led-proxy"
SOCKET_NAME = "wsled_socket"

def get_socket_path():
    # systemd automatically sets RUNTIME_DIRECTORY if RuntimeDirectory= is used
    # This is the most reliable way to avoid hardcoding /run/ paths.
    runtime_dir = os.environ.get("RUNTIME_DIRECTORY")
    
    if runtime_dir:
        return os.path.join(runtime_dir, SOCKET_NAME)
    
    # Fallback for userland client or manual dev testing
    standard_run_path = f"/run/{APP_NAME}/{SOCKET_NAME}"
    if os.path.exists(standard_run_path):
        return standard_run_path
        
    return f"/tmp/{SOCKET_NAME}"

SOCKET_PATH = get_socket_path()
