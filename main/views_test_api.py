from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import Table, TableStyle, SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
# Fan bo'yicha PDF natija yuklash
from django.utils.encoding import smart_str
def export_subject_results_pdf(request, subject_name):
    from datetime import datetime
    tests = StudentTest.objects.filter(test__subject__name=subject_name, completed=True).select_related('student', 'test', 'test__group')
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{smart_str(subject_name)}_test_natijalari.pdf"'

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=20)
    elements = []
    styles = getSampleStyleSheet()
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.lib.styles import ParagraphStyle

    # Custom styles
    title_style = ParagraphStyle('title', parent=styles['Title'], alignment=TA_CENTER, fontSize=16, spaceAfter=8)
    subtitle_style = ParagraphStyle('subtitle', parent=styles['Normal'], alignment=TA_CENTER, fontSize=13, spaceAfter=8)
    normal_style = ParagraphStyle('normal', parent=styles['Normal'], fontSize=11, spaceAfter=4)
    right_style = ParagraphStyle('right', parent=styles['Normal'], alignment=TA_RIGHT, fontSize=11)
    left_style = ParagraphStyle('left', parent=styles['Normal'], alignment=TA_LEFT, fontSize=11)

    # Header (title, date right, subtitle)
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("Samarqand davlat universitetining Kattaqo'rg'on filiali", ParagraphStyle('header', parent=styles['Normal'], alignment=TA_CENTER, fontSize=14, spaceAfter=0, leading=16)))
    test_date = tests.first().test.date.strftime('%d.%m.%Y') if tests and hasattr(tests.first().test, 'date') and tests.first().test.date else datetime.now().strftime('%d.%m.%Y')
    elements.append(Paragraph("Yakuniy nazorat test sinovlari natijalari", ParagraphStyle('subtitle', parent=styles['Normal'], alignment=TA_CENTER, fontSize=12, spaceAfter=2, leading=14)))
    elements.append(Spacer(1, 32))
    elements.append(Paragraph(f"Fanning nomi: {subject_name}", ParagraphStyle('subj', parent=styles['Normal'], fontSize=10, alignment=TA_LEFT)))
    elements.append(Spacer(1, 10))

    # Table header and data
    data = [[
        Paragraph('<b>№</b>', ParagraphStyle('th', alignment=TA_CENTER, fontSize=10)),
        Paragraph('<b>F.I.O</b>', ParagraphStyle('th', alignment=TA_CENTER, fontSize=10)),
        Paragraph('<b>Guruh</b>', ParagraphStyle('th', alignment=TA_CENTER, fontSize=10)),
        Paragraph('<b>Savollar soni</b>', ParagraphStyle('th', alignment=TA_CENTER, fontSize=10)),
        Paragraph('<b>To\'g\'ri javoblar soni</b>', ParagraphStyle('th', alignment=TA_CENTER, fontSize=10)),
        Paragraph('<b>Foizi</b>', ParagraphStyle('th', alignment=TA_CENTER, fontSize=10)),
    ]]
    for idx, stest in enumerate(tests, 1):
        fio = f"{stest.student.last_name.upper()} {stest.student.first_name.upper()} {getattr(stest.student, 'middle_name', '')}".strip()
        group = stest.test.group.name if stest.test.group else "-"
        question_ids = stest.question_ids if stest.question_ids else []
        if question_ids:
            answers = StudentAnswer.objects.filter(student_test=stest, question_id__in=question_ids)
        else:
            answers = StudentAnswer.objects.filter(student_test=stest)
        total = answers.count()
        correct = answers.filter(is_correct=True).count()
        percent = (correct/total)*100 if total else 0
        percent_str = f"{percent:.1f}".replace('.', ',') + "%"
        data.append([
            idx,
            Paragraph(fio, ParagraphStyle('td', alignment=TA_LEFT, fontSize=10)),
            group,
            total,
            correct,
            percent_str
        ])

    # Table column widths (ixcham va bir xil)
    table = Table(data, colWidths=[13*mm, 55*mm, 28*mm, 28*mm, 38*mm, 22*mm])
    table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('FONTSIZE', (0,1), (-1,-1), 10),
        ('ALIGN', (0,0), (0,-1), 'CENTER'),  # №
        ('ALIGN', (1,0), (1,-1), 'LEFT'),    # F.I.O
        ('ALIGN', (2,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LINEBELOW', (0,0), (-1,0), 1, colors.black),
        ('LINEABOVE', (0,0), (-1,0), 1, colors.black),
        ('LINEBEFORE', (0,0), (0,-1), 1, colors.black),
        ('LINEAFTER', (-1,0), (-1,-1), 1, colors.black),
        ('LINEBELOW', (0,-1), (-1,-1), 1, colors.black),
        ('LINEABOVE', (0,1), (-1,1), 0.5, colors.black),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.black),
        ('LEFTPADDING', (0,0), (-1,-1), 3),
        ('RIGHTPADDING', (0,0), (-1,-1), 3),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 10))
    # Test sanasi jadval ostida, o‘ngda
    elements.append(Paragraph(f"Test o'tkazilgan sana: {test_date}", ParagraphStyle('date', parent=styles['Normal'], fontSize=10, alignment=TA_LEFT)))
    elements.append(Spacer(1, 20))

    # Signature block (ikki ustun, pastda, oraliq bilan)
    elements.append(Spacer(1, 20))
    sign_data = [
        ["O‘UBB:", "I.Madatov"],
        ["RTTM xodimi:", "S.Yavkachtiyev"],
        ["RTTM xodimi:", "J.Ixmatullayev"],
    ]
    sign_table = Table(sign_data, colWidths=[95*mm, 95*mm])
    sign_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (0,-1), 'LEFT'),
        ('ALIGN', (1,0), (1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('LEFTPADDING', (0,0), (-1,-1), 2),
        ('RIGHTPADDING', (0,0), (-1,-1), 2),
        ('LINEBELOW', (0,-1), (-1,-1), 0, colors.white),
    ]))
    elements.append(sign_table)

    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response
