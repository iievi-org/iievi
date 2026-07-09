#!/usr/bin/env bash
# IIEVI Hetzner VPS hardening — Ubuntu 24.04 LTS, run as root ONCE on a fresh box.
#
#   scp infra/scripts/harden-vps.sh root@<vps-ip>:/root/ && ssh root@<vps-ip> bash harden-vps.sh
#
# The sequence is lockout-safe: the deploy user + SSH key are created and
# VERIFIED before root login and password auth are disabled. The script stops
# and waits for you to confirm key-based login works.

set -euo pipefail

DEPLOY_USER="deploy"

if [[ $EUID -ne 0 ]]; then
    echo "Run as root" >&2
    exit 1
fi

# ---------------------------------------------------------------------------
# 1. Deploy user + SSH key (BEFORE any SSH lockdown)
# ---------------------------------------------------------------------------
if ! id "$DEPLOY_USER" &>/dev/null; then
    adduser --disabled-password --gecos "" "$DEPLOY_USER"
    usermod -aG sudo "$DEPLOY_USER"
    echo "$DEPLOY_USER ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/90-deploy
    chmod 440 /etc/sudoers.d/90-deploy
fi

install -d -m 700 -o "$DEPLOY_USER" -g "$DEPLOY_USER" /home/$DEPLOY_USER/.ssh
if [[ ! -s /home/$DEPLOY_USER/.ssh/authorized_keys ]]; then
    if [[ -s /root/.ssh/authorized_keys ]]; then
        cp /root/.ssh/authorized_keys /home/$DEPLOY_USER/.ssh/authorized_keys
    else
        echo "ERROR: /root/.ssh/authorized_keys is empty — add your public key first." >&2
        exit 1
    fi
    chown "$DEPLOY_USER:$DEPLOY_USER" /home/$DEPLOY_USER/.ssh/authorized_keys
    chmod 600 /home/$DEPLOY_USER/.ssh/authorized_keys
fi

echo
echo "=================================================================="
echo " STOP. From your LOCAL machine, verify key-based login works:"
echo "     ssh $DEPLOY_USER@$(hostname -I | awk '{print $1}')"
echo " Do NOT continue until that succeeds."
echo "=================================================================="
read -rp "Did 'ssh $DEPLOY_USER@<ip>' work? (yes/no) " CONFIRM
[[ "$CONFIRM" == "yes" ]] || { echo "Aborting before SSH lockdown."; exit 1; }

# ---------------------------------------------------------------------------
# 2. SSH lockdown (only after key login is confirmed)
# ---------------------------------------------------------------------------
mkdir -p /etc/ssh/sshd_config.d
cat > /etc/ssh/sshd_config.d/90-iievi-hardening.conf <<'EOF'
PermitRootLogin no
PasswordAuthentication no
KbdInteractiveAuthentication no
X11Forwarding no
MaxAuthTries 3
EOF
sshd -t
systemctl reload ssh

# ---------------------------------------------------------------------------
# 3. Firewall: 22, 80, 443 only
# ---------------------------------------------------------------------------
apt-get update
apt-get install -y ufw
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# ---------------------------------------------------------------------------
# 4. fail2ban (default config protects sshd out of the box)
# ---------------------------------------------------------------------------
apt-get install -y fail2ban
systemctl enable --now fail2ban

# ---------------------------------------------------------------------------
# 5. Runtime packages
# ---------------------------------------------------------------------------
apt-get install -y \
    nginx \
    certbot python3-certbot-nginx \
    python3.12 python3.12-venv \
    redis-server \
    supervisor \
    git curl

# Playwright Chromium system libraries (E2E testing; not server-side rendering).
# Ubuntu 24.04 renamed libasound2 -> libasound2t64.
apt-get install -y \
    chromium-browser libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libgbm1 \
    libasound2t64 || apt-get install -y libasound2

systemctl enable --now redis-server nginx supervisor

# ---------------------------------------------------------------------------
# 6. Doppler CLI (secrets at runtime — no .env files on the box, ever)
# ---------------------------------------------------------------------------
if ! command -v doppler &>/dev/null; then
    curl -Ls https://cli.doppler.com/install.sh | sh
fi

# ---------------------------------------------------------------------------
# 7. Application directories
# ---------------------------------------------------------------------------
install -d -o "$DEPLOY_USER" -g "$DEPLOY_USER" /srv/iievi
install -d -o "$DEPLOY_USER" -g "$DEPLOY_USER" /var/log/iievi

echo
echo "Hardening complete. Next steps (docs/infra/hetzner.md):"
echo "  1. As deploy: clone the repo into /srv/iievi and run 'doppler setup' (production config)"
echo "  2. Copy infra/nginx/iievi-api.conf into /etc/nginx/sites-available/ (fix domain), enable, reload"
echo "  3. certbot --nginx -d <api-domain>   (auto-renewal timer is installed by certbot)"
echo "  4. Copy infra/supervisor/iievi.conf to /etc/supervisor/conf.d/ && supervisorctl reread && update"
echo "  5. Copy infra/logrotate/iievi to /etc/logrotate.d/"
