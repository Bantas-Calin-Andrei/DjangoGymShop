import time
from django.core.mail import mail_admins

class LoginAttemptMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.failed_logins = {}  # Stocare încercări eșuate

    def __call__(self, request):
        if request.path == '/magazin/login/' and request.method == 'POST':
            username = request.POST.get('username', '')
            ip = self.get_client_ip(request)

            if username:
                # Inițializează sau actualizează încercările eșuate
                if username not in self.failed_logins:
                    self.failed_logins[username] = []
                self.failed_logins[username].append((ip, time.time()))

                # Filtrează încercările mai vechi de 2 minute
                self.failed_logins[username] = [
                    attempt for attempt in self.failed_logins[username]
                    if time.time() - attempt[1] < 120
                ]

                # Trimite email dacă există 3 încercări eșuate în ultimele 2 minute
                if len(self.failed_logins[username]) >= 3:
                    subject = "Logări suspecte"
                    message_text = f"Username: {username}\nIP: {ip}"
                    message_html = f"""
                    <h1 style="color: red;">Logări suspecte</h1>
                    <p>Username: {username}</p>
                    <p>IP: {ip}</p>
                    """
                    mail_admins(subject, message_text, html_message=message_html)

        return self.get_response(request)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')
