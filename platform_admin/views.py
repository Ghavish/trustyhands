from django.shortcuts import render

from django.http import HttpResponse

def admin_dashboard(request):
    return HttpResponse("<h1>This is the Admin Page</h1>")