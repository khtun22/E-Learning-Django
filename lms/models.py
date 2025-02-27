from django.db import models
from django.contrib.auth.models import User

class AppUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    ROLE_TYPE = [
        ('T', 'Teacher'),
        ('S', 'Student'),
    ]
    account_type = models.CharField(max_length=1, choices=ROLE_TYPE)

    def __str__(self):
        return self.user.username

class Teacher(models.Model):
    app_user = models.OneToOneField(AppUser, on_delete=models.CASCADE)
    display_name = models.CharField(max_length=30)
    bio = models.TextField()
    last_update = models.DateTimeField(null=True, default=None)
    photo = models.ImageField(upload_to='profile_pics/', null=True, blank=True)  # New field

    def __str__(self):
        return self.display_name

class Student(models.Model):
    app_user = models.OneToOneField(AppUser, on_delete=models.CASCADE)
    display_name = models.CharField(max_length=30)
    last_update = models.DateTimeField(null=True, default=None)
    status = models.TextField(null=True, blank=True)  # New field (similar to bio)
    photo = models.ImageField(upload_to='profile_pics/', null=True, blank=True)  # New field

    def __str__(self):
        return self.display_name

class Course(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(null=True, blank=True)
    startdate = models.CharField(max_length=50, null=True, blank=True)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Course_Student(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    student_feedback = models.TextField(null=True, blank=True)
    blocked = models.BooleanField(default=False)

    def __str__(self):
        return f'[{self.course.name}]-[{self.student.display_name}]'

class Course_Material(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    file = models.FileField(upload_to='course_materials/')  # File upload
    uploaded_at = models.DateTimeField(auto_now_add=True)  # Auto set upload time

    def __str__(self):
        return self.title

class Notification(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Notification for {self.teacher.display_name} - {self.message[:30]}'

class StudentNotification(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Notification for {self.student.display_name} - {self.message[:30]}'
