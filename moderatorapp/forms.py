from django import forms
from django.db.models import Q

from django.contrib.auth.models import User
from ludoapp.models import MatchModel, WithdrawModel
from ludoapp.choices import INPROGRESS, PROCESSED, DENIED


class MatchForm(forms.ModelForm):
    winner = forms.ModelChoiceField(queryset=User.objects.none())

    class Meta:
        model = MatchModel
        fields = ['winner', ]

    def __init__(self, *args, **kwargs):
        super(MatchForm, self).__init__(*args, **kwargs)
        match = MatchModel.objects.get(id=kwargs.get('instance').pk)
        if match.status == INPROGRESS:
            self.fields['winner'].queryset = User.objects.filter(
                Q(id=match.player1.id) | Q(id=match.player2.id))


class WithdrawForm(forms.ModelForm):

    class Meta:
        model = WithdrawModel
        fields = ['status', 'transaction_id', 'reason', 'proof_screenshot']
        widgets = {
            'reason': forms.Textarea(attrs={'rows': 4}),
        }

    def clean_proof_screenshot(self):
        ss = self.cleaned_data['proof_screenshot']

        if self.cleaned_data['status'] == PROCESSED and not ss:
            raise forms.ValidationError("Screenshot is required if you have processed a transaction.")
        return ss

    def clean_reason(self):
        reason = self.cleaned_data['reason']

        if self.cleaned_data['status'] == DENIED and not reason:
            raise forms.ValidationError("Give a reason why you denied.")
        return reason

    def clean_transaction_id(self):
        transaction_id = self.cleaned_data['transaction_id']

        if self.cleaned_data['status'] == PROCESSED and not transaction_id:
            raise forms.ValidationError("Enter the transaction ID of the processed transaction.")
        return transaction_id