from django.contrib.auth.decorators import login_required
@login_required
def testapi_logout(request):
    logout(request)
    return redirect('testapi_login')
# Xodimlar natijalarini bo‘lim bo‘yicha eksport
def export_employees_by_bulim_excel(request, bulim_id):
    if not request.user.is_authenticated:
        return redirect('/api/login/')
    from main.models import Bulim
    try:
        bulim = Bulim.objects.get(id=bulim_id)
    except Bulim.DoesNotExist:
        return HttpResponse("Bo'lim topilmadi", status=404)
    employee_users = User.objects.filter(role='employee', bulim=bulim)
    employee_tests = StudentTest.objects.filter(completed=True, student__in=employee_users).select_related('student', 'test', 'test__subject', 'test__group').order_by('student__username', '-start_time')
    wb = Workbook()
    ws = wb.active
    ws.title = f"{bulim.name} - Xodimlar"
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center")
    headers = ["Xodim F.I.Sh.", "Username", "Test", "Fan", "Test sanasi", "Savollar soni", "To'g'ri javob", "Xato javob", "Ball", "Maksimal ball", "Foiz"]
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
    row = 2
    for stest in employee_tests:
        fio = f"{stest.student.first_name} {stest.student.last_name}"
        username = stest.student.username
        test_name = stest.test.subject.name if stest.test.subject else "-"
        subject = stest.test.subject.name if stest.test.subject else "-"
        test_date = stest.start_time.strftime("%d.%m.%Y %H:%M")
        question_ids = stest.question_ids if stest.question_ids else []
        if question_ids:
            answers = StudentAnswer.objects.filter(student_test=stest, question_id__in=question_ids)
        else:
            answers = StudentAnswer.objects.filter(student_test=stest)
        total = answers.count()
        correct = answers.filter(is_correct=True).count()
        incorrect = total - correct
        score = sum([a.score for a in answers])
        percent = int((correct / total) * 100) if total else 0
        data = [fio, username, test_name, subject, test_date, total, correct, incorrect, score, stest.test.total_score, f"{percent}%"]
        for col, value in enumerate(data, 1):
            ws.cell(row=row, column=col, value=value)
        row += 1
    column_widths = [22, 15, 20, 18, 18, 10, 12, 12, 10, 12, 8]
    for col, width in enumerate(column_widths, 1):
        ws.column_dimensions[get_column_letter(col)].width = width
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{bulim.name}_xodimlar_natijalari.xlsx"'
    wb.save(response)
    return response
# Tutorlarnatijalarini kafedra bo‘yicha eksport
def export_tutors_by_kafedra_excel(request, kafedra_id):
    if not request.user.is_authenticated:
        return redirect('/api/login/')
    from main.models import Kafedra
    try:
        kafedra = Kafedra.objects.get(id=kafedra_id)
    except Kafedra.DoesNotExist:
        return HttpResponse("Kafedra topilmadi", status=404)
    tutor_users = User.objects.filter(role='tutor', kafedra=kafedra)
    tutor_tests = StudentTest.objects.filter(completed=True, student__in=tutor_users).select_related('student', 'test', 'test__subject', 'test__group').order_by('student__username', '-start_time')
    wb = Workbook()
    ws = wb.active
    ws.title = f"{kafedra.name} - Tutorlar"
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center")
    headers = ["Tutor F.I.Sh.", "Username", "Test", "Fan", "Test sanasi", "Savollar soni", "To'g'ri javob", "Xato javob", "Ball", "Maksimal ball", "Foiz"]
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
    row = 2
    for stest in tutor_tests:
        fio = f"{stest.student.first_name} {stest.student.last_name}"
        username = stest.student.username
        test_name = stest.test.subject.name if stest.test.subject else "-"
        subject = stest.test.subject.name if stest.test.subject else "-"
        test_date = stest.start_time.strftime("%d.%m.%Y %H:%M")
        question_ids = stest.question_ids if stest.question_ids else []
        if question_ids:
            answers = StudentAnswer.objects.filter(student_test=stest, question_id__in=question_ids)
        else:
            answers = StudentAnswer.objects.filter(student_test=stest)
        total = answers.count()
        correct = answers.filter(is_correct=True).count()
        incorrect = total - correct
        score = sum([a.score for a in answers])
        percent = int((correct / total) * 100) if total else 0
        data = [fio, username, test_name, subject, test_date, total, correct, incorrect, score, stest.test.total_score, f"{percent}%"]
        for col, value in enumerate(data, 1):
            ws.cell(row=row, column=col, value=value)
        row += 1
    column_widths = [22, 15, 20, 18, 18, 10, 12, 12, 10, 12, 8]
    for col, width in enumerate(column_widths, 1):
        ws.column_dimensions[get_column_letter(col)].width = width
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{kafedra.name}_tutorlar_natijalari.xlsx"'
    wb.save(response)
    return response
