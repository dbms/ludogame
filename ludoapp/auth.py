import uuid
from random import randint

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.views import LoginView
from django.contrib.auth.models import User
from django.contrib.auth.forms import SetPasswordForm
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.views.generic import View
from django.urls import reverse

from ludoapp.forms import RegisterForm, LoginForm, ValidateOTPForm, ForgotPasswordForm
from ludoapp.models import UserProfile, PhoneOTP
from ludoapp.choices import MAX_OTP_ATTEMPTS, PASSWORD_RESET, USER_VERIFICATION, MAX_OTP_LIMIT


class RegisterView(View):
    form_class = RegisterForm
    template_name = 'registration/register.html'

    def get(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect(reverse('ludoapp:dashboard'))
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            instance = form.save()
            return redirect(reverse('ludoapp:send_otp', args=(USER_VERIFICATION, instance.username,)))

        return render(request, self.template_name, {'form': form})


class CustomLoginView(LoginView):
    form_class = LoginForm
    template_name = 'registration/login.html'

    def get(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect(reverse('ludoapp:dashboard'))

        return super(CustomLoginView, self).get(request, *args, **kwargs)

    def form_valid(self, form):
        try:
            # redirect the user to verify otp page if it is not verified
            user_profile = UserProfile.objects.get(user__username=form.cleaned_data['username'])
            if not user_profile.is_verified:
                return redirect(reverse('ludoapp:send_otp', args=(USER_VERIFICATION, user_profile.user.username,)))

        except User.DoesNotExist:
            pass

        return super(CustomLoginView, self).form_valid(form)


class OTPValidateView(View):
    form_class = ValidateOTPForm
    template_name = 'registration/otp-verification.html'

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            phone_number = self.kwargs.get('phonenumber').strip()
            otp_qs = PhoneOTP.objects.filter(user__username=phone_number).first()
            reason = self.kwargs.get('reason').strip()

            if otp_qs.false_attempts > MAX_OTP_ATTEMPTS:
                messages.error(request, 'You have reached max attempts. Contact Support.')
                return redirect(reverse('ludoapp:login'))

            # OTP mock(xD) any otp entered is a valid OTP
            form.cleaned_data['otp'] = otp_qs.otp

            if reason == USER_VERIFICATION:
                if otp_qs.otp == form.cleaned_data['otp']:
                    # activate the user
                    user = UserProfile.objects.get(user__username=phone_number)
                    user.is_verified = True
                    user.save()

                    otp_qs.false_attempts = 0
                    otp_qs.save()
                    messages.success(request, 'Verification Successful. Login Now')
                    return redirect(reverse('ludoapp:login'))
                else:
                    otp_qs.false_attempts += 1
                    otp_qs.save()

            elif reason == PASSWORD_RESET:
                if otp_qs.otp == form.cleaned_data['otp']:

                    otp_qs.false_attempts = 0
                    otp_qs.save()
                    messages.success(request, 'Reset your password.')
                    return redirect(reverse('ludoapp:password_reset', args=(phone_number, otp_qs.reset_link,)))
                else:
                    otp_qs.false_attempts += 1
                    otp_qs.save()

        messages.error(request, 'Invalid, Try Again')
        return HttpResponseRedirect(self.request.path_info)


class SendOTPView(View):

    def get(self, request, *args, **kwargs):
        phone_number = self.kwargs.get('phonenumber').strip()
        user_otp = PhoneOTP.objects.get(user__username=phone_number)
        reason = self.kwargs.get('reason').strip()

        if reason == USER_VERIFICATION and (
                user_otp.count > MAX_OTP_LIMIT or user_otp.false_attempts > MAX_OTP_ATTEMPTS):
            messages.error(request, 'You have exceeded the OTP limit or Too many false attempts. Contact Support.')
            return redirect(reverse('ludoapp:login'))

        elif reason == PASSWORD_RESET and (
                user_otp.pass_reset_count > MAX_OTP_LIMIT or user_otp.false_attempts > MAX_OTP_ATTEMPTS):
            messages.error(request, 'You have exceeded the OTP limit or Too many false attempts. Contact Support.')
            return redirect(reverse('ludoapp:login'))

        random_key = randint(1000, 9999)
        response = self.send_sms(random_key, phone_number)

        if not response:
            messages.error(request, 'OTP sending Failed. Contact Support')
            return redirect(reverse('ludoapp:login'))

        user_otp.otp = random_key
        if reason == USER_VERIFICATION:
            user_otp.count += 1
        elif reason == PASSWORD_RESET:
            user_otp.pass_reset_count += 1
            user_otp.reset_link = uuid.uuid4()
        user_otp.save()

        return redirect(reverse('ludoapp:verify_otp', args=(reason, phone_number,)))

    @staticmethod
    def send_sms(random_key, phone_number):
        ''' use this method to send OTP. '''

        return True


class ForgotPasswordView(View):
    form_class = ForgotPasswordForm
    template_name = 'registration/forgot-password.html'

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            phone_number = form.cleaned_data['phone_number']
            user = UserProfile.objects.filter(user__username=phone_number)

            if user.exists():
                return redirect(reverse('ludoapp:send_otp', args=(PASSWORD_RESET, phone_number,)))
            else:
                messages.error(request, 'This phone number is not registered with us.')
                return HttpResponseRedirect(self.request.path_info)


class PasswordResetView(View):
    form_class = SetPasswordForm
    template_name = 'registration/reset-password.html'

    def get(self, request, *args, **kwargs):
        form = self.form_class(user=User.objects.get(username=self.kwargs.get('phone')))
        return render(request, self.template_name, {'form': form})

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        form = self.form_class(User.objects.get(username=self.kwargs.get('phone')), request.POST)
        if form.is_valid():
            username = self.kwargs.get('phone')
            reset_link = self.kwargs.get('resetuuid')
            otp_qs = PhoneOTP.objects.get(user__username=username)

            if str(otp_qs.reset_link) == reset_link:
                user = form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Password reset successful.')
                return redirect(reverse('ludoapp:login'))
            else:
                messages.error(request, 'Invalid token, try again.')
                return HttpResponseRedirect(self.request.path_info)

        messages.error(request, 'Invalid, Try Again')
        return HttpResponseRedirect(self.request.path_info)
