from django.shortcuts import render

def activity_list(request):
    return render(request, 'activity/activity_list.html')