# Talabalar natijalarini guruh bo‘yicha eksport
def export_students_by_group_excel(request, group_id):
    if not request.user.is_authenticated:
        return redirect('/api/login/')
    from main.models import Group
    try:
        group = Group.objects.get(id=group_id)
    except Group.DoesNotExist:
        return HttpResponse("Guruh topilmadi", status=404)
    student_users = User.objects.filter(role='student', group=group)
    student_tests = StudentTest.objects.filter(completed=True, student__in=student_users).select_related('student', 'test', 'test__subject', 'test__group').order_by('student__username', '-start_time')
    wb = Workbook()
    ws = wb.active
    ws.title = f"{group.name} - Talabalar"
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center")
    headers = ["Talaba F.I.Sh.", "Username", "Test", "Fan", "Test sanasi", "Savollar soni", "To'g'ri javob", "Xato javob", "Ball", "Maksimal ball", "Foiz"]
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
    row = 2
    for stest in student_tests:
        fio = f"{stest.student.first_name} {stest.student.last_name}"
        username = stest.student.username
        test_name = stest.test.subject.name if stest.test.subject else "-"
        subject = stest.test.subject.name if stest.test.subject else "-"
        test_date = stest.start_time.strftime("%d.%m.%Y %H:%M")
        question_ids = stest.question_ids if stest.question_ids else []
        if question_ids:
            answers = StudentAnswer.objects.filter(student_test=stest, question_id__in=question_ids)
        else:
            answers = StudentAnswer.objects.filter(student_test=stest)
        total = answers.count()
        correct = answers.filter(is_correct=True).count()
        incorrect = total - correct
        score = sum([a.score for a in answers])
        percent = int((correct / total) * 100) if total else 0
        data = [fio, username, test_name, subject, test_date, total, correct, incorrect, score, stest.test.total_score, f"{percent}%"]
        for col, value in enumerate(data, 1):
            ws.cell(row=row, column=col, value=value)
        row += 1
    column_widths = [22, 15, 20, 18, 18, 10, 12, 12, 10, 12, 8]
    for col, width in enumerate(column_widths, 1):
        ws.column_dimensions[get_column_letter(col)].width = width
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{group.name}_talabalar_natijalari.xlsx"'
    wb.save(response)
    return response
from django.urls import reverse
# Django templates orqali API test qilish uchun viewlar
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse, HttpResponse
from main.models import Test, Question, AnswerOption, StudentTest, StudentAnswer
from main.models import User
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter
from django.utils import timezone
import io

# Login sahifasi
def testapi_login(request):
    if request.method == 'POST':
        access_code = request.POST.get('access_code')
        from main.models import User
        try:
            user = User.objects.get(access_code=access_code, role='student')
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            return redirect('testapi_dashboard')
        except User.DoesNotExist:
            return render(request, 'test_api/login.html', {'error': 'Access code xato yoki student topilmadi!'})
    return render(request, 'test_api/login.html')

# Dashboard sahifasi
def testapi_dashboard(request):
    if not request.user.is_authenticated:
        return redirect('/api/login/')
    
    now = timezone.now()
    if hasattr(request.user, 'group') and request.user.group:
        # Faqat muddati tugamagan testlar (end_time bo'lmasa, test ko'rinadi)
        tests = Test.objects.filter(group=request.user.group, active=True)
        filtered_tests = []
        for test in tests:
            if test.end_time:
                if now <= test.end_time:
                    filtered_tests.append(test)
            else:
                filtered_tests.append(test)
        tests = filtered_tests
    else:
        tests = []

    # Har bir fan/guruh/semestr uchun faqat eng so‘nggi (yoki eng muhim) test ko‘rsatiladi
    from collections import OrderedDict
    test_map = OrderedDict()  # (subject_id, group_id, semester_id) -> test
    for test in sorted(tests, key=lambda t: t.created_at, reverse=True):
        # Testga bog‘liq semester aniqlash
        from main.models import GroupSubject
        semester_id = None
        gs = GroupSubject.objects.filter(group=test.group, subject=test.subject).first()
        if gs:
            semester_id = gs.semester_id
        key = (test.subject_id, test.group_id, semester_id)
        if key not in test_map:
            test_map[key] = test

    final_tests = list(test_map.values())
    test_statuses = {}
    for test in final_tests:
        # Testga bog‘liq semester aniqlash
        from main.models import GroupSubject
        semester_id = None
        gs = GroupSubject.objects.filter(group=test.group, subject=test.subject).first()
        if gs:
            semester_id = gs.semester_id
        filter_kwargs = dict(
            student=request.user,
            group_id=test.group_id,
            subject_id=test.subject_id,
            completed=True,
            can_retake=False
        )
        if semester_id is not None:
            filter_kwargs['semester_id'] = semester_id
        else:
            filter_kwargs['semester_id__isnull'] = True
        participated = StudentTest.objects.filter(**filter_kwargs).exists()
        if participated:
            test_statuses[test.id] = 'done'
        else:
            test_statuses[test.id] = 'new'

    return render(request, 'test_api/dashboard.html', {'tests': final_tests, 'test_statuses': test_statuses})


