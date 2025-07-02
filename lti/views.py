from django.shortcuts import render
from django.http import HttpResponse

def lti_launch(request):
    return HttpResponse("LTI Launch endpoint - Will implement LTI 1.3 authentication here")