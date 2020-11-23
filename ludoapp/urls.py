from django.urls import path
from django.views.generic import TemplateView

from ludoapp import views, auth, events

app_name = 'ludoapp'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('dashboard/', views.DashBoardView.as_view(), name='dashboard'),

    path('register/', auth.RegisterView.as_view(), name='register'),
    path('login/', auth.CustomLoginView.as_view(), name='login'),
    path('send-otp/<slug:reason>/<slug:phonenumber>/', auth.SendOTPView.as_view(), name='send_otp'),
    path('verify-otp/<slug:reason>/<slug:phonenumber>/', auth.OTPValidateView.as_view(), name='verify_otp'),

    path('buy-coins/', views.BuyCoinsView.as_view(), name='buy_coins'),
    path('matches/', views.MatchesListView.as_view(), name='matches'),

    path('cancel/<slug:uuid>/', events.cancel_match, name='cancel_match'),
    path('play/<slug:uuid>/', events.play_match, name='play_match'),

    path('match-screen/<slug:uuid>/', views.GameCodeUpdateView.as_view(), name='match_screen'),

    path('save-game-output/<slug:uuid>/', views.SaveGameOutputView.as_view(), name='save_game_output'),
    path('transactions/', views.TransactionListView.as_view(), name='transactions'),
    path('match-history/', views.MatchHistoryListView.as_view(), name='match_history'),
    path('withdraw-coin/', views.WithdrawCoinCreateView.as_view(), name='withdraw_coin'),

    path('support/', views.SupportCreateView.as_view(), name='support'),
    path('terms-conditions/', views.TermsConditionsView.as_view()),
    path('how-to-play/', TemplateView.as_view(template_name='how-to-play.html'), name='how_to_play'),

    path('forgot-password/', auth.ForgotPasswordView.as_view(), name='forgot_password'),
    path('password-reset/<slug:phone>/<slug:resetuuid>/', auth.PasswordResetView.as_view(), name='password_reset'),
]
