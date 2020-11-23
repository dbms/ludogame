import datetime
from decimal import Decimal

from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils import timezone
from django.views import generic

from ludoapp import choices
from ludoapp.forms import TransactionForm, MatchForm, GameCodeForm, GameOutputForm, SupportForm
from ludoapp.models import Transactions, UserProfile, MatchModel, TermsConditionsModel, SupportModel, WithdrawModel
from ludoapp.match import MatchOperations, UserOperations, WithdrawOperations
from main.decorators import RegularUserRequiredMixin
from ludoapp.payment.paymentapp import UserPayment


class HomeView(generic.TemplateView):
    template_name = 'ludoapp/home.html'


class DashBoardView(RegularUserRequiredMixin, generic.View):
    form_class = MatchForm
    template_name = 'ludoapp/dashboard.html'

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():

            # check if user is available
            if not request.user.userprofile.is_available:
                # check if user has submitted a withdraw request(display proper message)
                filter_ongoing_requests = WithdrawModel.objects.filter(user=self.request.user, status=choices.INITIATED)
                if len(filter_ongoing_requests) > 0:
                    messages.error(self.request, 'You cannot play untill you withdrawl request is processed.')
                    return redirect(reverse('ludoapp:dashboard'))
                else:
                    messages.error(request, 'First finish your in-progress match or cancel the challenge.')
                    return redirect(reverse('ludoapp:dashboard'))

            # check if her has sufficient balance
            if request.user.userprofile.balance < form.cleaned_data['bid_amount']:
                messages.error(request, 'Insufficient Balance, Add coins here.')
                return redirect(reverse('ludoapp:buy_coins'))

            match = form.save(commit=False)
            match.player1 = self.request.user
            # mark user as busy
            UserProfile.objects.filter(user=self.request.user).update(is_available=False)
            match.save()
            return redirect(reverse('ludoapp:dashboard'))

        return render(request, self.template_name, {'form': form})


class MatchesListView(RegularUserRequiredMixin, generic.ListView):
    template_name = 'ludoapp/matches.html'
    model = MatchModel
    context_object_name = 'ongoing_matches'
    ordering = ['-id']

    def get_queryset(self):
        queryset = super(MatchesListView, self).get_queryset()
        queryset = queryset.filter(status=choices.INPROGRESS)
        return queryset

    def get_context_data(self, **kwargs):
        context = super(MatchesListView, self).get_context_data(**kwargs)
        context['balance'] = UserProfile.objects.get(user=self.request.user).balance
        context['open_matches'] = MatchModel.objects.filter(
            Q(status=choices.OPEN) | Q(player1=self.request.user, status=choices.ACCEPTED))
        return context


class BuyCoinsView(RegularUserRequiredMixin, generic.View):
    template_name = 'ludoapp/buy-coins.html'
    form_class = TransactionForm
    context = {}

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        self.get_balance()
        self.context['form'] = form
        return render(request, self.template_name, self.context)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        self.get_balance()
        form = self.form_class(request.POST)
        if form.is_valid():
            amount_from_user = round(Decimal(form.cleaned_data['amount']), 2)
            response = UserPayment.check_transaction_status(amount_from_user)
            txn_status = response.get('STATUS')
            txn_amount = response.get('TXNAMOUNT')

            if txn_status != 'TXN_SUCCESS' or Decimal(txn_amount) != amount_from_user:
                messages.error(request, 'Invalid transaction.')
                return redirect(reverse('ludoapp:buy_coins'))

            form = form.save(commit=False)
            form.user = self.request.user
            form.api_response = response
            form.mode = choices.BUY_COIN

            # add amount to user's account
            uo_obj = UserOperations(request.user)
            uo_obj.add_balance(form.amount)

            # save the updated user balance in transaction table also
            form.user_balance = request.user.userprofile.balance
            form.save()

            messages.success(request, 'Coins added successfully.')
            return redirect(reverse('ludoapp:buy_coins'))

        self.context['form'] = form
        return render(request, self.template_name, self.context)

    # find an alternate of this thing
    def get_balance(self):
        self.context['balance'] = UserProfile.objects.get(user=self.request.user).balance


class TransactionListView(RegularUserRequiredMixin, generic.ListView):
    template_name = 'ludoapp/transactions.html'
    model = Transactions
    context_object_name = 'transactions'
    paginate_by = 10
    ordering = ['-created_on']

    def get_queryset(self):
        queryset = super(TransactionListView, self).get_queryset()
        queryset = queryset.filter(user=self.request.user)
        return queryset

    def get_context_data(self, **kwargs):
        context = super(TransactionListView, self).get_context_data(**kwargs)
        context['balance'] = self.request.user.userprofile.balance
        return context


class MatchHistoryListView(RegularUserRequiredMixin, generic.ListView):
    template_name = 'ludoapp/match-history.html'
    model = MatchModel
    context_object_name = 'matches'
    paginate_by = 10
    ordering = ['-created_on']

    def get_queryset(self):
        queryset = super(MatchHistoryListView, self).get_queryset()
        queryset = queryset.filter(Q(player1=self.request.user) | Q(player2=self.request.user))
        return queryset

    def get_context_data(self, **kwargs):
        context = super(MatchHistoryListView, self).get_context_data(**kwargs)
        context['count'] = self.get_queryset().count()
        return context


