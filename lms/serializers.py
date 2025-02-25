from rest_framework import serializers
from .models import *

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'account_type']

class TeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teacher
        fields = '__all__'

class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = '__all__'

class CourseSerializer(serializers.ModelSerializer):
    teacher_name = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ['courseid', 'name', 'description', 'startdate', 'teacher_name']

    def get_teacher_name(self, obj):
        return obj.teacher.display_name

class CourseMaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course_Material
        fields = '__all__'
