from django.contrib import messages
from django.db import transaction
from django.shortcuts import render, redirect
from django.urls import reverse

from ludoapp.models import MatchModel, UserProfile
from ludoapp.choices import CANCELLED, OPEN, ACCEPTED, INPROGRESS
from ludoapp.match import MatchOperations
from main.decorators import regular_user_required


@regular_user_required
@transaction.atomic
def cancel_match(request, uuid):
    if request.method == 'POST':
        match = MatchModel.objects.get(uuid=uuid)

        # check if player who created the challenge is cancelling it from dashboard
        if match.player1 != request.user:
            messages.success(request, 'You don\'t have permission to cancel this match!')
            return redirect(reverse('ludoapp:dashboard'))

        if match.status in [OPEN, ACCEPTED]:
            mo_obj = MatchOperations(match)
            mo_obj.cancel_match()
            messages.success(request, 'Challenge cancelled successfully!')
        else:
            messages.error(request, 'Match cannot be cancelled.')

    return redirect(reverse('ludoapp:dashboard'))


@regular_user_required
@transaction.atomic
def play_match(request, uuid):
    if request.method == 'POST':
        # check form is valid here
        match = MatchModel.objects.get(uuid=uuid)

        # check if user is available
        if not request.user.userprofile.is_available:
            messages.error(request, 'First finish your in-progress match or cancel the challenge.')
            return redirect(reverse('ludoapp:dashboard'))

        # check if player wants to play with himself
        if match.player1 == request.user:
            messages.error(request, 'You are trying to play with yourself, seriously!!')
            return redirect(reverse('ludoapp:dashboard'))

        # check if match is open
        elif match.status != OPEN:
            messages.error(request, 'This challenge is not available.')
            return redirect(reverse('ludoapp:dashboard'))

        # check if the player has sufficient balance
        elif request.user.userprofile.balance < match.bid_amount:
            messages.error(request, 'You don\'t have sufficient coins to play this match. Buy coins here.')
            return redirect(reverse('ludoapp:buy_coins'))

        else:
            mo_obj = MatchOperations(match)
            mo_obj.accept_challenge(who_accepted=request.user)

            return redirect(reverse('ludoapp:match_screen', args=(match.uuid,)))

    return redirect(reverse('ludoapp:dashboard'))
