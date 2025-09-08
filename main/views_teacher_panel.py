from django.shortcuts import render, redirect, get_object_or_404
from main.models import Subject, Group, Faculty, University, Question, AnswerOption, Semester, GroupSubject
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from django.http import JsonResponse

@require_GET
def get_subjects_by_group_semester(request):
    group_id = request.GET.get('group_id')
    semester_id = request.GET.get('semester_id')
    subjects = []
    if group_id and semester_id:
        group_subjects = GroupSubject.objects.filter(
            group_id=group_id,
            semester_id=semester_id
        ).select_related('subject')
        subjects = [
            {'id': gs.subject.id, 'name': gs.subject.name}
            for gs in group_subjects
        ]
    return JsonResponse({'subjects': subjects})

@login_required
def teacher_logout(request):
    logout(request)
    return redirect('/api/login/')

def login_check(request):
    if not request.user.is_authenticated:
        return redirect('/api/login/')
    return None

# Edit question view (real form)
@login_required
def edit_question(request, question_id):
    login_redirect = login_check(request)
    if login_redirect:
        return login_redirect
    question = get_object_or_404(Question, id=question_id, created_by=request.user)
    faculties = Faculty.objects.all()
    groups = Group.objects.all()
    subjects = Subject.objects.all()
    semesters = Semester.objects.all()
    # 'sentence_ordering' vaqtincha yashiriladi
    question_types = [qt for qt in Question.QUESTION_TYPE_CHOICES if qt[0] != 'sentence_ordering']
    selected = {
        'faculty': getattr(question.subject, 'faculty_id', ''),
        'group': '',
        'semester': getattr(question.subject, 'semester_id', ''),
        'subject': question.subject.id,
        'question_type': question.question_type,
    }
    answer_options = list(question.answer_options.all())
    if request.method == 'POST':
        text = request.POST.get('text')
        subject_id = request.POST.get('subject')
        question_type = request.POST.get('question_type')
        group_id = request.POST.get('group')
        semester = request.POST.get('semester')
        selected = {
            'faculty': request.POST.get('faculty', ''),
            'group': group_id,
            'semester': semester,
            'subject': subject_id,
            'question_type': question_type,
        }
        subject = Subject.objects.get(id=subject_id)
        question.text = text
        question.subject = subject
        question.question_type = question_type
        question.save()
        question.answer_options.all().delete()
        if question_type == 'single_choice':
            for i in range(1, 5):
                option_text = request.POST.get(f'single_option_{i}')
                if option_text:
                    is_correct = (request.POST.get('single_correct') == str(i))
                    AnswerOption.objects.create(question=question, text=option_text, is_correct=is_correct)
        elif question_type == 'multiple_choice':
            for i in range(1, 5):
                option_text = request.POST.get(f'multi_option_{i}')
                if option_text:
                    is_correct = bool(request.POST.get(f'multi_correct_{i}'))
                    AnswerOption.objects.create(question=question, text=option_text, is_correct=is_correct)
        elif question_type == 'fill_in_blank':
            answer = request.POST.get('fill_blank_answer')
            if answer:
                AnswerOption.objects.create(question=question, text=answer, is_correct=True)
        elif question_type == 'true_false':
            answer = request.POST.get('true_false_answer')
            AnswerOption.objects.create(question=question, text=answer, is_correct=(answer == 'true'))
        elif question_type == 'matching':
            i = 1
            while True:
                left = request.POST.get(f'matching_left_{i}')
                right = request.POST.get(f'matching_right_{i}')
                if left or right:
                    if left and right:
                        AnswerOption.objects.create(question=question, left=left, right=right, is_correct=True)
                    i += 1
                else:
                    break
        elif question_type == 'sentence_ordering':
            for i in range(1, 5):
                order_text = request.POST.get(f'ordering_{i}')
                if order_text:
                    AnswerOption.objects.create(question=question, text=order_text, is_correct=True)
        return redirect('teacher_dashboard')
    return render(request, 'teacher_panel/add_question.html', {
        'subjects': subjects,
        'faculties': faculties,
        'groups': groups,
        'semesters': semesters,
        'question_types': question_types,
        'selected': selected,
        'edit_mode': True,
        'question': question,
        'answer_options': answer_options,
    })

# Delete question view
@login_required
def delete_question(request, question_id):
    login_redirect = login_check(request)
    if login_redirect:
        return login_redirect
    question = get_object_or_404(Question, id=question_id, created_by=request.user)
    question.delete()
    return redirect('teacher_dashboard')

@login_required
def teacher_dashboard(request):
    login_redirect = login_check(request)
    if login_redirect:
        return login_redirect
    if not hasattr(request.user, 'role') or request.user.role != 'teacher':
        return redirect('/api/login/')
    subjects = Subject.objects.all()
    questions = Question.objects.filter(created_by=request.user)
    return render(request, 'teacher_panel/dashboard.html', {'subjects': subjects, 'questions': questions})


