from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
import os
from datetime import datetime
from .models import *
from .forms import *
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
from django.db import connection
from django.contrib import messages
from django.conf import settings
from django.core.files.storage import default_storage
# application home page

@login_required
def index(request):
    user = request.user
    try:
        app_user = AppUser.objects.get(user=user)
    except AppUser.DoesNotExist:
        app_user = None

    if app_user is not None:
        account_type = app_user.account_type

        if account_type == 'S':
            profile = Student.objects.get(app_user=app_user)
            display_name = profile.display_name
            enrolled_courses = Course.objects.filter(
                course_student__student=profile,
                course_student__blocked=False
            )

            # Fetch unread notifications for students
            student_unread_notifications = StudentNotification.objects.filter(student=profile, is_read=False)

            taught_courses = None
        elif account_type == 'T':
            profile = Teacher.objects.get(app_user=app_user)
            display_name = profile.display_name
            taught_courses = Course.objects.filter(teacher=profile)
            enrolled_courses = None

            # Fetch unread notifications for teachers
            unread_notifications = Notification.objects.filter(teacher=profile, is_read=False)

        else:
            enrolled_courses = taught_courses = student_unread_notifications = unread_notifications = None

        return render(request, 'lms/index.html', {
            'user': user,
            'display_name': display_name,
            'account_type': account_type,
            'enrolled_courses': enrolled_courses,
            'taught_courses': taught_courses,
            'student_unread_notifications': student_unread_notifications if account_type == 'S' else None,
            'unread_notifications': unread_notifications if account_type == 'T' else None
        })

    return render(request, 'lms/index.html', {'user': user})


# account creation
def register(request):

    registered = False

    if request.method == 'POST':
        # handles request to register user
        user_form = UserForm(data=request.POST)
        role_form = UserRoleForm(data=request.POST)

        if user_form.is_valid() and role_form.is_valid():
            # save the User attributes
            user = user_form.save()
            user.set_password(user.password)
            user.save()

            # save the AppUser attributes
            role = role_form.save(commit=False)
            role.user = user    # link to User
            role.save()

            # create user profie for Teacher/Student
            account_type = role.account_type
            if account_type == 'S':
                student = Student.objects.create(app_user=role,
                                                 display_name=f'{user.first_name} {user.last_name}')
            elif account_type == 'T':
                teacher = Teacher.objects.create(app_user=role,
                                                 display_name=f'{user.first_name} {user.last_name}')

            registered = True
    else:
        # GET: creates empty form
        user_form = UserForm()
        role_form = UserRoleForm()

    return render(request, 'lms/register.html',
                  {'user_form': user_form, 'role_form': role_form,
                    'registered': registered})

# function-based view to create login screen
def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                
                # Redirect to home page instead of profile page
                return HttpResponseRedirect('/')
            else:
                message = 'Account is disabled'
                return render(request, 'lms/login.html', {'message': message})
        else:
            message = 'Invalid login details'
            return render(request, 'lms/login.html', {'message': message})
    else:
        return render(request, 'lms/login.html')


# logout function
@login_required
def user_logout(request):
    logout(request)
    return HttpResponseRedirect('/')

# update student profile
from django.shortcuts import render, redirect
from .models import Student, AppUser, StudentNotification
from .forms import *  # This will now include StudentProfileForm

@login_required
def student_profile(request):
    user = request.user
    app_user = AppUser.objects.get(user=user)

    if app_user.account_type != 'S':
        return redirect('/')

    student = Student.objects.get(app_user=app_user)
    student_unread_notifications = StudentNotification.objects.filter(student=student, is_read=False)

    form = StudentForm(instance=student)  # Ensure this is passed

    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been successfully updated!")
            return redirect('student_profile')

    return render(request, 'lms/student_profile.html', {
        'student': student,
        'form': form,  # Ensure this is included
        'account_type': 'S',
        'student_unread_notifications': student_unread_notifications
    })


    


@login_required
def teacher_profile(request):
    user = request.user
    app_user = AppUser.objects.get(user=user)

    if app_user.account_type != 'T':
        return redirect('/')

    teacher = Teacher.objects.get(app_user=app_user)
    unread_notifications = Notification.objects.filter(teacher=teacher, is_read=False)

    form = TeacherForm(instance=teacher)  # Ensure this is passed

    if request.method == 'POST':
        form = TeacherForm(request.POST, request.FILES, instance=teacher)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been successfully updated!")
            return redirect('teacher_profile')

    return render(request, 'lms/teacher_profile.html', {
        'teacher': teacher,
        'form': form,  # Ensure this is included
        'account_type': 'T',
        'unread_notifications': unread_notifications
    })


