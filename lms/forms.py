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
    startdate = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        input_formats=['%Y-%m-%d']
    )

    class Meta:
        model = Course
        fields = ['name', 'description', 'startdate']




