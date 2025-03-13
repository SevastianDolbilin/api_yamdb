from rest_framework import permissions


class IsAnonymous(permissions.BasePermission):
    """Разрешение, позволяющее просматривать
    данные анонимному пользователю.
    """

    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS


class IsAuthor(permissions.BasePermission):
    """Разрешение, позволяющее взаимодействовать с данными автору.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return getattr(obj, 'author', None) == request.user


class IsModerator(permissions.BasePermission):
    """Разрешение, позволяющее взаимодействовать с данными
    модератеру.
    """

    def has_object_permission(self, request, view, obj):
        return (
            request.user.is_authenticated
            and request.user.is_moderator
        )


class IsSuperUserOrIsAdmin(permissions.BasePermission):
    """Разрешение, дающее полные права для взаимодействия с контентом.
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and (
                request.user.is_admin
                or request.user.is_superuser
                or request.user.is_staff
            )
        )

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)
