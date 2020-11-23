import logging
from random import randint

from django.contrib.auth.models import User
from django.db.models import Q

from ludoapp import choices
from ludoapp.models import GameOutputModel, UserProfile, Transactions

logger = logging.getLogger(__name__)


class MatchOperations(object):

    def __init__(self, match):
        self.match = match

    def accept_challenge(self, who_accepted):
        """
        accept the challenge

        :param who_accepted: player who accepted the challenge
        :return: None
        """

        self.match.status = choices.ACCEPTED
        self.match.player2 = who_accepted
        self.match.save()

        # make both players busy again
        self.change_player_available_state(False)

    def get_transfer_and_commission_amount(self):

        bid_amount = self.match.bid_amount
        # if amount is less than 100 then 20% commission
        if bid_amount <= 100:
            commission = bid_amount / 5

        # if amount is b/w 100 and 300 then 10% commission
        elif 100 < bid_amount <= 300:
            commission = bid_amount / 10

        # above 300 commission is 5%
        else:
            commission = bid_amount / 20

        return bid_amount - commission, commission

    def cancel_match(self):
        self.match.status = choices.CANCELLED
        self.match.save()
        # make both players available again
        self.change_player_available_state(True)

    def change_player_available_state(self, state: bool):
        """
        change user available state.

        :param state: available or busy
        :return: None
        """

        UserProfile.objects.filter(
            Q(user=self.match.player1) | Q(user=self.match.player2)).update(is_available=state)

    def decide_match_winner_automatically(self):
        outputs = self.get_submitted_game_outputs()

        if len(outputs) == 1:
            output_1 = outputs[0]
            if output_1.user_says == choices.LOST:
                winner, looser = self.get_match_winner_looser(player_is='looser', player=output_1.player)

                self.update_match_winner(winner)
                self.transfer_bid_amount(winner, looser)
                self.update_match_status(choices.OVER)
                self.change_player_available_state(True)

        elif len(outputs) > 1:
            output_1, output_2 = outputs

            # check if both said cancelled
            if output_1.user_says == output_2.user_says == choices.CANCELLED:
                self.cancel_match()

            elif output_1.user_says == choices.LOST or output_2.user_says == choices.LOST:
                if output_1.user_says == choices.LOST:
                    winner, looser = self.get_match_winner_looser(player_is='looser', player=output_1.player)
                else:
                    winner, looser = self.get_match_winner_looser(player_is='looser', player=output_2.player)

                self.update_match_winner(winner)
                self.transfer_bid_amount(winner, looser)
                self.update_match_status(choices.OVER)
                self.change_player_available_state(True)
            else:
                logger.info(f'Cannot determine winner automatically, moderator will decide match is - {self.match.id}')
        else:
            logger.error(f'More then 2 game outputs were submitted for match id -{self.match.id}')

    def decided_match_winner_by_moderator(self, winner):
        winner, looser = self.get_match_winner_looser(player_is='winner', player=winner)

        self.update_match_winner(winner)
        self.transfer_bid_amount(winner, looser)
        self.update_match_status(choices.OVER)
        self.change_player_available_state(True)

    def get_match_players_ids(self) -> list:
        """
        return the match player's id's ad list

        :return: list of ids
        """

        ids = GameOutputModel.objects.filter(
            match=self.match).values_list('player', flat=True)

        return ids or []

    def get_match_winner_looser(self, player_is, player):
        """
        return the winner and looser of the match

        :param player_is: player is winner of looser
        :param player: who lost the match
        :return: winner and looser
        """

        # this decide the assuming player is winner
        if self.match.player1 == player:
            winner = self.match.player1
            looser = self.match.player2
        else:
            winner = self.match.player2
            looser = self.match.player1

        # if player was looser swap
        if player_is == 'looser':
            winner, looser = looser, winner

        return [winner, looser]

    def get_submitted_game_outputs(self):
        """
        return the game outputs submitted by the players

        :return: queryset of game outputs
        """

        return GameOutputModel.objects.filter(match=self.match)

    def transfer_bid_amount(self, winner, looser):
        if looser.userprofile.balance < self.match.bid_amount:
            logger.error('We are in some inconsistent state, looser doesn\'t have sufficient transfer_amount')

        # update looser balance
        uo_obj_looser = UserOperations(looser)
        uo_obj_looser.minus_balance(self.match.bid_amount)
        # passing updated looser model instance to create transaction
        self.create_transaction(user=looser, mode=choices.MATCH_LOST, amount=-1*int(self.match.bid_amount))

        transfer_amount, commission = self.get_transfer_and_commission_amount()

        # update winner balance
        uo_obj_winner = UserOperations(winner)
        uo_obj_winner.add_balance(transfer_amount)
        self.create_transaction(user=winner, mode=choices.MATCH_WON, amount=transfer_amount)

        # update admin balance
        uo_obj_admin = UserOperations(self.get_admin())
        uo_obj_admin.add_balance(commission)
        self.create_transaction(user=self.get_admin(), mode=choices.MATCH_COMMISSION, amount=commission)

    def update_match_status(self, status):
        """
        updates the status of the match

        :return: None
        """

        self.match.status = status
        self.match.save()

    def update_match_winner(self, winner):
        """
        updates the status of the match

        :return: None
        """

        self.match.winner = winner
        self.match.status = choices.OVER
        self.match.save()

    @staticmethod
    def get_admin():
        return User.objects.get(username='admin')

    @staticmethod
    def create_transaction(user, mode, amount):
        updated_user_balance = UserProfile.objects.get(user=user).balance
        Transactions.objects.create(
            user=user,
            user_balance=updated_user_balance,
            amount=amount,
            transaction_id=str(MatchOperations.generate_fake_transaction_id()),
            mode=mode
        )

    @staticmethod
    def generate_fake_transaction_id():
        random_id = randint(-10000000, 0)

        if Transactions.objects.filter(transaction_id=random_id).exists():
            return MatchOperations.generate_fake_transaction_id()
        else:
            return random_id


class UserOperations(object):
    def __init__(self, user):
        self.user = user

    def add_balance(self, amount):
        self.user.userprofile.balance += amount
        self.user.userprofile.save()

    def minus_balance(self, amount):
        self.user.userprofile.balance -= amount
        self.user.userprofile.save()


class WithdrawOperations(object):
    def __init__(self, user):
        self.user = user

    def withdraw_state_changed(self, status):
        if status == choices.INITIATED:
            self.user.userprofile.is_available = False
            self.user.userprofile.save()

        elif status in [choices.PROCESSED, choices.DENIED]:
            self.user.userprofile.is_available = True
            self.user.userprofile.save()

        else:
            logger.error("Invalid Withdraw State")

    def process_request(self, withdraw_model_obj):

        # substract the balance
        uo_obj = UserOperations(self.user)
        uo_obj.minus_balance(withdraw_model_obj.amount)

        # create a transaction
        MatchOperations.create_transaction(
            user=self.user,
            mode=choices.COIN_SOLD,
            amount=withdraw_model_obj.amount
        )


