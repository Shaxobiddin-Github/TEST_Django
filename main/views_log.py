import os
import json
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from .models import Log

User = get_user_model()

@csrf_exempt
def log_action(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            action = data.get('action')
            user_id = data.get('user_id')
            user = User.objects.filter(id=user_id).first()
            Log.objects.create(user=user, action=action)

            # Faqat kerakli harakatlar va vaqt
            if user and action in ['Sahifani tark etdi', 'Sahifaga qaytdi']:
                base_dir = os.path.join(
                    os.path.dirname(__file__),
                    'templates', 'test_api', 'harakat', user.username
                )
                os.makedirs(base_dir, exist_ok=True)
                file_path = os.path.join(base_dir, 'actions.txt')
                now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                with open(file_path, 'a', encoding='utf-8') as f:
                    f.write(f"{now} - {action}\n")

            return JsonResponse({'status': 'ok'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Only POST allowed'}, status=405)