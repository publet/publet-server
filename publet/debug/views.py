from django.http import Http404
from django.shortcuts import render


def home(request):
    return render(request, 'debug_list.html')


def handle_404(request):
    raise Http404


def handle_500(request):
    a = []
    print a[2]
