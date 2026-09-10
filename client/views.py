from django.shortcuts import render

from django.http import HttpResponse

def client_dashboard(request):
    return HttpResponse("<h1>This is the Client Page</h1>")