
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from rest_framework.response import Response
from rest_framework import serializers

# API: Get max question count for a subject
@api_view(['GET'])
@permission_classes([AllowAny])
def subject_max_question_count(request):
    subject_id = request.query_params.get('subject_id')
    if not subject_id:
        return Response({'error': 'subject_id required'}, status=400)
    try:
        from .models import Subject
        subject = Subject.objects.get(id=subject_id)
    except Subject.DoesNotExist:
        return Response({'error': 'Subject not found'}, status=404)
    count = subject.questions.count()
    return Response({'max_question_count': count})
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User

class StudentLoginAPIView(APIView):
    def post(self, request):
        access_code = request.data.get('access_code')
        if not access_code:
            return Response({'detail': 'Access code required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(access_code=access_code, role='student')
        except User.DoesNotExist:
            return Response({'detail': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)
        refresh = RefreshToken.for_user(user)
        return Response({
            'token': str(refresh.access_token)
        }, status=status.HTTP_200_OK)
# Yuqoridagi view’lar bilan birga yangilangan versiya
import csv
from django.http import HttpResponse
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import User, University, Faculty, Group, Subject, Question, AnswerOption, Test, TestQuestion, StudentTest, StudentAnswer, Log
from django.db import models
from .serializers import (
    UserSerializer, UniversitySerializer, FacultySerializer, GroupSerializer, SubjectSerializer,
    QuestionSerializer, AnswerOptionSerializer, TestSerializer, TestQuestionSerializer,
    StudentTestSerializer, StudentAnswerSerializer, LogSerializer
)
from .permissions import IsAdmin, IsTeacher, IsController, IsStudent, HasMultipleRoles

# Mavjud view’lar (qisqartirilgan)
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]

class UniversityViewSet(viewsets.ModelViewSet):
    queryset = University.objects.all()
    serializer_class = UniversitySerializer
    permission_classes = [IsAdmin]

class FacultyViewSet(viewsets.ModelViewSet):
    queryset = Faculty.objects.all()
    serializer_class = FacultySerializer
    permission_classes = [IsAdmin]

class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsAdmin]

class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [HasMultipleRoles(allowed_roles=['teacher', 'controller'])]

    def get_queryset(self):
        queryset = super().get_queryset()
        group_id = self.request.query_params.get('group_id')
        if group_id:
            from main.models import GroupSubject
            subject_ids = GroupSubject.objects.filter(group_id=group_id).values_list('subject_id', flat=True)
            queryset = queryset.filter(id__in=subject_ids)
        return queryset

class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [IsTeacher]

class AnswerOptionViewSet(viewsets.ModelViewSet):
    queryset = AnswerOption.objects.all()
    serializer_class = AnswerOptionSerializer
    permission_classes = [IsTeacher]

class TestViewSet(viewsets.ModelViewSet):
    queryset = Test.objects.all()
    serializer_class = TestSerializer
    permission_classes = [IsController]

    def perform_create(self, serializer):
        test = serializer.save(created_by=self.request.user)
        Log.objects.create(user=self.request.user, action=f"Test yaratildi: {test.subject.name}")

    @action(detail=True, methods=['post'])
    def generate_questions(self, request, pk=None):
        test = self.get_object()
        questions = Question.objects.filter(subject=test.subject)
        if len(questions) < test.question_count:
            return Response({"error": "Yetarli savol mavjud emas"}, status=400)
        
        selected_questions = random.sample(list(questions), test.question_count)
        score_per_question = test.total_score / test.question_count
        
        for question in selected_questions:
            TestQuestion.objects.create(test=test, question=question, score=score_per_question)
        
        Log.objects.create(user=self.request.user, action=f"Test uchun savollar tanlandi: {test.id}")
        return Response({"status": "Savollar tanlandi"})

    @action(detail=True, methods=['get'])
    def export_stats(self, request, pk=None):
        test = self.get_object()
        student_tests = StudentTest.objects.filter(test=test)
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="test_{test.id}_stats.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Talaba', 'To‘g‘ri javoblar', 'Noto‘g‘ri javoblar', 'Umumiy ball', 'Foiz'])
        
        for student_test in student_tests:
            correct_answers = student_test.answers.filter(is_correct=True).count()
            incorrect_answers = student_test.answers.count() - correct_answers
            percentage = (student_test.total_score / test.total_score) * 100 if test.total_score else 0
            writer.writerow([
                student_test.student.username,
                correct_answers,
                incorrect_answers,
                student_test.total_score,
                f"{percentage:.2f}%"
            ])
        
        Log.objects.create(user=self.request.user, action=f"Test statistikasi eksport qilindi: {test.id}")
        return response

class TestQuestionViewSet(viewsets.ModelViewSet):
    queryset = TestQuestion.objects.all()
    serializer_class = TestQuestionSerializer
    permission_classes = [IsController | IsStudent]

class StudentTestViewSet(viewsets.ModelViewSet):
    queryset = StudentTest.objects.all()
    serializer_class = StudentTestSerializer
    permission_classes = [IsStudent]

    def get_queryset(self):
        return StudentTest.objects.filter(student=self.request.user)

    def perform_create(self, serializer):
        test = serializer.validated_data['test']
        group = test.group
        subject = test.subject
        semester = None
        # GroupSubject orqali semestrni aniqlash (agar kerak bo‘lsa)
        from main.models import GroupSubject
        gs = GroupSubject.objects.filter(group=group, subject=subject).first()
        if gs:
            semester = gs.semester
        # Faqat bitta marta topshirish (yakunlanmagan yoki can_retake=False bo‘lsa bloklanadi)
        already = StudentTest.objects.filter(
            student=self.request.user,
            group=group,
            subject=subject,
            semester=semester
        ).filter(
            models.Q(completed=False) | models.Q(completed=True, can_retake=False)
        ).exists()
        if already:
            raise serializers.ValidationError({"error": "Siz bu fanga ushbu semestrda testni allaqachon topshirgansiz yoki yakunlanmagan test mavjud!"})
        # Yangi yozuvga group, subject, semester ni ham saqlaymiz
        student_test = serializer.save(
            student=self.request.user,
            group=group,
            subject=subject,
            semester=semester
        )
        Log.objects.create(user=self.request.user, action=f"Test boshlandi: {student_test.subject.name}")

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        student_test = self.get_object()
        if student_test.completed:
            return Response({"error": "Test allaqachon yakunlangan"}, status=400)
        
        # Vaqtni tekshirish
        if student_test.start_time + student_test.test.duration < timezone.now():
            student_test.completed = True
            student_test.end_time = timezone.now()
            total_score = sum(answer.score for answer in student_test.answers.all())
            student_test.total_score = total_score
            student_test.save()
            Log.objects.create(user=self.request.user, action=f"Test vaqti tugashi bilan yakunlandi: {student_test.test.subject.name}")
            return Response({"error": "Test vaqti tugadi", "total_score": total_score}, status=400)
        
        student_test.completed = True
        student_test.end_time = timezone.now()
        total_score = sum(answer.score for answer in student_test.answers.all())
        student_test.total_score = total_score
        student_test.save()
        
        Log.objects.create(user=self.request.user, action=f"Test yakunlandi: {student_test.test.subject.name}")
        return Response({"status": "Test yakunlandi", "total_score": total_score})

    @action(detail=True, methods=['get'])
    def check_unanswered(self, request, pk=None):
        student_test = self.get_object()
        test_questions = TestQuestion.objects.filter(test=student_test.test)
        answered_questions = student_test.answers.values_list('question_id', flat=True)
        unanswered = test_questions.exclude(question__id__in=answered_questions)
        
        if unanswered.exists():
            return Response({
                "status": "Belgilanmagan savollar mavjud",
                "unanswered_questions": [q.question.id for q in unanswered]
            }, status=200)
        return Response({"status": "Barcha savollar javoblangan"})

    # Yangi: Qolgan vaqtni tekshirish
    @action(detail=True, methods=['get'])
    def check_time(self, request, pk=None):
        student_test = self.get_object()
        if student_test.completed:
            return Response({"error": "Test allaqachon yakunlangan"}, status=400)
        
        time_remaining = student_test.start_time + student_test.test.duration - timezone.now()
        if time_remaining.total_seconds() <= 0:
            student_test.completed = True
            student_test.end_time = timezone.now()
            student_test.total_score = sum(answer.score for answer in student_test.answers.all())
            student_test.save()
            Log.objects.create(user=self.request.user, action=f"Test vaqti tugashi bilan yakunlandi: {student_test.test.subject.name}")
            return Response({"error": "Test vaqti tugadi"}, status=400)
        
        return Response({"time_remaining_seconds": time_remaining.total_seconds()})

class StudentAnswerViewSet(viewsets.ModelViewSet):
    queryset = StudentAnswer.objects.all()
    serializer_class = StudentAnswerSerializer
    permission_classes = [IsStudent]

    def get_queryset(self):
        return StudentAnswer.objects.filter(student_test__student=self.request.user)

    def perform_create(self, serializer):
        student_answer = serializer.save()
        question = student_answer.question
        correct_answers = set(question.answer_options.filter(is_correct=True).values_list('id', flat=True))
        selected_answers = set(student_answer.answer_option.values_list('id', flat=True))
        
        # Maxsus savol turlari uchun logika
        if question.question_type == 'single_choice':
            student_answer.is_correct = selected_answers and (selected_answers.issubset(correct_answers))
        elif question.question_type == 'multiple_choice':
            student_answer.is_correct = selected_answers == correct_answers
        elif question.question_type == 'fill_in_blank':
            student_answer.is_correct = student_answer.text_answer.strip().lower() in [ans.text.strip().lower() for ans in question.answer_options.filter(is_correct=True)]
        elif question.question_type == 'true_false':
            student_answer.is_correct = selected_answers and (selected_answers.issubset(correct_answers))
        elif question.question_type == 'sentence_ordering':
            student_answer.is_correct = student_answer.text_answer == question.answer_options.filter(is_correct=True).first().text
        elif question.question_type == 'matching':
            student_answer.is_correct = student_answer.text_answer == question.answer_options.filter(is_correct=True).first().text
        
        student_answer.score = student_answer.student_test.test.test_questions.get(question=question).score if student_answer.is_correct else 0
        student_answer.save()
        
        Log.objects.create(user=self.request.user, action=f"Javob yuborildi: {question.text[:50]}...")


# Log ViewSet
class LogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Log.objects.all()
    serializer_class = LogSerializer
    permission_classes = [IsAdmin]