from annoying.decorators import render_to
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


@login_required
@render_to('home.html')
def home(request):

    if request.user.is_basic or request.user.is_pro or request.user.is_free:
        return redirect('groups-list')

    if request.user.is_reader:
        return redirect('reader-dashboard')


@login_required
@render_to('styleguide.html')
def styleguide(request):
    return {}