from main.models import Kafedra, Bulim

@login_required
def add_question(request):
    login_redirect = login_check(request)
    if login_redirect:
        return login_redirect
    if not hasattr(request.user, 'role') or request.user.role != 'teacher':
        return redirect('/api/login/')

    target = request.GET.get('target', 'student')
    context = {'question_types': [qt for qt in Question.QUESTION_TYPE_CHOICES if qt[0] != 'sentence_ordering'], 'selected': {}}

    if target == 'student':
        context['faculties'] = Faculty.objects.all()
        context['groups'] = Group.objects.all()
        context['semesters'] = Semester.objects.all()
        group_id = request.GET.get('group') or request.POST.get('group')
        semester_id = request.GET.get('semester') or request.POST.get('semester')
        if group_id and semester_id:
            from main.models import GroupSubject
            group_subjects = GroupSubject.objects.filter(group_id=group_id, semester_id=semester_id)
            context['subjects'] = Subject.objects.filter(id__in=group_subjects.values_list('subject_id', flat=True))
        else:
            context['subjects'] = Subject.objects.none()
        context['target'] = 'student'
    elif target == 'tutor':
        context['kafedralar'] = Kafedra.objects.all()
        context['subjects'] = Subject.objects.all()
        context['target'] = 'tutor'
    elif target == 'employee':
        context['bulimlar'] = Bulim.objects.all()
        context['subjects'] = Subject.objects.all()
        context['target'] = 'employee'
    else:
        # Default to student if unknown
        context['faculties'] = Faculty.objects.all()
        context['groups'] = Group.objects.all()
        context['semesters'] = Semester.objects.all()
        context['subjects'] = Subject.objects.all()
        context['target'] = 'student'

    if request.method == 'POST':
        text = request.POST.get('text')
        subject_id = request.POST.get('subject')
        question_type = request.POST.get('question_type')
        context['selected'] = {'subject': subject_id, 'question_type': question_type}
        error = None

        if target == 'student':
            faculty_id = request.POST.get('faculty')
            group_id = request.POST.get('group')
            semester_id = request.POST.get('semester')
            context['selected'].update({'faculty': faculty_id, 'group': group_id, 'semester': semester_id})
            if not (faculty_id and group_id and semester_id):
                error = "Fakultet, guruh va semestrni tanlang!"
        elif target == 'tutor':
            kafedra_id = request.POST.get('kafedra')
            context['selected'].update({'kafedra': kafedra_id})
            if not kafedra_id:
                error = "Kafedrani tanlang!"
        elif target == 'employee':
            bulim_id = request.POST.get('bulim')
            context['selected'].update({'bulim': bulim_id})
            if not bulim_id:
                error = "Bo'limni tanlang!"

        if not text or not subject_id or not question_type:
            error = "Barcha maydonlarni to‘ldiring!"

        if error:
            context['error'] = error
            return render(request, 'teacher_panel/add_question.html', context)

        subject = Subject.objects.get(id=subject_id)
        q = Question.objects.create(text=text, subject=subject, question_type=question_type, created_by=request.user)
        # Javob variantlari logikasi (o'zgartirilmagan)
        if question_type == 'single_choice':
            for i in range(1, 5):
                option_text = request.POST.get(f'single_option_{i}')
                if option_text:
                    is_correct = (request.POST.get('single_correct') == str(i))
                    AnswerOption.objects.create(question=q, text=option_text, is_correct=is_correct)
        elif question_type == 'multiple_choice':
            for i in range(1, 5):
                option_text = request.POST.get(f'multi_option_{i}')
                if option_text:
                    is_correct = bool(request.POST.get(f'multi_correct_{i}'))
                    AnswerOption.objects.create(question=q, text=option_text, is_correct=is_correct)
        elif question_type == 'fill_in_blank':
            answer = request.POST.get('fill_blank_answer')
            if answer:
                AnswerOption.objects.create(question=q, text=answer, is_correct=True)
        elif question_type == 'true_false':
            answer = request.POST.get('true_false_answer')
            AnswerOption.objects.create(question=q, text=answer, is_correct=(answer == 'true'))
        elif question_type == 'matching':
            i = 1
            while True:
                left = request.POST.get(f'matching_left_{i}')
                right = request.POST.get(f'matching_right_{i}')
                image = request.FILES.get(f'matching_image_{i}')
                if left or right or image:
                    AnswerOption.objects.create(
                        question=q,
                        left=left or '',
                        right=right or '',
                        image=image if image else None,
                        is_correct=True
                    )
                    i += 1
                else:
                    break
        elif question_type == 'sentence_ordering':
            for i in range(1, 5):
                order_text = request.POST.get(f'ordering_{i}')
                if order_text:
                    AnswerOption.objects.create(question=q, text=order_text, is_correct=True)
        return render(request, 'teacher_panel/add_question.html', context)
    return render(request, 'teacher_panel/add_question.html', context)