# Test savollari va javob berish
def testapi_test(request, test_id):
    if not request.user.is_authenticated:
        return redirect('/api/login/')

    from main.models import TestQuestion, StudentAnswer, StudentTest
    import random
    test = Test.objects.get(id=test_id)
    test_questions = list(TestQuestion.objects.filter(test=test))
    # Talaba shu testda qatnashganmi?
    # Talaba shu testda qatnashganmi? (fan, guruh, semestr bo'yicha faqat 1 marta)
    from main.models import GroupSubject
    group = test.group
    subject = test.subject
    semester = None
    gs = GroupSubject.objects.filter(group=group, subject=subject).first()
    if gs:
        semester = gs.semester
    old_test = StudentTest.objects.filter(
        student=request.user,
        group=group,
        subject=subject,
        semester=semester,
        completed=True,
        can_retake=False
    ).first()
    if old_test:
        return render(request, 'test_api/already_participated.html', {'test': test})
    # Har bir talaba uchun random savollar tanlash (test.question_count ta)
    if not request.session.get(f'test_{test.id}_question_ids'):
        selected_tqs = random.sample(test_questions, min(test.question_count, len(test_questions)))
        question_ids = [tq.question.id for tq in selected_tqs]
        request.session[f'test_{test.id}_question_ids'] = question_ids
    else:
        question_ids = request.session[f'test_{test.id}_question_ids']
        selected_tqs = [tq for tq in test_questions if tq.question.id in question_ids]
    questions = [tq.question for tq in selected_tqs]
    answered_questions = []
    # Matching uchun: har bir matching savol uchun aralashtirilgan right variantlar
    matching_rights_dict = {}
    for q in questions:
        if q.question_type == 'matching':
            rights = [opt for opt in q.answer_options.all() if opt.right or opt.image]
            random.shuffle(rights)
            matching_rights_dict[q.id] = rights

    if request.method == 'POST':
        question_ids = request.session.get(f'test_{test.id}_question_ids', [])
        selected_tqs = [tq for tq in test_questions if tq.question.id in question_ids]
        stest = StudentTest.objects.create(
            student=request.user,
            test=test,
            group=group,
            subject=subject,
            semester=semester,
            question_ids=question_ids
        )
        for q in questions:
            is_correct = False
            score = 0
            tq = next((tq for tq in selected_tqs if tq.question.id == q.id), None)
            if q.question_type == 'single_choice':
                ans_id = request.POST.get(f'question_{q.id}')
                option = AnswerOption.objects.filter(id=ans_id).first()
                sa = StudentAnswer.objects.create(student_test=stest, question=q)
                if option:
                    sa.answer_option.add(option)
                    if option.is_correct:
                        is_correct = True
                        score = tq.score if tq else 0
                sa.is_correct = is_correct
                sa.score = score
                sa.save()
                answered_questions.append(q.id)
            elif q.question_type == 'true_false':
                ans_val = request.POST.get(f'question_{q.id}')
                correct_option = q.answer_options.filter(is_correct=True).first()
                sa = StudentAnswer.objects.create(student_test=stest, question=q, text_answer=ans_val)
                if correct_option and (
                    (ans_val == 'true' and correct_option.text.strip().lower() in ['to‘g‘ri', 'to‘gri', 'true']) or
                    (ans_val == 'false' and correct_option.text.strip().lower() in ['noto‘g‘ri', 'noto‘gri', 'false'])
                ):
                    is_correct = True
                    score = tq.score if tq else 0
                sa.is_correct = is_correct
                sa.score = score
                sa.save()
                answered_questions.append(q.id)
            elif q.question_type == 'multiple_choice':
                selected = [opt for opt in q.answer_options.all() if request.POST.get(f'question_{q.id}_{opt.id}')]
                correct_options = list(q.answer_options.filter(is_correct=True))
                sa = StudentAnswer.objects.create(student_test=stest, question=q)
                for opt in selected:
                    sa.answer_option.add(opt)
                if set(selected) == set(correct_options):
                    is_correct = True
                    score = tq.score if tq else 0
                sa.is_correct = is_correct
                sa.score = score
                sa.save()
                answered_questions.append(q.id)
            elif q.question_type == 'fill_in_blank':
                txt = request.POST.get(f'question_{q.id}', '').strip().lower()
                correct_option = q.answer_options.filter(is_correct=True).first()
                if correct_option and txt == correct_option.text.strip().lower():
                    is_correct = True
                    score = tq.score if tq else 0
                StudentAnswer.objects.create(
                    student_test=stest,
                    question=q,
                    text_answer=txt,
                    is_correct=is_correct,
                    score=score
                )
                answered_questions.append(q.id)
            elif q.question_type == 'matching':
                correct = True
                left_options = [opt for opt in q.answer_options.all() if opt.left]
                for idx, left_opt in enumerate(left_options, 1):
                    selected_right_id = request.POST.get(f'matching_{q.id}_{idx}')
                    if not selected_right_id:
                        correct = False
                    else:
                        right_opt = AnswerOption.objects.filter(id=selected_right_id).first()
                        if not right_opt:
                            correct = False
                        else:
                            # Matnli yoki rasmli javobni tekshirish
                            if left_opt.right and right_opt.right:
                                if left_opt.right != right_opt.right:
                                    correct = False
                            elif left_opt.image and right_opt.image:
                                if left_opt.image.name != right_opt.image.name:
                                    correct = False
                            else:
                                correct = False
                if correct:
                    is_correct = True
                    score = tq.score if tq else 0
                StudentAnswer.objects.create(
                    student_test=stest,
                    question=q,
                    is_correct=is_correct,
                    score=score
                )
                answered_questions.append(q.id)
            elif q.question_type == 'sentence_ordering':
                txt = request.POST.get(f'question_{q.id}', '').strip()
                correct_options = q.answer_options.filter(is_correct=True).order_by('id')
                student_words = [w.strip().lower() for w in txt.split()]
                correct_words = [opt.text.strip().lower() for opt in correct_options]
                if student_words == correct_words:
                    is_correct = True
                    score = tq.score if tq else 0
                StudentAnswer.objects.create(
                    student_test=stest,
                    question=q,
                    text_answer=txt,
                    is_correct=is_correct,
                    score=score
                )
                answered_questions.append(q.id)
        
        # Testni tugallangan deb belgilash
        stest.completed = True
        stest.total_score = sum([a.score for a in StudentAnswer.objects.filter(student_test=stest)])
        stest.save()
        
        return redirect('testapi_result', stest.id)

    else:
        stest = StudentTest.objects.filter(student=request.user, test=test).order_by('-start_time').first()
        if stest:
            answered_questions = list(stest.answers.values_list('question_id', flat=True))
    return render(request, 'test_api/test.html', {
        'test': test,
        'questions': questions,
        'answered_questions': answered_questions,
        'matching_rights_dict': matching_rights_dict,
        'test_minutes': test.minutes
    })



