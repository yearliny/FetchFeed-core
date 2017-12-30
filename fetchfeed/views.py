from django.shortcuts import render
from django.http import JsonResponse
from . import prc


def index(request):
    return render(request, "fetchfeed/index.html")


def api(request, meth):
    if meth == 'get':
        url = request.GET.get('url')
        page_html = prc.GetPage(url).read()
    return JsonResponse(page_html)

