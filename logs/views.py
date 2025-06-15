# core/views.py (or wherever your Log model is)

from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.db.models import Q
from .models import Log

User = get_user_model()

def log_list_view(request):
    logs = Log.objects.all().order_by('-created_at')

    user = request.GET.get('user')
    keyword = request.GET.get('keyword')
    date = request.GET.get('date')

    if user:
        logs = logs.filter(user_id=user)
    if keyword:
        logs = logs.filter(log__icontains=keyword)
    if date:
        logs = logs.filter(created_at__date=date)

    users = User.objects.all()
    return render(request, 'logs/log_list.html', {
        'logs': logs,
        'users': users,
        'filter_user': user,
        'filter_keyword': keyword,
        'filter_date': date,
    })