# Natija sahifasi
def testapi_result(request, stest_id):
    if not request.user.is_authenticated:
        return redirect('/api/login/')
    stest = StudentTest.objects.get(id=stest_id)
    
    # StudentTest modelidagi question_ids dan foydalanish
    question_ids = stest.question_ids if stest.question_ids else []
    if not question_ids:
        # Fallback: sessiondan olish
        question_ids = request.session.get(f'test_{stest.test.id}_question_ids', [])
    
    if question_ids:
        answers = StudentAnswer.objects.filter(student_test=stest, question_id__in=question_ids)
    else:
        answers = StudentAnswer.objects.filter(student_test=stest)
    
    total = answers.count()
    correct = answers.filter(is_correct=True).count()
    incorrect = total - correct
    score = sum([a.score for a in answers])
    percent = int((correct / total) * 100) if total else 0
    
    # Har bir javob uchun to'liq ma'lumot tayyorlash
    detailed_answers = []
    for answer in answers:
        question = answer.question
        user_answer = ""
        correct_answer = ""
        
        if question.question_type == 'single_choice':
            if answer.answer_option.exists():
                user_answer = answer.answer_option.first().text
            correct_option = question.answer_options.filter(is_correct=True).first()
            correct_answer = correct_option.text if correct_option else ""
            
        elif question.question_type == 'multiple_choice':
            user_answer = ", ".join([opt.text for opt in answer.answer_option.all()])
            correct_answer = ", ".join([opt.text for opt in question.answer_options.filter(is_correct=True)])
            
        elif question.question_type in ['fill_in_blank', 'true_false', 'sentence_ordering']:
            user_answer = answer.text_answer or ""
            correct_option = question.answer_options.filter(is_correct=True).first()
            correct_answer = correct_option.text if correct_option else ""
            
        elif question.question_type == 'matching':
            user_answer = "Moslashtirish javobi"
            correct_answer = "To'g'ri moslashtirish"
        
        detailed_answers.append({
            'question': question,
            'user_answer': user_answer,
            'correct_answer': correct_answer,
            'is_correct': answer.is_correct,
            'score': answer.score
        })
    
    return render(request, 'test_api/result.html', {
        'stest': stest,
        'total': total,
        'correct': correct,
        'incorrect': incorrect,
        'score': score,
        'percent': percent,
        'answers': answers,
        'detailed_answers': detailed_answers
    })

