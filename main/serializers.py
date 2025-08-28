from rest_framework import serializers
from .models import User, University, Faculty, Group, Subject, Question, AnswerOption, Test, TestQuestion, StudentTest, StudentAnswer, Log

# Foydalanuvchi seriyalizatori
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'role', 'access_code']
        read_only_fields = ['access_code']  # Access_code faqat admin ko‘radi

# Universitet seriyalizatori
class UniversitySerializer(serializers.ModelSerializer):
    class Meta:
        model = University
        fields = ['id', 'name', 'created_at']

# Fakultet seriyalizatori
class FacultySerializer(serializers.ModelSerializer):
    class Meta:
        model = Faculty
        fields = ['id', 'university', 'name', 'created_at']

# Guruh seriyalizatori
class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'faculty', 'name', 'created_at']

# Fan seriyalizatori
class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ['id', 'name', 'group', 'teacher', 'semester', 'created_at']

# Javob varianti seriyalizatori
class AnswerOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerOption
        fields = ['id', 'text', 'is_correct']

# Savol seriyalizatori
class QuestionSerializer(serializers.ModelSerializer):
    answer_options = AnswerOptionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Question
        fields = ['id', 'subject', 'text', 'question_type', 'image', 'answer_options', 'created_at', 'updated_at']

# Test seriyalizatori
class TestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Test
        fields = ['id', 'subject', 'question_count', 'total_score', 'duration', 'created_at']

# Test savoli seriyalizatori
class TestQuestionSerializer(serializers.ModelSerializer):
    question = QuestionSerializer(read_only=True)
    
    class Meta:
        model = TestQuestion
        fields = ['id', 'test', 'question', 'score']

# Talaba javobi seriyalizatori
class StudentAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentAnswer
        fields = ['question', 'answer_option', 'text_answer', 'is_correct', 'score']

# Talaba testi seriyalizatori
class StudentTestSerializer(serializers.ModelSerializer):
    answers = StudentAnswerSerializer(many=True, read_only=True)
    
    class Meta:
        model = StudentTest
        fields = [
            'id', 'test', 'group', 'subject', 'semester',
            'start_time', 'end_time', 'total_score', 'completed', 'can_retake', 'answers'
        ]

# Log seriyalizatori
class LogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Log
        fields = ['id', 'user', 'action', 'created_at']