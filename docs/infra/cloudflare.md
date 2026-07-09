# Cloudflare CDN, WAF & DNS

All production traffic passes through Cloudflare (proxy/orange-cloud mode).

## DNS

| Record | Type | Target | Proxy |
|---|---|---|---|
| `iievi.<tld>` (marketing) | CNAME | Vercel | Proxied |
| `app.iievi.<tld>` (web app) | CNAME | Vercel | Proxied |
| `api.iievi.<tld>` | A | Hetzner VPS IP | Proxied |

SSL/TLS mode: **Full (strict)** — the origin has a valid Let's Encrypt cert.

## WAF

Security → WAF → Managed rules → enable **Cloudflare Managed Ruleset** and the
**OWASP Core Rule Set** (paranoia level default, action: managed challenge).

## Caching rules

1. **Marketing static assets** — `iievi.<tld>/*.(css|js|woff2|png|jpg|svg|webp)`:
   Cache Level: Cache Everything, Edge TTL: 1 year.
2. **API pass-through** — `api.iievi.<tld>/*`: Bypass cache.
3. **Health endpoint exception** — `api.iievi.<tld>/health`:
   Cache Everything, Edge TTL: 30 seconds (nginx also sends
   `Cache-Control: public, max-age=30`).

Order matters: the /health rule must sit ABOVE the API bypass rule.

## Bots & DDoS

- Security → Bots → enable **Bot Fight Mode**.
- DDoS protection is automatic; leave the HTTP DDoS managed ruleset on
  default sensitivity. Add an override only if legitimate spikes (campaign
  launches) get challenged.

## Country header for payment routing

`CF-IPCountry` is injected by enabling: Rules → Settings (Managed Transforms)
→ **Add visitor location headers**. The API reads this header to route
Razorpay (IN) vs Stripe (everywhere else). No custom Transform Rule needed —
the managed transform provides `CF-IPCountry` on every proxied request.

## Origin protection (recommended)

Restrict UFW port 443/80 to Cloudflare IP ranges once everything works
(https://www.cloudflare.com/ips/), so the origin cannot be hit directly.
Keep 22 open to your own IP or use Cloudflare Access + tunnels later.