# Statistik tahlil sahifasi
def testapi_stats(request):
    if not request.user.is_authenticated:
        return redirect('/api/login/')
    stats = {
        'total_tests': Test.objects.count(),
        'total_questions': Question.objects.count(),
        'total_students': User.objects.count(),
        'total_answers': StudentAnswer.objects.count(),
    }
    return render(request, 'test_api/stats.html', {'stats': stats})

# Barcha test natijalarini ko'rish sahifasi (Admin/Controller uchun)
def testapi_all_results(request):
    if not request.user.is_authenticated:
        return redirect('/api/login/')
    
    # Faqat admin va controller ko'ra oladi
    if request.user.role not in ['admin', 'controller']:
        return redirect('testapi_dashboard')
    
    # Barcha tugatilgan testlarni fan va guruh bo'yicha gruppalash
    student_tests = StudentTest.objects.filter(completed=True).select_related(
        'student', 'test', 'test__subject', 'test__group'
    ).order_by('test__subject__name', 'test__group__name', 'student__username', '-start_time')
    
    # Ma'lumotlarni ierarxik tuzish: Fan -> Guruh -> Talaba -> Testlar
    organized_data = {}
    
    for stest in student_tests:
        subject_name = stest.test.subject.name if stest.test.subject else "NOMA'LUM FAN"
        group_name = stest.test.group.name if stest.test.group else "NOMA'LUM GURUH"
        group_id = stest.test.group.id if stest.test.group else 0
        student_username = stest.student.username

        # Fan bo'yicha guruhlashtirish
        if subject_name not in organized_data:
            organized_data[subject_name] = {}

        # Guruh bo'yicha guruhlashtirish
        if group_name not in organized_data[subject_name]:
            organized_data[subject_name][group_name] = {
                'group_id': group_id,
                'students': {}
            }

        # Talaba bo'yicha guruhlashtirish
        if student_username not in organized_data[subject_name][group_name]['students']:
            organized_data[subject_name][group_name]['students'][student_username] = {
                'student': stest.student,
                'tests': []
            }
        
        # Test natijalarini hisoblash
        question_ids = stest.question_ids if stest.question_ids else []
        if question_ids:
            answers = StudentAnswer.objects.filter(student_test=stest, question_id__in=question_ids)
        else:
            answers = StudentAnswer.objects.filter(student_test=stest)
        
        total = answers.count()
        correct = answers.filter(is_correct=True).count()
        incorrect = total - correct
        score = sum([a.score for a in answers])
        percent = int((correct / total) * 100) if total else 0
        
        # Har bir javob uchun batafsil ma'lumot
        answer_details = []
        for answer in answers:
            question = answer.question
            user_answer = ""
            correct_answer = ""
            
            if question.question_type == 'single_choice':
                if answer.answer_option.exists():
                    user_answer = answer.answer_option.first().text
                correct_option = question.answer_options.filter(is_correct=True).first()
                correct_answer = correct_option.text if correct_option else ""
                
            elif question.question_type == 'multiple_choice':
                user_answer = ", ".join([opt.text for opt in answer.answer_option.all()])
                correct_answer = ", ".join([opt.text for opt in question.answer_options.filter(is_correct=True)])
                
            elif question.question_type in ['fill_in_blank', 'true_false', 'sentence_ordering']:
                user_answer = answer.text_answer or ""
                correct_option = question.answer_options.filter(is_correct=True).first()
                correct_answer = correct_option.text if correct_option else ""
                
            elif question.question_type == 'matching':
                user_answer = "Moslashtirish javobi"
                correct_answer = "To'g'ri moslashtirish"
            
            answer_details.append({
                'question': question,
                'user_answer': user_answer,
                'correct_answer': correct_answer,
                'is_correct': answer.is_correct,
                'score': answer.score
            })
        
        # Test ma'lumotlarini qo'shish
        organized_data[subject_name][group_name]['students'][student_username]['tests'].append({
            'student_test': stest,
            'total': total,
            'correct': correct,
            'incorrect': incorrect,
            'score': score,
            'percent': percent,
            'answer_details': answer_details
        })
    
    from main.models import Group, Kafedra, Bulim
    groups_list = Group.objects.all().order_by('name')
    kafedralar_list = Kafedra.objects.all().order_by('name')
    bulimlar_list = Bulim.objects.all().order_by('name')
    return render(request, 'test_api/all_results.html', {
        'organized_data': organized_data,
        'groups_list': groups_list,
        'kafedralar_list': kafedralar_list,
        'bulimlar_list': bulimlar_list
    })