# chat room selection page
@login_required
@login_required
def chat(request):
    user = request.user
    app_user = AppUser.objects.get(user=user)
    account_type = app_user.account_type

    student_unread_notifications = []
    unread_notifications = []

    if account_type == 'S':
        student = Student.objects.get(app_user=app_user)
        courses = Course.objects.filter(course_student__student=student)
        course_list = courses.values_list('name', flat=True)

        # Fetch unread notifications for students
        student_unread_notifications = StudentNotification.objects.filter(student=student, is_read=False)

    elif account_type == 'T':
        teacher = Teacher.objects.get(app_user=app_user)
        courses = Course.objects.filter(teacher=teacher)
        course_list = courses.values_list('name', flat=True)

        # Fetch unread notifications for teachers
        unread_notifications = Notification.objects.filter(teacher=teacher, is_read=False)

    else:
        course_list = []

    chat_rooms = list(course_list)
    chat_rooms.insert(0, 'General')

    return render(request, 'lms/chat.html', {
        'user': user,
        'account_type': account_type,
        'chat_rooms': chat_rooms,
        'student_unread_notifications': student_unread_notifications if account_type == 'S' else None,
        'unread_notifications': unread_notifications if account_type == 'T' else None
    })



# chat room page
@login_required
def room(request, room_name):
    user = request.user
    app_user = AppUser.objects.get(user=user)
    account_type = app_user.account_type

    student_unread_notifications = []
    unread_notifications = []

    if account_type == 'S':
        student = Student.objects.get(app_user=app_user)

        # Fetch unread notifications for students
        student_unread_notifications = StudentNotification.objects.filter(student=student, is_read=False)

    elif account_type == 'T':
        teacher = Teacher.objects.get(app_user=app_user)

        # Fetch unread notifications for teachers
        unread_notifications = Notification.objects.filter(teacher=teacher, is_read=False)

    return render(request, 'lms/room.html', {
        'user': user,
        'account_type': account_type,
        'room_name': room_name,
        'student_unread_notifications': student_unread_notifications if account_type == 'S' else None,
        'unread_notifications': unread_notifications if account_type == 'T' else None
    })


@login_required
def create_course(request):
    user = request.user
    app_user = AppUser.objects.get(user=user)
    if app_user.account_type != 'T':
        return HttpResponseRedirect('/')

    teacher = Teacher.objects.get(app_user=app_user)

    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.teacher = teacher
            course.save()
            return redirect('index')
    else:
        form = CourseForm()

    # Pass notifications
    unread_notifications = Notification.objects.filter(teacher=teacher, is_read=False)

    return render(request, 'lms/create_course.html', {
        'form': form,
        'account_type': 'T',
        'unread_notifications': unread_notifications
    })


@login_required
def add_material(request, course_id):
    user = request.user
    app_user = AppUser.objects.get(user=user)

    if app_user.account_type != 'T':
        return HttpResponseRedirect('/')

    teacher = Teacher.objects.get(app_user=app_user)
    course = Course.objects.get(id=course_id, teacher=teacher)

    if request.method == 'POST':
        form = CourseMaterialForm(request.POST, request.FILES)
        if form.is_valid():
            material = form.save(commit=False)
            material.course = course

            if not material.title:
                material.title = f"Material for {course.name} - {teacher.display_name}"

            material.save()

            enrolled_students = Course_Student.objects.filter(course=course)
            channel_layer = get_channel_layer()

            for enrollment in enrolled_students:
                notification = StudentNotification.objects.create(
                    student=enrollment.student,
                    message=f'New material uploaded in "{course.name}" by {teacher.display_name}.'
                )

                async_to_sync(channel_layer.group_send)(
                    f"notifications_student_{enrollment.student.app_user.user.id}",
                    {
                        "type": "send_student_notification",
                        "message": notification.message,
                        "id": notification.id,
                        "url": f"/mark_student_notification_as_read/{notification.id}/"
                    }
                )

            return HttpResponseRedirect(f'/add_material/{course.id}/')

    else:
        form = CourseMaterialForm()

    materials = Course_Material.objects.filter(course=course)
    unread_notifications = Notification.objects.filter(teacher=teacher, is_read=False)

    return render(request, 'lms/add_material.html', {
        'form': form,
        'course': course,
        'materials': materials,
        'account_type': 'T',
        'unread_notifications': unread_notifications
    })

