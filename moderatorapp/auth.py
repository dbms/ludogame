from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.urls import reverse

from django.contrib.auth.forms import AuthenticationForm


class CustomLoginView(LoginView):
    form_class = AuthenticationForm
    template_name = 'moderatorapp/login.html'

    def get(self, request, *args, **kwargs):
        if self.request.user.is_authenticated and request.user.groups.filter(name='moderator').exists():
            return redirect(reverse('moderatorapp:dashboard'))

        return super(CustomLoginView, self).get(request, *args, **kwargs)

    def form_valid(self, form):
        try:
            user = User.objects.get(username=form.cleaned_data['username'])

            # check if user is in moderator group
            if not user.groups.filter(name='moderator').exists():
                messages.error(self.request, 'You don\'t have permission to login here.')
                return redirect(reverse('moderatorapp:login'))

            # check if moderator is active
            if not user.is_active:
                messages.error(self.request, 'User In-Active')
                return redirect(reverse('moderatorapp:login'))
        except User.DoesNotExist:
            pass

        return super(CustomLoginView, self).form_valid(form)

    def get_success_url(self):
        return reverse('moderatorapp:login')