class GameCodeUpdateView(RegularUserRequiredMixin, generic.UpdateView):
    model = MatchModel
    template_name = 'ludoapp/match-screen.html'
    form_class = GameCodeForm

    def get(self, request, *args, **kwargs):
        self.should_cancel_match()
        return super().get(request, *args, **kwargs)

    def get_object(self):
        """
        overriding get_object because not using pk/id to update the match,
        using uuid so have to override the get_object method

        :return: MatchModel object
        """

        return MatchModel.objects.get(uuid=self.kwargs.get('uuid'))

    @transaction.atomic
    def form_valid(self, form, **kwargs):
        match = self.object

        if self.should_cancel_match():
            messages.error(self.request, 'You entered the code after 90 seconds.')
            return redirect(reverse('ludoapp:dashboard'))

        # check if any other player than player1 is entering the game code
        if match.player1 != self.request.user:
            messages.error(self.request, 'The player who set the challenge is allowed to enter the game code.')
            return redirect(reverse('ludoapp:match_screen', args=(match.uuid,)))

        # allow game code only when match is in accepted state
        elif match.status != choices.ACCEPTED:
            messages.error(self.request, 'This game is not in Accepted State')
            return redirect(reverse('ludoapp:match_screen', args=(match.uuid,)))

        else:
            form.save()
            # update match status to inprogress
            match.status = choices.INPROGRESS
            match.save()
            messages.success(self.request, 'Go to the game and wait for other player to join!')
            return redirect(reverse('ludoapp:match_screen', args=(match.uuid,)))

    def should_cancel_match(self):
        """
        cancel the match is game code is not entered in 90 seconds
        :return: bool
        """

        match = self.get_object()
        now = timezone.make_aware(datetime.datetime.now(), timezone.get_default_timezone())
        if (now - match.updated_on).seconds > 90 and match.status == choices.ACCEPTED:
            mo_obj = MatchOperations(match)
            mo_obj.cancel_match()
            return True
        else:
            False


class SaveGameOutputView(RegularUserRequiredMixin, generic.FormView):
    template_name = 'ludoapp/match-output.html'
    form_class = GameOutputForm
    context = {}

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)

        if form.is_valid():
            match = MatchModel.objects.get(uuid=self.kwargs.get('uuid'))
            mo_obj = MatchOperations(match)

            # check who is submitting the game output
            if request.user not in [match.player1, match.player2]:
                messages.error(self.request, 'Only players who played this match are allowd to submit the result.')
                return redirect(reverse('ludoapp:dashboard'))

            # check if user has already submitted the output
            if request.user.id in mo_obj.get_match_players_ids():
                messages.error(self.request, 'You have already submitted the result.')
                return redirect(reverse('ludoapp:dashboard'))

            # check if winner is already decided
            if match.winner:
                messages.error(self.request,
                               f'{match.winner.userprofile.full_name()}'
                               f' is the winner for this match. Disagree? Contact Support.')
                return redirect(reverse('ludoapp:dashboard'))

            # check if match decision is taken as cancelled already
            if match.status == choices.CANCELLED:
                messages.error(self.request, 'This match is decided as cancelled. Disagree? Contact Support.')
                return redirect(reverse('ludoapp:dashboard'))

            # else save the output
            out = form.save(commit=False)
            out.match = match
            out.player = request.user
            out.save()

            mo_obj.decide_match_winner_automatically()

            messages.success(self.request, 'Game result submitted.')
            return redirect(reverse('ludoapp:dashboard'))
        else:
            return self.form_invalid(form)


class TermsConditionsView(generic.ListView):
    model = TermsConditionsModel
    template_name = 'terms.html'


class SupportCreateView(RegularUserRequiredMixin, generic.CreateView):
    model = SupportModel
    template_name = 'support.html'
    form_class = SupportForm

    def form_valid(self, form):
        form = form.save(commit=False)
        form.user = self.request.user
        form.save()

        messages.success(self.request, 'Message Recieved.')
        return redirect(reverse('ludoapp:support'))

    def get_context_data(self, **kwargs):
        context = super(SupportCreateView, self).get_context_data(**kwargs)
        context['support_history'] = SupportModel.objects.filter(user=self.request.user)[:10]
        return context


class WithdrawCoinCreateView(RegularUserRequiredMixin, generic.CreateView):
    model = WithdrawModel
    fields = ['amount', 'send_to']
    template_name = 'ludoapp/withdraw.html'

    @transaction.atomic()
    def form_valid(self, form):

        # check if a request is already initiated
        filter_ongoing_requests = WithdrawModel.objects.filter(user=self.request.user, status=choices.INITIATED)
        if len(filter_ongoing_requests) > 0:
            messages.error(self.request, 'Wait until your previous request is processed.')
            return redirect(reverse('ludoapp:withdraw_coin'))

        # check if requested amount is greater than balance.
        if self.request.user.userprofile.balance < form.cleaned_data['amount']:
            messages.error(self.request, 'Your balance is less than requested amount.')
            return redirect(reverse('ludoapp:withdraw_coin'))

        # validate Minimum Withraw Amount
        if form.cleaned_data['amount'] < choices.MIN_WITHDRAW_AMOUNT:
            messages.error(self.request, f'Minimum withdraw amount is {choices.MIN_WITHDRAW_AMOUNT}')
            return redirect(reverse('ludoapp:withdraw_coin'))

        # Validate user should not in mid of any match(check availability)
        if not self.request.user.userprofile.is_available:
            messages.error(self.request, 'Finish your ongoing match for submitting withdraw request.')
            return redirect(reverse('ludoapp:withdraw_coin'))

        form = form.save(commit=False)
        form.user = self.request.user
        form.save()

        wo_obj = WithdrawOperations(self.request.user)
        wo_obj.withdraw_state_changed(choices.INITIATED)

        messages.success(self.request, 'Request Submitted.')
        return redirect(reverse('ludoapp:withdraw_coin'))

    def get_context_data(self, **kwargs):
        context = super(WithdrawCoinCreateView, self).get_context_data(**kwargs)
        context['withdraw_history'] = WithdrawModel.objects.filter(user=self.request.user)[:10]
        context['balance'] = self.request.user.userprofile.balance
        return context
