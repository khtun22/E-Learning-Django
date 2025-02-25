from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from datetime import datetime
from .models import *
from .forms import *

# application home page
@login_required
@login_required
def index(request):
    user = request.user

    try:
        app_user = AppUser.objects.get(user=user)
    except AppUser.DoesNotExist:
        app_user = None

    if app_user is not None:
        account_type = app_user.account_type

        # Get user profile
        if account_type == 'S':
            profile = Student.objects.get(app_user=app_user)
            courses = Course.objects.filter(course_student__student=profile)
            course_list = courses.values_list('name', flat=True)

        elif account_type == 'T':
            profile = Teacher.objects.get(app_user=app_user)
            courses = Course.objects.filter(teacher=profile)
            course_list = courses.values_list('name', flat=True)

        # Check if profile is incomplete
        if profile.last_update is None:
            profile_update_message = "Please update your profile."

        else:
            profile_update_message = None

        return render(request, 'lms/index.html', {
            'user': user,
            'account_type': account_type,
            'username': profile.display_name,
            'enrolled_courses': course_list if account_type == 'S' else None,
            'taught_courses': course_list if account_type == 'T' else None,
            'profile_update_message': profile_update_message
        })

    return render(request, 'lms/index.html', {'user': user, 'username': f'{user.first_name} {user.last_name}'})

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

    # Ensure only teachers can create courses
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
        'account_type': 'T'  # Ensure account_type is passed to the template
    })