def delete_material(request, material_id):
    if request.method == "POST":
        material = get_object_or_404(Course_Material, id=material_id)

        # Only allow the teacher who uploaded the material to delete it
        if material.course.teacher.app_user.user != request.user:
            return JsonResponse({"success": False, "error": "Unauthorized"}, status=403)

        # Get file path (use `path` instead of `url`)
        file_path = material.file.path  # Absolute path

        # Delete the database record first
        material.delete()

        # Check if file exists and delete it safely
        if file_path and default_storage.exists(file_path):
            try:
                os.remove(file_path)  # Remove the file from the storage
                print(f"Deleted file: {file_path}")  # Debugging log
            except Exception as e:
                print(f"Error deleting file: {e}")  # Log any error

        return JsonResponse({"success": True})

    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)

@login_required
def course_enrollment(request):
    user = request.user
    app_user = AppUser.objects.get(user=user)

    if app_user.account_type != 'S':
        return HttpResponseRedirect('/')

    student = Student.objects.get(app_user=app_user)

    # Get all courses not yet enrolled by the student and not blocked
    enrolled_courses = Course_Student.objects.filter(student=student).values_list('course_id', flat=True)
    blocked_courses = Course_Student.objects.filter(student=student, blocked=True).values_list('course_id', flat=True)
    available_courses = Course.objects.exclude(id__in=enrolled_courses).exclude(id__in=blocked_courses)

    # Fetch unread notifications for students
    student_unread_notifications = StudentNotification.objects.filter(student=student, is_read=False)

    return render(request, 'lms/course_enrollment.html', {
        'student': student,
        'courses': available_courses,
        'account_type': 'S',
        'student_unread_notifications': student_unread_notifications
    })



@login_required
def enroll_course(request, course_id):
    user = request.user
    app_user = AppUser.objects.get(user=user)

    if app_user.account_type != 'S':
        return JsonResponse({'error': 'Only students can enroll'}, status=403)

    student = Student.objects.get(app_user=app_user)
    course = Course.objects.get(id=course_id)

    if Course_Student.objects.filter(course=course, student=student).exists():
        return JsonResponse({'error': 'Already enrolled'}, status=400)

    # Enroll student
    Course_Student.objects.create(course=course, student=student)

    # Create a notification for the teacher
    notification = Notification.objects.create(
        teacher=course.teacher,
        message=f'{student.display_name} has enrolled in your course "{course.name}".'
    )

    # Send real-time WebSocket notification
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"notifications_{course.teacher.app_user.user.id}",
        {"type": "send_notification", "message": notification.message}
    )

    return JsonResponse({'success': 'Enrolled successfully'})


@login_required
def course_materials(request, course_id):
    user = request.user
    app_user = AppUser.objects.get(user=user)

    if app_user.account_type != 'S':
        return HttpResponseRedirect('/')

    student = Student.objects.get(app_user=app_user)
    course = Course.objects.get(id=course_id)

    materials = Course_Material.objects.filter(course=course)
    student_unread_notifications = StudentNotification.objects.filter(student=student, is_read=False)

    return render(request, 'lms/course_materials.html', {
        'course': course,
        'materials': materials,
        'account_type': 'S',
        'student_unread_notifications': student_unread_notifications
    })



@login_required
def course_enrollment_list(request, course_id):
    user = request.user
    app_user = AppUser.objects.get(user=user)

    if app_user.account_type != 'T':
        return HttpResponseRedirect('/')

    teacher = Teacher.objects.get(app_user=app_user)
    course = Course.objects.get(id=course_id, teacher=teacher)

    # Get only non-blocked students enrolled in this course
    enrolled_students = Course_Student.objects.filter(course=course, blocked=False).select_related('student')

    # Get blocked students separately (for unblocking)
    blocked_students = Course_Student.objects.filter(course=course, blocked=True).select_related('student')
    unread_notifications = Notification.objects.filter(teacher=teacher, is_read=False)

    return render(request, 'lms/course_enrollment_list.html', {
        'course': course,
        'enrolled_students': enrolled_students,
        'blocked_students': blocked_students,  # Pass blocked students separately
        'account_type': 'T',
        'unread_notifications': unread_notifications
    })



@login_required
def course_feedback(request, course_id):
    user = request.user
    app_user = AppUser.objects.get(user=user)

    if app_user.account_type != 'S':
        return HttpResponseRedirect('/')

    student = Student.objects.get(app_user=app_user)
    course = Course.objects.get(id=course_id)

    feedback_entry, created = Course_Student.objects.get_or_create(course=course, student=student)
    if request.method == 'POST':
        feedback_entry.student_feedback = request.POST.get('feedback')
        feedback_entry.save()
        return redirect('index')

    student_unread_notifications = StudentNotification.objects.filter(student=student, is_read=False)

    return render(request, 'lms/course_feedback.html', {
        'course': course,
        'feedback': feedback_entry.student_feedback,
        'account_type': 'S',
        'student_unread_notifications': student_unread_notifications
    })