# Universal Excel eksport (rolga mos)
def export_all_results_excel(request):
    if not request.user.is_authenticated:
        return redirect('/api/login/')

    user = request.user
    role = getattr(user, 'role', None)

    # Foydalanuvchi roli bo‘yicha filtr
    if role == 'admin' or role == 'controller':
        student_tests = StudentTest.objects.filter(completed=True).select_related('student', 'test', 'test__subject', 'test__group').order_by('test__subject__name', 'test__group__name', 'student__username', '-start_time')
    elif role == 'employee':
        # Xodim o‘z guruhidagi natijalarni ko‘radi
        if hasattr(user, 'group') and user.group:
            student_tests = StudentTest.objects.filter(completed=True, test__group=user.group).select_related('student', 'test', 'test__subject', 'test__group').order_by('test__subject__name', 'test__group__name', 'student__username', '-start_time')
        else:
            student_tests = StudentTest.objects.none()
    elif role == 'tutor':
        # Tutor o‘z fanidagi natijalarni ko‘radi
        if hasattr(user, 'subject') and user.subject:
            student_tests = StudentTest.objects.filter(completed=True, test__subject=user.subject).select_related('student', 'test', 'test__subject', 'test__group').order_by('test__subject__name', 'test__group__name', 'student__username', '-start_time')
        else:
            student_tests = StudentTest.objects.none()
    else:
        return redirect('testapi_dashboard')

    wb = Workbook()
    ws = wb.active
    ws.title = 'Barcha Natijalar'

    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center")

    headers = [
        "Fan", "Guruh", "Talaba F.I.Sh.", "Username", "Test sanasi",
        "Savollar soni", "To'g'ri javob", "Xato javob", "Ball", "Maksimal ball", "Foiz",
        "Savol", "Talaba javobi", "To'g'ri javob", "Holat", "Ball (savol)"
    ]
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment

    row = 2
    for stest in student_tests:
        subject = stest.test.subject.name if stest.test.subject else "NOMA'LUM FAN"
        group = stest.test.group.name if stest.test.group else "NOMA'LUM GURUH"
        student_fio = f"{stest.student.first_name} {stest.student.last_name}"
        username = stest.student.username
        test_date = stest.start_time.strftime("%d.%m.%Y %H:%M")

        question_ids = stest.question_ids if stest.question_ids else []
        if question_ids:
            answers = StudentAnswer.objects.filter(student_test=stest, question_id__in=question_ids)
        else:
            answers = StudentAnswer.objects.filter(student_test=stest)

        total = answers.count()
        correct = answers.filter(is_correct=True).count()
        incorrect = total - correct
        score = sum([a.score for a in answers])
        percent = int((correct / total) * 100) if total else 0

        if answers.exists():
            for answer in answers:
                question = answer.question
                user_answer = ""
                correct_answer = ""
                if question.question_type == 'single_choice':
                    if answer.answer_option.exists():
                        user_answer = answer.answer_option.first().text
                    correct_option = question.answer_options.filter(is_correct=True).first()
                    correct_answer = correct_option.text if correct_option else ""
                elif question.question_type == 'multiple_choice':
                    user_answer = ", ".join([opt.text for opt in answer.answer_option.all()])
                    correct_answer = ", ".join([opt.text for opt in question.answer_options.filter(is_correct=True)])
                elif question.question_type in ['fill_in_blank', 'true_false', 'sentence_ordering']:
                    user_answer = answer.text_answer or ""
                    correct_option = question.answer_options.filter(is_correct=True).first()
                    correct_answer = correct_option.text if correct_option else ""
                elif question.question_type == 'matching':
                    user_answer = "Moslashtirish javobi"
                    correct_answer = "To'g'ri moslashtirish"
                data = [
                    subject, group, student_fio, username, test_date,
                    total, correct, incorrect, score, stest.test.total_score, f"{percent}%",
                    question.text, user_answer, correct_answer,
                    "To'g'ri" if answer.is_correct else "Xato", answer.score
                ]
                for col, value in enumerate(data, 1):
                    ws.cell(row=row, column=col, value=value)
                row += 1
        else:
            data = [
                subject, group, student_fio, username, test_date,
                0, 0, 0, 0, stest.test.total_score, "0%",
                "Javob berilmagan", "", "", "", 0
            ]
            for col, value in enumerate(data, 1):
                ws.cell(row=row, column=col, value=value)
            row += 1

    column_widths = [20, 18, 22, 15, 18, 10, 12, 12, 10, 12, 8, 40, 30, 30, 10, 8]
    for col, width in enumerate(column_widths, 1):
        ws.column_dimensions[get_column_letter(col)].width = width

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="barcha_natijalar.xlsx"'
    wb.save(response)
    return response

