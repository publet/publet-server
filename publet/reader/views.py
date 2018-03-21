from annoying.decorators import render_to
from django.contrib.auth.decorators import login_required
from publet.payments.models import Purchase
from publet.projects.models import Publication


@login_required
@render_to('reader/dashboard.html')
def dashboard(request):

    purchases = Purchase.objects.filter(user=request.user)

    return {
        'purchases': purchases
    }


@login_required
@render_to('reader/featured.html')
def featured(request):
    free = Publication.objects.filter(price__isnull=True, status='live')[:5]
    newest = Publication.objects.order_by('-modified')[:5]

    return {
        'free': free,
        'newest': newest,
        'popular': []
    }