@login_required
def remove_student(request, course_id, student_id):
    user = request.user
    app_user = AppUser.objects.get(user=user)

    if app_user.account_type != 'T':
        return JsonResponse({'error': 'Only teachers can remove students'}, status=403)

    teacher = Teacher.objects.get(app_user=app_user)
    course = Course.objects.get(id=course_id, teacher=teacher)

    try:
        enrollment = Course_Student.objects.get(course=course, student_id=student_id)
        enrollment.delete()
        return JsonResponse({'success': 'Student removed successfully'})
    except Course_Student.DoesNotExist:
        return JsonResponse({'error': 'Student not found in course'}, status=404)


@login_required
def block_student(request, course_id, student_id):
    user = request.user
    app_user = AppUser.objects.get(user=user)

    if app_user.account_type != 'T':
        return JsonResponse({'error': 'Only teachers can block students'}, status=403)

    teacher = Teacher.objects.get(app_user=app_user)
    course = Course.objects.get(id=course_id, teacher=teacher)

    try:
        enrollment, created = Course_Student.objects.get_or_create(course=course, student_id=student_id)
        enrollment.blocked = True  # Mark student as blocked
        enrollment.save()
        return JsonResponse({'success': 'Student blocked successfully'})
    except Course_Student.DoesNotExist:
        return JsonResponse({'error': 'Student not found in course'}, status=404)


@login_required
def unblock_student(request, course_id, student_id):
    user = request.user
    app_user = AppUser.objects.get(user=user)

    if app_user.account_type != 'T':
        return JsonResponse({'error': 'Only teachers can unblock students'}, status=403)

    teacher = Teacher.objects.get(app_user=app_user)
    course = Course.objects.get(id=course_id, teacher=teacher)

    try:
        enrollment = Course_Student.objects.get(course=course, student_id=student_id)
        enrollment.blocked = False  # Unblock student
        enrollment.save()
        return JsonResponse({'success': 'Student unblocked successfully'})
    except Course_Student.DoesNotExist:
        return JsonResponse({'error': 'Student not found in course'}, status=404)

@login_required
def mark_notification_as_read(request, notification_id):
    user = request.user
    app_user = AppUser.objects.get(user=user)

    if app_user.account_type != 'T':
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

    try:
        notification = Notification.objects.get(id=notification_id, teacher__app_user=app_user)
        notification.is_read = True
        notification.save()
    except Notification.DoesNotExist:
        pass  # Ignore errors if notification does not exist

    connection.close()  # Force database connection to close

    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def mark_student_notification_as_read(request, notification_id):
    user = request.user
    app_user = AppUser.objects.get(user=user)

    if app_user.account_type != 'S':
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

    try:
        notification = StudentNotification.objects.get(id=notification_id, student__app_user=app_user)
        notification.is_read = True
        notification.save()
    except StudentNotification.DoesNotExist:
        pass

    connection.close()  # Prevents database lock error
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def search(request):
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('search_type', 'student')  # Default to student
    students = []
    teachers = []
    student_unread_notifications = []
    unread_notifications = []
    account_type = ""

    # Retrieve user and notifications
    app_user = AppUser.objects.get(user=request.user)
    account_type = app_user.account_type
    
    if account_type == 'S':
        student_unread_notifications = StudentNotification.objects.filter(student__app_user=app_user, is_read=False)
    
    if account_type == 'T':
        teacher = Teacher.objects.get(app_user=app_user)
        unread_notifications = Notification.objects.filter(teacher=teacher, is_read=False)

    if search_type == 'student':
        students = Student.objects.all()
        if query:  # Filter by name or status if a search query is entered
            students = students.filter(display_name__icontains=query) | \
                       students.filter(status__icontains=query)

    elif search_type == 'teacher':
        teachers = Teacher.objects.all()
        if query:  # Filter by name or bio if a search query is entered
            teachers = teachers.filter(display_name__icontains=query) | \
                       teachers.filter(bio__icontains=query)

        # Exclude the logged-in teacher from the results
        if account_type == 'T':
            teachers = teachers.exclude(app_user=app_user)

    return render(request, 'lms/search.html', {
        'query': query,
        'search_type': search_type,
        'students': students,
        'teachers': teachers,
        'student_unread_notifications': student_unread_notifications,
        'unread_notifications': unread_notifications,
        'account_type': account_type  # Ensure account type is passed
    })

