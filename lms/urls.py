from django.urls import include, path
from django.contrib.auth.decorators import login_required
from . import api, views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('accounts/login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('student_profile/', views.student_profile, name='student_profile'),
    path('teacher_profile/', views.teacher_profile, name='teacher_profile'),
    path('create_course/', views.create_course, name='create_course'),  # New route

    path('api/courses/', api.CourseList.as_view(), name='courses_api'),
    path('api/students', api.StudentList.as_view(), name='students_api'),
    path('api/teachers/', api.TeacherList.as_view(), name='teachers_api'),
    path('api/teacher/<int:pk>/', api.TeacherDetails.as_view(), name='teacher_api'),
    path('api/course/<int:pk>/', api.CourseDetails.as_view(), name='course_api'),

    path('chat/', views.chat, name='chat'),
    path('chat/<str:room_name>/', views.room, name='room'),
]

