from django.shortcuts import render

def advanced_features(request):
    return render(request, 'advanced/advanced_features.html')
