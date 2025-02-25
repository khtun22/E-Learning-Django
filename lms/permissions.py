from rest_framework import permissions

# Custom permissions are defined here

# A teacher object can only be viewed and modified by the teacher or Admin 
class IsTeacherOwner(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        # creator_permission is True if object belongs to current user
        creator_permission = bool(obj.app_user.user == request.user)

        # admin_permission is True if current user is Administrator
        admin_permission = request.user.is_staff

        return creator_permission or admin_permission
    
# A course object can be viewed by any authenticated user but can only be modified by the
# teacher who owns the course
class IsCourseOwner(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):

        if request.method in permissions.SAFE_METHODS:
            # Check permissions for read-only request
            return True
        else:
            # Check permissions for write request
            creator_permission = bool(obj.teacher.app_user.user == request.user)
            return creator_permission