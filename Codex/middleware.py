import time
from django.http import HttpResponse
from django.core.cache import cache

class SecurityHeadersMiddleware:
    """
    Middleware that adds security headers to all HTTP responses to protect
    against XSS, Clickjacking, MIME-sniffing, and data injection attacks.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Prevent MIME-sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        # Prevent Clickjacking inside iframes
        response.headers['X-Frame-Options'] = 'DENY'
        # XSS Filter protection for legacy browsers
        response.headers['X-XSS-Protection'] = '1; mode=block'
        # Referrer privacy policy
        response.headers['Referrer-Policy'] = 'same-origin'
        # Feature/Permissions policy restricting hardware access
        response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=(), payment=()'
        
        # Content Security Policy (CSP)
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com data:; "
            "img-src 'self' data: media: blob:; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        response.headers['Content-Security-Policy'] = csp
        
        return response


class LoginRateLimitMiddleware:
    """
    Middleware to limit failed login attempts per IP address to prevent brute-force attacks.
    Locks out suspicious IPs for 5 minutes after 5 consecutive failed attempts.
    """
    MAX_ATTEMPTS = 5
    LOCKOUT_TIME = 300  # 5 minutes in seconds

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        is_login_path = request.path.rstrip('/') in ['/login', '/connexion']
        if is_login_path and request.method == 'POST':
            client_ip = self.get_client_ip(request)
            key = f"rate_limit_login_{client_ip}"
            attempts_info = cache.get(key, {'count': 0, 'first_attempt': time.time()})

            if attempts_info['count'] >= self.MAX_ATTEMPTS:
                elapsed = time.time() - attempts_info['first_attempt']
                if elapsed < self.LOCKOUT_TIME:
                    remaining_time = int(self.LOCKOUT_TIME - elapsed)
                    return HttpResponse(
                        f"""
                        <!DOCTYPE html>
                        <html lang="fr">
                        <head><meta charset="utf-8"><title>Accès temporairement bloqué - Sécurité Codex</title>
                        <style>
                          body {{ font-family: Inter, sans-serif; background: #0f172a; color: white; display: grid; place-items: center; min-height: 100vh; margin: 0; }}
                          .card {{ background: #1e293b; padding: 36px; border-radius: 20px; border: 1px solid #334155; text-align: center; max-width: 420px; box-shadow: 0 20px 40px rgba(0,0,0,0.4); }}
                          h1 {{ color: #ef4444; font-size: 1.5rem; margin-bottom: 12px; }}
                          p {{ color: #94a3b8; line-height: 1.6; font-size: 0.95rem; }}
                          .timer {{ font-size: 1.8rem; font-weight: 800; color: #f59e0b; margin: 18px 0; }}
                        </style>
                        </head>
                        <body>
                          <div class="card">
                            <h1>🔒 Bloqué pour Sécurité</h1>
                            <p>Trop de tentatives de connexion échouées depuis votre adresse IP.</p>
                            <p>Par mesure de sécurité contre les attaques par force brute, l'accès est temporairement suspendu.</p>
                            <div class="timer">Veuillez patienter {remaining_time}s</div>
                            <p style="font-size:0.8rem;color:#64748b;">Système de protection anti-intrusion Codex</p>
                          </div>
                        </body>
                        </html>
                        """,
                        status=429
                    )

        response = self.get_response(request)

        # Increment count if login failed (status code 200 re-rendering form with errors or 400)
        if is_login_path and request.method == 'POST':
            client_ip = self.get_client_ip(request)
            key = f"rate_limit_login_{client_ip}"
            if response.status_code != 302:  # 302 redirect indicates successful login
                attempts_info = cache.get(key, {'count': 0, 'first_attempt': time.time()})
                attempts_info['count'] += 1
                cache.set(key, attempts_info, self.LOCKOUT_TIME)
            else:
                # Clear counter on successful login
                cache.delete(key)

        return response

    @staticmethod
    def get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        return ip
