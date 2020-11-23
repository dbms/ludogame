import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from ludoapp.models import MatchModel
from ludoapp.choices import ACCEPTED
from ludoapp.match import MatchOperations


class Command(BaseCommand):
    help = 'Cancel matches which are in accepted state for more than 90 seconds.' \
           'And make users available to play tha match again.'

    def handle(self, *args, **kwargs):

        accepted_matches = MatchModel.objects.filter(status=ACCEPTED)

        for match in accepted_matches:
            now = timezone.make_aware(datetime.datetime.now(), timezone.get_default_timezone())

            if (now - match.updated_on).seconds > 90:
                mo_obj = MatchOperations(match)
                mo_obj.cancel_match()
