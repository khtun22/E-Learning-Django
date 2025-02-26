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
    path('create_course/', views.create_course, name='create_course'),
    path('add_material/<int:course_id>/', views.add_material, name='add_material'),
    
    path('course_enrollment_list/<int:course_id>/', views.course_enrollment_list, name='course_enrollment_list'),
    path('remove_student/<int:course_id>/<int:student_id>/', views.remove_student, name='remove_student'),
    path('block_student/<int:course_id>/<int:student_id>/', views.block_student, name='block_student'),
    path('unblock_student/<int:course_id>/<int:student_id>/', views.unblock_student, name='unblock_student'),


    path('course_enrollment/', views.course_enrollment, name='course_enrollment'),
    path('enroll_course/<int:course_id>/', views.enroll_course, name='enroll_course'),
    path('course_feedback/<int:course_id>/', views.course_feedback, name='course_feedback'),

    path('course_materials/<int:course_id>/', views.course_materials, name='course_materials'),
    
    path('api/courses/', api.CourseList.as_view(), name='courses_api'),
    path('api/students', api.StudentList.as_view(), name='students_api'),
    path('api/teachers/', api.TeacherList.as_view(), name='teachers_api'),
    path('api/teacher/<int:pk>/', api.TeacherDetails.as_view(), name='teacher_api'),
    path('api/course/<int:pk>/', api.CourseDetails.as_view(), name='course_api'),

    path('chat/', views.chat, name='chat'),
    path('chat/<str:room_name>/', views.room, name='room'),
]

