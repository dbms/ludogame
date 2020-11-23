import uuid
from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.db.models.signals import post_save
from django.dispatch import receiver
from tinymce.models import HTMLField

from ludoapp.choices import MATCH_STATUSES, GAME_OUTPUTS, TRANSACTION_MODE, WITHDRAW_STATUS, INITIATED


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.IntegerField(null=True, default=0)
    created_on = models.DateTimeField(auto_now_add=True)
    is_available = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.user.first_name

    def full_name(self):
        return f'{self.user.first_name} {self.user.last_name}'


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
        PhoneOTP.objects.create(user=instance)


class PhoneOTP(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=4, null=True)
    count = models.IntegerField(default=0, null=True)
    pass_reset_count = models.IntegerField(default=0, null=True)
    reset_link = models.UUIDField(default=uuid.uuid4, null=True)
    false_attempts = models.IntegerField(default=0, null=True)
    generated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.user.userprofile.full_name())


class Transactions(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    user_balance = models.IntegerField(null=True)
    amount = models.IntegerField(null=True)
    api_response = JSONField(default=dict)
    transaction_id = models.CharField(max_length=50, null=True, unique=True)
    mode = models.CharField(max_length=32, choices=TRANSACTION_MODE, null=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.first_name


class MatchModel(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    player1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='player1')
    player2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='player2', null=True, blank=True)
    bid_amount = models.IntegerField(null=True)
    game_code = models.CharField(max_length=8, null=True)
    status = models.CharField(max_length=20, choices=MATCH_STATUSES, default='open')
    winner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='winner', null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.player1.username

    def player1_name(self):
        if self.player1:
            return self.player1.first_name + " " + self.player1.last_name
        else:
            return ''

    def player2_name(self):
        if self.player2:
            return self.player2.first_name + " " + self.player2.last_name
        else:
            return ''


class GameOutputModel(models.Model):
    match = models.ForeignKey(MatchModel, on_delete=models.CASCADE, null=True)
    player = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    user_says = models.CharField(max_length=20, choices=GAME_OUTPUTS, default='lost')
    created_on = models.DateTimeField(auto_now_add=True)
    screenshot = models.ImageField(upload_to='screenshots', blank=True, null=True)

    def __str__(self):
        return str(self.match.id)


class TermsConditionsModel(models.Model):
    content = HTMLField()


class SupportModel(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    message = models.TextField(null=True)
    contact_mobile = models.CharField(max_length=12, blank=True, null=True)
    attach_screenshot = models.ImageField(upload_to='support_images', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.first_name


class WithdrawModel(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    amount = models.IntegerField(null=True)
    send_to = models.CharField(max_length=10, null=True)
    status = models.CharField(max_length=32, null=True, default=INITIATED, choices=WITHDRAW_STATUS)
    created_on = models.DateTimeField(auto_now_add=True)
    transaction_id = models.CharField(max_length=128, null=True, blank=True)
    processed_on = models.DateTimeField(null=True, blank=True)
    proof_screenshot = models.ImageField(upload_to='proof_images', null=True, blank=True)
    reason = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.user.first_name
