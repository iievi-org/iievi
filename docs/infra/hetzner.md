# Hetzner VPS Provisioning & Hardening

Target: CX32 (4 vCPU, 8 GB RAM), Singapore (`sin` location), Ubuntu 24.04 LTS.

## 1. Provision

Console: https://console.hetzner.cloud → New Server → Singapore → CX32 →
Ubuntu 24.04 → add your SSH public key → create.

Or with the hcloud CLI:

```bash
hcloud server create --name iievi-prod --type cx32 --location sin \
  --image ubuntu-24.04 --ssh-key <your-key-name>
```

## 2. Harden (lockout-safe order)

```bash
scp infra/scripts/harden-vps.sh root@<vps-ip>:/root/
ssh root@<vps-ip> bash harden-vps.sh
```

The script enforces the exact sequence from the infrastructure spec:

1. Create `deploy` user, copy SSH key to `~deploy/.ssh/authorized_keys`
2. **Pause and require confirmation** that `ssh deploy@<ip>` works
3. Only then: disable root login + password auth in sshd
4. UFW: allow 22/80/443, deny everything else
5. fail2ban with default config
6. Install nginx, certbot (+nginx plugin), Python 3.12, Redis 7, Supervisor,
   Playwright Chromium libraries (E2E testing), Doppler CLI
7. Create `/srv/iievi` and `/var/log/iievi` owned by deploy

## 3. Application setup (as deploy)

```bash
ssh deploy@<vps-ip>
git clone git@github.com:<ORG>/iievi.git /srv/iievi
cd /srv/iievi/apps/api && uv sync --frozen
doppler setup --project iievi --config prd   # use a prd service token
```

## 4. nginx + TLS

```bash
sudo cp /srv/iievi/infra/nginx/iievi-api.conf /etc/nginx/sites-available/
sudo sed -i 's/api.iievi.example/<your-api-domain>/g' /etc/nginx/sites-available/iievi-api.conf
sudo ln -s /etc/nginx/sites-available/iievi-api.conf /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d <your-api-domain>       # obtains cert, rewires TLS lines
sudo systemctl list-timers | grep certbot        # renewal timer — verify it exists
```

certbot's systemd timer handles renewal twice daily; no manual cron needed
(add `0 3 * * * certbot renew --quiet` to root's crontab only if you disable
the timer).

## 5. Supervisor

```bash
sudo cp /srv/iievi/infra/supervisor/iievi.conf /etc/supervisor/conf.d/
sudo cp /srv/iievi/infra/logrotate/iievi /etc/logrotate.d/
sudo supervisorctl reread && sudo supervisorctl update
sudo supervisorctl status    # all four iievi:* processes must show RUNNING
```

## 6. Deploy pipeline access

Add repository secrets: `VPS_HOST`, `VPS_SSH_KEY` (a dedicated deploy keypair,
not your personal key), `API_BASE_URL`, `DOPPLER_TOKEN`, `VERCEL_DEPLOY_HOOK`.
Allow the deploy user passwordless `sudo supervisorctl` (already granted via
sudoers in the hardening script).
