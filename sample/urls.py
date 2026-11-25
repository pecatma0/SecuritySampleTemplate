from django.http import HttpResponse, JsonResponse
from django.urls import path
from django.views.decorators.http import require_safe


@require_safe
def home(request):
    return HttpResponse(
        '<!doctype html><html lang="ja"><meta charset="utf-8">'
        '<title>Django セキュリティチェック</title>'
        '<h1>Django セキュリティチェック</h1>'
        '<p><a href="/healthz/">稼働状態</a></p></html>',
        headers={
            "Content-Security-Policy": (
                "default-src 'none'; base-uri 'none'; form-action 'none'; "
                "frame-ancestors 'none'"
            ),
            "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
            "Cache-Control": "no-store",
        },
    )


@require_safe
def health(request):
    return JsonResponse({"status": "ok"}, headers={"Cache-Control": "no-store"})


urlpatterns = [path("", home), path("healthz/", health)]
