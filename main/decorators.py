from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from ludoapp.models import UserProfile


class ModeratorRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        is_moderator = self.request.user.groups.filter(name='moderator').exists()
        is_active = self.request.user.is_active
        return is_moderator and is_active


class RegularUserRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return is_regular_user(self.request)


def regular_user_required(function):
    def wrap(request, *args, **kwargs):
        if request.user.is_authenticated and is_regular_user(request):
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied

    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


def is_regular_user(request):
    is_verified = UserProfile.objects.get(user=request.user).is_verified
    is_moderator = request.user.groups.filter(name='moderator').exists()
    is_superuser = request.user.is_superuser or request.user.is_staff
    is_active = request.user.is_active

    return not is_moderator and is_active and is_verified and not is_superuser
