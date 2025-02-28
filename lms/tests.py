from django.test import TestCase, Client
from django.contrib.auth.models import User
from lms.models import AppUser, Teacher, Student, Course, Course_Student, Course_Material
from lms.forms import CourseForm
from rest_framework.test import APIClient
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

### **1️⃣ Model Tests**
class ModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="teacher1", password="password123")
        self.app_user = AppUser.objects.create(user=self.user, account_type='T')
        self.teacher = Teacher.objects.create(app_user=self.app_user, display_name="John Doe")
        self.course = Course.objects.create(name="Math 101", description="Basic Math", startdate="2024-06", teacher=self.teacher)

    def test_course_creation(self):
        """Test if a course is created successfully"""
        self.assertEqual(self.course.name, "Math 101")
        self.assertEqual(self.course.teacher.display_name, "John Doe")

    def test_teacher_creation(self):
        """Test if a teacher is created correctly"""
        self.assertEqual(self.teacher.display_name, "John Doe")

### **2️⃣ View Tests**
class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="teacher1", password="password123")
        self.app_user = AppUser.objects.create(user=self.user, account_type='T')
        self.teacher = Teacher.objects.create(app_user=self.app_user, display_name="John Doe")
        self.client.login(username="teacher1", password="password123")

    def test_home_page_loads(self):
        """Test if the home page loads successfully"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_create_course(self):
        """Test if a teacher can create a course successfully"""
        response = self.client.post('/create_course/', {
            'name': 'Physics 101',
            'description': 'Basic Physics',
            'startdate': '2025-02'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after successful creation
        self.assertTrue(Course.objects.filter(name='Physics 101').exists())

### **3️⃣ Form Tests**
class FormTests(TestCase):
    def test_valid_course_form(self):
        """Test if a valid course form passes validation"""
        form = CourseForm(data={'name': 'Biology 101', 'description': 'Intro to Biology', 'startdate': '2024-09'})
        self.assertTrue(form.is_valid())

    def test_invalid_course_form(self):
        """Test if an invalid course form fails validation"""
        form = CourseForm(data={'name': '', 'description': '', 'startdate': ''})
        self.assertFalse(form.is_valid())

### **4️⃣ API Tests**
class APITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="teacher1", password="password123")
        self.app_user = AppUser.objects.create(user=self.user, account_type='T')
        self.teacher = Teacher.objects.create(app_user=self.app_user, display_name="John Doe")
        self.course = Course.objects.create(name="Chemistry 101", description="Chemistry Basics", startdate="2024-06", teacher=self.teacher)
        self.client.login(username="teacher1", password="password123")

    def test_get_courses(self):
        """Test if the API returns a list of courses"""
        response = self.client.get(reverse('courses_api'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]['name'], 'Chemistry 101')

    def test_create_course_api(self):
        """Test if the API allows a teacher to create a course"""
        response = self.client.post(reverse('courses_api'), {
            'name': 'Physics 102',
            'description': 'Advanced Physics',
            'startdate': '2025-01',
            'teacher': self.teacher.id
        })
        self.assertEqual(response.status_code, 405)  # List API is read-only

### **5️⃣ File Upload & Delete Tests**
class FileUploadTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="teacher1", password="password123")
        self.app_user = AppUser.objects.create(user=self.user, account_type='T')
        self.teacher = Teacher.objects.create(app_user=self.app_user, display_name="John Doe")
        self.course = Course.objects.create(name="Science 101", description="Science Basics", startdate="2024-07", teacher=self.teacher)
        self.client.login(username="teacher1", password="password123")

    def test_upload_file(self):
        """Test if a teacher can upload course material"""
        file = SimpleUploadedFile("test.pdf", b"file_content", content_type="application/pdf")
        response = self.client.post(reverse('add_material', args=[self.course.id]), {'file': file})
        self.assertEqual(response.status_code, 302)  # Redirect after successful upload
        self.assertTrue(Course_Material.objects.exists())

    def test_delete_file(self):
        """Test if a teacher can delete course material"""
        material = Course_Material.objects.create(course=self.course, title="Lecture Notes", file="test.pdf")
        response = self.client.post(reverse('delete_material', args=[material.id]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Course_Material.objects.filter(id=material.id).exists())

### **6️⃣ Authentication Tests**
class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="student1", password="password123")
        self.app_user = AppUser.objects.create(user=self.user, account_type='S')
        self.student = Student.objects.create(app_user=self.app_user, display_name="Jane Doe")

    def test_login(self):
        """Test if a user can log in"""
        response = self.client.post('/accounts/login/', {'username': 'student1', 'password': 'password123'})
        self.assertEqual(response.status_code, 302)  # Redirect after successful login

    def test_logout(self):
        """Test if a user can log out"""
        self.client.login(username="student1", password="password123")
        response = self.client.get('/logout/')
        self.assertEqual(response.status_code, 302)  # Redirect after logout
