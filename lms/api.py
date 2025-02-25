from rest_framework import generics
from .models import *
from .serializers import *
from .permissions import IsTeacherOwner, IsCourseOwner

# List all courses
class CourseList(generics.ListAPIView):
    queryset = Course.objects.all()
    # set serializer_class to the serializer for the object
    serializer_class = CourseSerializer

# List all students
class StudentList(generics.ListAPIView):
    queryset = Student.objects.all()
    # set serializer_class to the serializer for the object
    serializer_class = StudentSerializer

# List all teacher
class TeacherList(generics.ListAPIView): 
    # set queryset to the list of objects to return
    queryset = Teacher.objects.all()
    # set serializer_class to the serializer for the object
    serializer_class = TeacherSerializer

# Implements Read, Update, Delete operations for a specific teacher
# The GenericAPIView expects the id for the object to be 'pk'
# by default. This can be changed by setting lookup_field
class TeacherDetails(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsTeacherOwner]

    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer
    # default is 'pk' so this attribute is optional
    lookup_field = 'pk'


class CourseDetails(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsCourseOwner]
    
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    # default is 'pk' so this attribute is optional
    lookup_field = 'pk'