# Excel export funksiyasi
def export_group_results_excel(request, group_id):
    if not request.user.is_authenticated:
        return redirect('/api/login/')
    
    # Ruxsatlarni tekshirish
    from main.models import Group
    user = request.user
    role = getattr(user, 'role', None)
    try:
        group = Group.objects.get(id=group_id)
    except Group.DoesNotExist:
        return HttpResponse("Guruh topilmadi", status=404)

    # Admin va controller istalgan guruhni ko‘ra oladi
    if role in ['admin', 'controller']:
        student_tests = StudentTest.objects.filter(
            completed=True, test__group=group
        ).select_related('student', 'test', 'test__subject').order_by('test__subject__name', 'student__username', '-start_time')
    # Xodim faqat o‘z guruhini ko‘ra oladi
    elif role == 'employee':
        if hasattr(user, 'group') and user.group and user.group.id == group.id:
            student_tests = StudentTest.objects.filter(
                completed=True, test__group=group
            ).select_related('student', 'test', 'test__subject').order_by('test__subject__name', 'student__username', '-start_time')
        else:
            return HttpResponse("Siz faqat o‘z guruhingizni eksport qila olasiz", status=403)
    # Tutor faqat o‘z faniga tegishli guruhlarni ko‘ra oladi
    elif role == 'tutor':
        if hasattr(user, 'subject') and user.subject:
            # Guruhda shu tutor fani bormi?
            has_subject = StudentTest.objects.filter(completed=True, test__group=group, test__subject=user.subject).exists()
            if has_subject:
                student_tests = StudentTest.objects.filter(
                    completed=True, test__group=group, test__subject=user.subject
                ).select_related('student', 'test', 'test__subject').order_by('test__subject__name', 'student__username', '-start_time')
            else:
                return HttpResponse("Bu guruhda sizga tegishli fan natijalari yo‘q", status=403)
        else:
            return HttpResponse("Sizga fan biriktirilmagan", status=403)
    else:
        return redirect('testapi_dashboard')
    
    # Excel fayl yaratish
    wb = Workbook()
    ws = wb.active
    ws.title = f"{group.name} - Test Natijalari"
    
    # Sarlavha stilini yaratish
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center")
    
    # Sarlavhalar
    headers = [
        "Talaba Ismi", "Username", "Fan", "Test Sanasi", 
        "Jami Savollar", "To'g'ri Javoblar", "Xato Javoblar", 
        "Olingan Ball", "Maksimal Ball", "Foiz", "Savol", 
        "Talaba Javobi", "To'g'ri Javob", "Javob Holati", "Ball"
    ]
    
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
    
    # Ma'lumotlarni yozish
    row = 2
    for stest in student_tests:
        # Test natijalarini hisoblash
        question_ids = stest.question_ids if stest.question_ids else []
        if question_ids:
            answers = StudentAnswer.objects.filter(student_test=stest, question_id__in=question_ids)
        else:
            answers = StudentAnswer.objects.filter(student_test=stest)
        
        total = answers.count()
        correct = answers.filter(is_correct=True).count()
        incorrect = total - correct
        score = sum([a.score for a in answers])
        percent = int((correct / total) * 100) if total else 0
        
        # Har bir javob uchun alohida qator
        if answers.exists():
            for answer in answers:
                question = answer.question
                user_answer = ""
                correct_answer = ""
                
                if question.question_type == 'single_choice':
                    if answer.answer_option.exists():
                        user_answer = answer.answer_option.first().text
                    correct_option = question.answer_options.filter(is_correct=True).first()
                    correct_answer = correct_option.text if correct_option else ""
                    
                elif question.question_type == 'multiple_choice':
                    user_answer = ", ".join([opt.text for opt in answer.answer_option.all()])
                    correct_answer = ", ".join([opt.text for opt in question.answer_options.filter(is_correct=True)])
                    
                elif question.question_type in ['fill_in_blank', 'true_false', 'sentence_ordering']:
                    user_answer = answer.text_answer or ""
                    correct_option = question.answer_options.filter(is_correct=True).first()
                    correct_answer = correct_option.text if correct_option else ""
                    
                elif question.question_type == 'matching':
                    user_answer = "Moslashtirish javobi"
                    correct_answer = "To'g'ri moslashtirish"
                
                # Qatorga ma'lumot yozish
                data = [
                    f"{stest.student.first_name} {stest.student.last_name}",
                    stest.student.username,
                    stest.test.subject.name,
                    stest.start_time.strftime("%d.%m.%Y %H:%M"),
                    total,
                    correct,
                    incorrect,
                    score,
                    stest.test.total_score,
                    f"{percent}%",
                    question.text,
                    user_answer,
                    correct_answer,
                    "To'g'ri" if answer.is_correct else "Xato",
                    answer.score
                ]
                
                for col, value in enumerate(data, 1):
                    ws.cell(row=row, column=col, value=value)
                
                row += 1
        else:
            # Agar javob yo'q bo'lsa
            data = [
                f"{stest.student.first_name} {stest.student.last_name}",
                stest.student.username,
                stest.test.subject.name,
                stest.start_time.strftime("%d.%m.%Y %H:%M"),
                0, 0, 0, 0, stest.test.total_score, "0%",
                "Javob berilmagan", "", "", "", 0
            ]
            
            for col, value in enumerate(data, 1):
                ws.cell(row=row, column=col, value=value)
            
            row += 1
    
    # Ustunlar kengligini sozlash
    column_widths = [20, 15, 25, 18, 12, 12, 12, 12, 12, 8, 40, 30, 30, 12, 8]
    for col, width in enumerate(column_widths, 1):
        ws.column_dimensions[get_column_letter(col)].width = width
    
    # HTTP response yaratish
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{group.name}_test_natijalari.xlsx"'
    
    # Excel faylni response ga yozish
    wb.save(response)
    return response
