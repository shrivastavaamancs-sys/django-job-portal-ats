from django.http import HttpResponseForbidden

from .models import AccessToken


class InviteTokenMiddleware:
    PROTECTED_PREFIXES = (
        "/jd/",
        "/upload-resume/",
        "/candidate/",
        "/result-filter/",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.access_token = None

        if any(request.path.startswith(p) for p in self.PROTECTED_PREFIXES):
            user = getattr(request, "user", None)
            if user and user.is_authenticated and user.is_staff:
                return self.get_response(request)

            query_token = (request.GET.get("token") or "").strip()
            if query_token:
                request.session["invite_token"] = query_token

            session_token = request.session.get("invite_token")
            token_obj = (
                AccessToken.objects.filter(token=session_token, is_active=True).first()
                if session_token
                else None
            )

            if not token_obj:
                if session_token:
                    request.session.pop("invite_token", None)
                return HttpResponseForbidden(
                    "<h3>Access Restricted</h3><p>Valid access token link use karein (e.g. ?token=YOUR_TOKEN).</p>"
                )

            request.access_token = token_obj

            if not token_obj.can_edit and request.method not in ("GET", "HEAD", "OPTIONS"):
                return HttpResponseForbidden(
                    "<h3>View-Only Access</h3><p>Aapko sirf dekhne ki permission hai.</p>"
                )

        return self.get_response(request)