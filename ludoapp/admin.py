from django.contrib import admin
from ludoapp import models


@admin.register(models.UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'balance', 'created_on', 'is_available', 'is_verified')


@admin.register(models.Transactions)
class TransactionsAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount',  'mode', 'user_balance', 'transaction_id', 'created_on')


@admin.register(models.MatchModel)
class MatchModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'uuid', 'player1', 'player2', 'bid_amount', 'game_code', 'status', 'winner',
                    'created_on', 'updated_on')

    readonly_fields = ('created_on', 'updated_on')


@admin.register(models.GameOutputModel)
class GameOutputModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'match', 'player', 'user_says', 'created_on', 'screenshot')


@admin.register(models.PhoneOTP)
class PhoneOTPAdmin(admin.ModelAdmin):
    list_display = ('user', 'otp', 'count', 'false_attempts', 'generated_at')


@admin.register(models.SupportModel)
class SupportModelAdmin(admin.ModelAdmin):
    list_display = ('user', 'contact_mobile', 'message', 'attach_screenshot', 'created_at',)


@admin.register(models.WithdrawModel)
class WithdrawModelAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'send_to', 'status', 'created_on', 'transaction_id', 'processed_on',
                    'proof_screenshot', 'reason')


admin.site.register(models.TermsConditionsModel)
