import datetime

from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic.base import TemplateView
from django.views import generic

from ludoapp.choices import INPROGRESS, INITIATED, PROCESSED, CANCELLED
from ludoapp.match import MatchOperations, WithdrawOperations
from ludoapp.models import Transactions, MatchModel, GameOutputModel, SupportModel, WithdrawModel
from main.decorators import ModeratorRequiredMixin
from moderatorapp.forms import MatchForm, WithdrawForm


class DashBoardView(ModeratorRequiredMixin, TemplateView):
    template_name = 'moderatorapp/dashboard.html'

    def get_context_data(self, **kwargs):
        valor = self.request.GET.get('number')
        return super().get_context_data(**kwargs)


class MatchesListView(generic.ListView):
    template_name = 'moderatorapp/matches.html'
    model = MatchModel
    paginate_by = 10
    context_object_name = 'matches'
    ordering = ['-created_on']

    def get_queryset(self):
        qs = MatchModel.objects.all().order_by('-id')

        first_name = self.request.GET.get('first_name', '')
        last_name = self.request.GET.get('last_name', '')
        phone = self.request.GET.get('phone', '')
        last_days = self.request.GET.get('days', '')
        game_code = self.request.GET.get('game_code', '')
        match_status = self.request.GET.get('match_status', '')

        if first_name:
            qs = qs.filter(Q(player1__first_name__icontains=first_name) |
                           Q(player2__first_name__icontains=first_name))
        if last_name:
            qs = qs.filter(Q(player1__last_name__icontains=last_name) |
                           Q(player2__last_name__icontains=last_name))
        if phone:
            qs = qs.filter(Q(player1__username__icontains=phone) |
                           Q(player2__username__icontains=phone))
        if last_days:
            qs = qs.filter(created_on__gte=datetime.datetime.today() - datetime.timedelta(days=int(last_days)))

        if game_code:
            qs = qs.filter(game_code__icontains=game_code)

        if match_status:
            qs = qs.filter(status__icontains=match_status)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        fields = ['first_name', 'last_name', 'phone', 'days', 'game_code', 'match_status']

        # return field value as it is
        for field in fields:
            context[field] = self.request.GET.get(field, '')

        return context


class TransactionListView(ModeratorRequiredMixin, generic.ListView):
    template_name = 'moderatorapp/transactions.html'
    model = Transactions
    paginate_by = 10
    context_object_name = 'transactions'
    ordering = ['-created_on']

    def get_queryset(self):
        qs = Transactions.objects.all().order_by('-id')

        first_name = self.request.GET.get('first_name', '')
        last_name = self.request.GET.get('last_name', '')
        phone = self.request.GET.get('phone', '')
        last_days = self.request.GET.get('days', '')
        mode = self.request.GET.get('mode', '')

        if first_name:
            qs = qs.filter(user__first_name__icontains=first_name)
        if last_name:
            qs = qs.filter(user__last_name__icontains=last_name)
        if phone:
            qs = qs.filter(user__username__icontains=phone)
        if last_days:
            qs = qs.filter(created_on__gte=datetime.datetime.today() - datetime.timedelta(days=int(last_days)))
        if mode:
            qs = qs.filter(mode__icontains=mode)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        fields = ['first_name', 'last_name', 'phone', 'days', 'mode']
        # return field value as it is
        for field in fields:
            context[field] = self.request.GET.get(field, '')

        return context


class MatchUpdateView(ModeratorRequiredMixin, generic.UpdateView):
    model = MatchModel
    form_class = MatchForm
    template_name = 'moderatorapp/match-result.html'

    @transaction.atomic
    def form_valid(self, form):
        match = self.get_object()

        if match.status != INPROGRESS:
            messages.error(self.request, 'Result of this match has been decided already.')
            return redirect(reverse('moderatorapp:matches'))

        form.save()
        mo_obj = MatchOperations(match)
        mo_obj.decided_match_winner_by_moderator(form.cleaned_data['winner'])
        messages.success(self.request, 'Game result updated.')
        return redirect(reverse('moderatorapp:matches'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        match = MatchModel.objects.get(id=self.kwargs.get('pk'))

        context['match'] = match
        context['game_outputs'] = GameOutputModel.objects.filter(match=match)

        return context


class SupportListView(ModeratorRequiredMixin, generic.ListView):
    template_name = 'moderatorapp/support-messages.html'
    model = SupportModel
    context_object_name = 'messages'
    paginate_by = 10
    ordering = ['-created_at']


class WithdrawListView(ModeratorRequiredMixin, generic.ListView):
    template_name = 'moderatorapp/withdraw-requests.html'
    model = WithdrawModel
    context_object_name = 'withdraw_requests'
    paginate_by = 10
    ordering = ['-created_on']


class ProcessRequestView(ModeratorRequiredMixin, generic.UpdateView):
    model = WithdrawModel
    form_class = WithdrawForm
    template_name = 'moderatorapp/process-request.html'

    @transaction.atomic
    def form_valid(self, form):
        withdraw_model_obj = self.get_object()
        if withdraw_model_obj.status != INITIATED:
            messages.error(self.request, 'This request has been already processed.')
            return redirect(reverse('moderatorapp:withdraw_request'))

        if form.cleaned_data['status'] == INITIATED:
            messages.error(self.request, 'Request is already in initiated state.')
            return redirect(reverse('moderatorapp:process_request', args=(self.get_object().id,)))

        saved_instance = form.save(commit=False)
        saved_instance.processed_on = timezone.make_aware(datetime.datetime.now(), timezone.get_default_timezone())
        saved_instance.save()

        wo_obj = WithdrawOperations(withdraw_model_obj.user)
        if form.cleaned_data['status'] == PROCESSED:
            wo_obj.process_request(withdraw_model_obj)

        wo_obj.withdraw_state_changed(form.cleaned_data['status'])

        messages.success(self.request, 'Successfully Saved.')
        return redirect(reverse('moderatorapp:withdraw_request'))


class MatchCancelView(ModeratorRequiredMixin, generic.View):
    @transaction.atomic
    def post(self, request, *args, **kwargs):

        # validate if one of the user said game cancelled.
        match = MatchModel.objects.get(id=self.kwargs.get('pk'))
        mo_obj = MatchOperations(match)
        match_outputs = mo_obj.get_submitted_game_outputs()

        if CANCELLED in list(match_outputs.values_list('user_says', flat=True)):
            mo_obj.cancel_match()
            messages.success(self.request, 'Match cancelled successfully.')
        else:
            messages.success(self.request, 'Match Cannot be cancelled.')
        return redirect(reverse('moderatorapp:matches'))
