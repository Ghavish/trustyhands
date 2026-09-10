from django.shortcuts import render

from django.http import HttpResponse

def provider_dashboard(request):
    return HttpResponse("<h1>This is the Service Provider Page</h1>")