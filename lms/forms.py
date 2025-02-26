from django import forms
from django.contrib.auth.models import User
from .models import *

class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ['username', 'password', 'first_name', 'last_name', 'email']

class UserRoleForm(forms.ModelForm):
    class Meta:
        model = AppUser
        fields = ['account_type']

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['display_name', 'status', 'photo']  # Added status & photo fields

class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = ['display_name', 'bio', 'photo']  # Added photo field


class CourseForm(forms.ModelForm):
    startdate = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Feb -2024 to Oct -2024'}),
        required=False
    )

    class Meta:
        model = Course
        fields = ['name', 'description', 'startdate']

class CourseMaterialForm(forms.ModelForm):
    class Meta:
        model = Course_Material
        fields = ['file']





