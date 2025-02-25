from django.contrib import admin
from .models import *

admin.site.register(AppUser)
admin.site.register(Teacher)
admin.site.register(Student)
admin.site.register(Course)
admin.site.register(Course_Student)
admin.site.register(Course_Material)