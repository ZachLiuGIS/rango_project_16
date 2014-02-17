from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse


# Create your views here.
def index(request):
    return render(request, 'rango/index.html', {'boldmessage': 'Zach'})


def about(request):
    return render(request, 'rango/about.html')