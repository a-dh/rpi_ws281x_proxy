#!/bin/bash
# Automation script to build the rpi-led-proxy Debian package
set -e
# Run from the repository root wherever the script is called from
cd "$(dirname "$0")/.."

PKG_NAME="rpi-led-proxy"
# Single source of truth for the version: pyproject.toml
VERSION=$(sed -n 's/^version = "\(.*\)"/\1/p' pyproject.toml)
BUILD_DIR="${PKG_NAME}_${VERSION}_all"

echo "🔨 Starting build for ${PKG_NAME}..."

# 1. Clean up old builds
rm -rf "$BUILD_DIR"
rm -f "${BUILD_DIR}.deb"

# 2. Create directory structure
mkdir -p "$BUILD_DIR/DEBIAN"
mkdir -p "$BUILD_DIR/usr/local/bin"
mkdir -p "$BUILD_DIR/lib/systemd/system"

# 3. Copy application files
# Explicit modes: the daemon runs as root, so nothing may be group/other-writable
install -m 644 src/wsled_proxy.py src/shared_config.py "$BUILD_DIR/usr/local/bin/"
# Userland CLI; imports wsled_client/shared_config from its own directory
install -m 644 src/wsled_client.py "$BUILD_DIR/usr/local/bin/"
install -m 755 src/wsled_ctl.py "$BUILD_DIR/usr/local/bin/wsled-ctl"
install -m 644 scripts/led-proxy.service "$BUILD_DIR/lib/systemd/system/${PKG_NAME}.service"

# 4. Create the Control file
cat << EOC > "$BUILD_DIR/DEBIAN/control"
Package: ${PKG_NAME}
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: all
Depends: python3, python3-rpi-ws281x
Maintainer: Albert den Haan <albert.denhaan@gmail.com>
Description: Hardened WS281x LED proxy daemon and wsled-ctl CLI.
EOC

# 5. Create the Post-Installation script
cat << EOP > "$BUILD_DIR/DEBIAN/postinst"
#!/bin/sh
set -e
if [ "\$1" = "configure" ]; then
    echo "⚙️  Reloading systemd and starting ${PKG_NAME}..."
    systemctl daemon-reload
    systemctl enable ${PKG_NAME}.service
    systemctl restart ${PKG_NAME}.service
fi
EOP
chmod 755 "$BUILD_DIR/DEBIAN/postinst"

# 6. Stop and disable the service on removal (not on upgrade: postinst restarts it)
cat << EOP > "$BUILD_DIR/DEBIAN/prerm"
#!/bin/sh
set -e
if [ "\$1" = "remove" ] || [ "\$1" = "deconfigure" ]; then
    systemctl disable --now ${PKG_NAME}.service || true
fi
EOP
chmod 755 "$BUILD_DIR/DEBIAN/prerm"

cat << EOP > "$BUILD_DIR/DEBIAN/postrm"
#!/bin/sh
set -e
if [ "\$1" = "remove" ] || [ "\$1" = "purge" ]; then
    systemctl daemon-reload || true
fi
EOP
chmod 755 "$BUILD_DIR/DEBIAN/postrm"

# 7. Build the package
# Files are owned by root in the package, not by whoever built it
chmod -R go-w "$BUILD_DIR"
dpkg-deb --root-owner-group --build "$BUILD_DIR"

echo "✅ Build complete: ${BUILD_DIR}.deb"
