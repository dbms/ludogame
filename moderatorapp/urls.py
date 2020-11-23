from django.urls import path
from moderatorapp import auth, views

app_name = 'moderatorapp'

urlpatterns = [
    path('dashboard/', views.DashBoardView.as_view(), name='dashboard'),
    path('login/', auth.CustomLoginView.as_view(), name='login'),
    path('transactions/', views.TransactionListView.as_view(), name='transactions'),

    path('matches/', views.MatchesListView.as_view(), name='matches'),
    path('match/<int:pk>/', views.MatchUpdateView.as_view(), name='match_update'),
    path('match/cancel/<int:pk>/', views.MatchCancelView.as_view(), name='match_cancel'),

    path('support-messages/', views.SupportListView.as_view(), name='support_messages'),
    path('withdraw-requests/', views.WithdrawListView.as_view(), name='withdraw_request'),
    path('process-request/<int:pk>/', views.ProcessRequestView.as_view(), name='process_request'),

]
