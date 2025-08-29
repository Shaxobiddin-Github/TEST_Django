from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from main.models import StudentTest, Group, Bulim, Kafedra, User, Test
from django.views.decorators.http import require_POST
from django.http import JsonResponse

@login_required
def participated_students_list(request):
    from main.models import StudentAnswer
    from django.db.models import Count, Case, When, F, FloatField, Value
    from django.db.models.functions import Cast
    from django.db.models import Count, Case, When, F, FloatField

    # Guruhlar, bo'limlar va kafedralarni aniqlash
    groups = Group.objects.all()
    bulims = Bulim.objects.all()
    kafedras = Kafedra.objects.all()

    # Test natijalarini olish
    student_tests = StudentTest.objects.filter(completed=True).select_related(
        'student', 'test', 'group', 'subject', 'semester'
    ).prefetch_related('answers')

    # Har bir test uchun natijalarni hisoblash va test obyektiga qo'shish
    for st in student_tests:
        answers = StudentAnswer.objects.filter(student_test=st)
        if st.question_ids:
            answers = answers.filter(question_id__in=st.question_ids)
        total = answers.count()
        correct = answers.filter(is_correct=True).count()
        st.total_answers = total
        st.correct_answers_count = correct
        st.percent_result = round((correct / total * 100), 1) if total > 0 else 0


    # Guruhlar uchun
    group_data = {}
    group_tests_list = list(student_tests)
    for group in groups:
        group_students = {}
        for st in group_tests_list:
            if st.group == group:
                student = st.student
                if student not in group_students:
                    group_students[student] = []
                group_students[student].append(st)
        if group_students:
            group_data[group] = group_students

    # Bo'limlar uchun
    bulim_data = {}
    for bulim in bulims:
        bulim_users = {}
        for st in group_tests_list:
            if hasattr(st.test, 'bulim') and st.test.bulim == bulim:
                user = st.student
                if user.role != 'student':
                    continue
                if user not in bulim_users:
                    bulim_users[user] = []
                bulim_users[user].append(st)
        if bulim_users:
            bulim_data[bulim] = bulim_users

    # Kafedralar uchun
    kafedra_data = {}
    for kafedra in kafedras:
        kafedra_users = {}
        for st in group_tests_list:
            if hasattr(st.test, 'kafedra') and st.test.kafedra == kafedra:
                user = st.student
                if user.role != 'student':
                    continue
                if user not in kafedra_users:
                    kafedra_users[user] = []
                kafedra_users[user].append(st)
        if kafedra_users:
            kafedra_data[kafedra] = kafedra_users
    return render(request, 'controller_panel/participated_students_list.html', {
        'group_data': group_data,
        'bulim_data': bulim_data,
        'kafedra_data': kafedra_data,
    })

@require_POST
@login_required
def allow_retake(request):
    stest_id = request.POST.get('stest_id')
    password = request.POST.get('password')
    if password != '96970204':
        return JsonResponse({'success': False, 'error': 'Parol noto‘g‘ri!'}, status=403)
    try:
        stest = StudentTest.objects.get(id=stest_id)
        stest.can_retake = True
        stest.save()
        return JsonResponse({'success': True})
    except StudentTest.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Test topilmadi!'}, status=404)
