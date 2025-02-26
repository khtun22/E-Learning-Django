from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from datetime import datetime
from .models import *
from .forms import *

from django.contrib import messages

from django.http import JsonResponse
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

            # Get only non-blocked courses
            enrolled_courses = Course.objects.filter(
                course_student__student=profile,
                course_student__blocked=False  # Only show courses where student is not blocked
            )

            taught_courses = None
        elif account_type == 'T':
            profile = Teacher.objects.get(app_user=app_user)
            taught_courses = Course.objects.filter(teacher=profile)
            enrolled_courses = None
        else:
            enrolled_courses = taught_courses = None

        return render(request, 'lms/index.html', {
            'user': user,
            'account_type': account_type,
            'enrolled_courses': enrolled_courses,
            'taught_courses': taught_courses
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
@login_required
def student_profile(request):
    user = request.user
    app_user = AppUser.objects.get(user=user)

    if request.method == 'POST':
        profile = Student.objects.get(app_user=app_user)
        form = StudentForm(request.POST, request.FILES, instance=profile)  # Handle image upload

        if form.is_valid():
            student = form.save(commit=False)
            student.app_user = app_user
            student.last_update = datetime.now()
            student.save()
            return HttpResponseRedirect('/')
    else:
        profile = Student.objects.get(app_user=app_user)
        form = StudentForm(instance=profile)

    return render(request, 'lms/student_profile.html',
                  {'user': user, 'account_type': 'S', 'form': form})
    
# update teacher profile
@login_required
def teacher_profile(request):
    user = request.user
    app_user = AppUser.objects.get(user=user)

    if request.method == 'POST':
        profile = Teacher.objects.get(app_user=app_user)
        form = TeacherForm(request.POST, request.FILES, instance=profile)  # Handle image upload

        if form.is_valid():
            teacher = form.save(commit=False)
            teacher.app_user = app_user
            teacher.last_update = datetime.now()
            teacher.save()
            return HttpResponseRedirect('/')
    else:
        profile = Teacher.objects.get(app_user=app_user)
        form = TeacherForm(instance=profile)

    return render(request, 'lms/teacher_profile.html',
                  {'user': user, 'account_type': 'T', 'form': form})

# chat room selection page
@login_required
def chat(request):
    # get the logged in user
    user = request.user
    app_user = AppUser.objects.get(user=user)
    account_type = app_user.account_type

    # Get the courses enrolled/taught by the user
    # Each course has its own chat room
    if account_type == 'S':
        # list of courses that student has enrolled to
        student = Student.objects.get(app_user=app_user)
        courses = student.course_set.all()
        course_list = courses.values_list('name', flat=True)
            
    if account_type == 'T':
        # list of course that teacher is teaching
        teacher = Teacher.objects.get(app_user=app_user)
        courses = teacher.course_set.all()
        course_list = courses.values_list('name', flat=True)

    # Add a General chat room to the list
    chat_rooms = list(course_list)
    chat_rooms.insert(0, 'General')

    return render(request, 'lms/chat.html',
                  {'user': user, 'account_type': account_type, 'chat_rooms': chat_rooms})

# chat room page
@login_required
def room(request, room_name):
    # get the logged in user
    user = request.user
    app_user = AppUser.objects.get(user=user)
    account_type = app_user.account_type

    return render(request, 'lms/room.html',
                  {'user': user, 'account_type': account_type, 'room_name': room_name })

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
            return HttpResponseRedirect('/')
    else:
        form = CourseForm()

    return render(request, 'lms/create_course.html', {
        'form': form,
        'account_type': 'T'
    })

@login_required
def add_material(request, course_id):
    user = request.user
    app_user = AppUser.objects.get(user=user)

    # Ensure only teachers can upload materials
    if app_user.account_type != 'T':
        return HttpResponseRedirect('/')

    teacher = Teacher.objects.get(app_user=app_user)
    course = Course.objects.get(id=course_id, teacher=teacher)

    if request.method == 'POST':
        form = CourseMaterialForm(request.POST, request.FILES)
        if form.is_valid():
            material = form.save(commit=False)
            material.course = course  # Link the material to the course
            material.title = course.name  # Automatically set title as course name
            material.save()
            return HttpResponseRedirect(f'/add_material/{course.id}/')  # Reload the page
    else:
        form = CourseMaterialForm()

    materials = Course_Material.objects.filter(course=course)

    return render(request, 'lms/add_material.html', {
        'form': form,
        'course': course,
        'materials': materials,
        'account_type': 'T'
    })

@login_required
def course_enrollment(request):
    user = request.user
    app_user = AppUser.objects.get(user=user)

    if app_user.account_type != 'S':
        return HttpResponseRedirect('/')

    student = Student.objects.get(app_user=app_user)

    # Get all courses student is enrolled in
    enrolled_courses = Course_Student.objects.filter(student=student).values_list('course_id', flat=True)
    
    # Get all courses student is blocked from
    blocked_courses = Course_Student.objects.filter(student=student, blocked=True).values_list('course_id', flat=True)

    # Exclude blocked courses from available courses
    available_courses = Course.objects.exclude(id__in=enrolled_courses).exclude(id__in=blocked_courses)

    return render(request, 'lms/course_enrollment.html', {
        'student': student,
        'courses': available_courses
    })



@login_required
def enroll_course(request, course_id):
    user = request.user
    app_user = AppUser.objects.get(user=user)

    if app_user.account_type != 'S':
        return JsonResponse({'error': 'Only students can enroll'}, status=403)

    student = Student.objects.get(app_user=app_user)
    course = Course.objects.get(id=course_id)

    # Check if student is already enrolled
    if Course_Student.objects.filter(course=course, student=student).exists():
        return JsonResponse({'error': 'Already enrolled'}, status=400)

    # Enroll student
    Course_Student.objects.create(course=course, student=student)
    return JsonResponse({'success': 'Enrolled successfully'})

@login_required
def course_materials(request, course_id):
    user = request.user
    app_user = AppUser.objects.get(user=user)

    if app_user.account_type != 'S':
        return HttpResponseRedirect('/')

    student = Student.objects.get(app_user=app_user)
    course = Course.objects.get(id=course_id)

    # Ensure student is enrolled in the course
    enrollment = Course_Student.objects.filter(course=course, student=student).first()
    if not enrollment or enrollment.blocked:
        return HttpResponseRedirect('/')  # Redirect blocked students

    materials = Course_Material.objects.filter(course=course)

    return render(request, 'lms/course_materials.html', {
        'course': course,
        'materials': materials,
        'account_type': 'S'
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

    return render(request, 'lms/course_enrollment_list.html', {
        'course': course,
        'enrolled_students': enrolled_students,
        'blocked_students': blocked_students,  # Pass blocked students separately
        'account_type': 'T'
    })



@login_required
def course_feedback(request, course_id):
    user = request.user
    app_user = AppUser.objects.get(user=user)

    if app_user.account_type != 'S':
        return HttpResponseRedirect('/')

    student = Student.objects.get(app_user=app_user)
    course = Course.objects.get(id=course_id)

    # Ensure student is enrolled in the course
    enrollment = Course_Student.objects.filter(course=course, student=student).first()
    if not enrollment:
        return HttpResponseRedirect('/')

    if request.method == 'POST':
        feedback = request.POST.get('feedback', '')
        enrollment.student_feedback = feedback
        enrollment.save()
        messages.success(request, "Your feedback has been updated successfully!")
        return HttpResponseRedirect(f'/course_feedback/{course.id}/')

    return render(request, 'lms/course_feedback.html', {
        'course': course,
        'existing_feedback': enrollment.student_feedback if enrollment.student_feedback else '',
        'account_type': 'S'
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