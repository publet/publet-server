"""
Publet
Copyright (C) 2018  Publet Inc.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
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
