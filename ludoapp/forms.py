from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from ludoapp import choices
from ludoapp.models import Transactions, MatchModel, GameOutputModel, PhoneOTP, SupportModel


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transactions
        fields = ['amount', 'transaction_id']
        labels = {
            'transaction_id': "Order ID"
        }
        help_texts = {
            'transaction_id': 'Enter a random transaction ID.'
        }

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount < 20:
            raise forms.ValidationError("Minimum allowed is 20.")
        return amount


class MatchForm(forms.ModelForm):
    class Meta:
        model = MatchModel
        fields = ['bid_amount', ]
        labels = {
            'bid_amount': "Enter Coins"
        }
        help_texts = {
            'bid_amount': 'Allowed Coins - [20, 40, 60, 100, ...., upto your balance]'
        }

    def clean_bid_amount(self):
        bid_amount = self.cleaned_data['bid_amount']
        if bid_amount <= 0:
            raise forms.ValidationError("Amount should be greater than 0")
        if bid_amount % 20 != 0:
            raise forms.ValidationError("Amount can only be a multiple of 20")
        return bid_amount


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)

    class Meta:
        model = User
        fields = [
            'username',
            'first_name',
            'last_name',
            'password1',
            'password2',
        ]
        labels = {
            'username': 'Phone Number'
        }

    def __init__(self, *args, **kwargs):
        super(RegisterForm, self).__init__(*args, **kwargs)

        for fieldname in ['username', 'password1', 'password2']:
            self.fields[fieldname].help_text = None

    def clean_first_name(self):
        first_name = self.cleaned_data['first_name']
        return first_name.title()

    def clean_last_name(self):
        last_name = self.cleaned_data['last_name']
        return last_name.title()

    def clean_username(self):
        username = self.cleaned_data['username'].strip()

        if username.isdigit() and len(username) == 10:
            return username

        raise forms.ValidationError("Enter a valid phone number")


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label='Phone Number',
        widget=forms.TextInput(attrs={'autofocus': True})
    )


class ValidateOTPForm(forms.ModelForm):
    class Meta:
        model = PhoneOTP
        fields = ['otp', ]


class ForgotPasswordForm(forms.Form):
    phone_number = forms.CharField(
        label='Phone Number', max_length=10,
        widget=forms.TextInput(attrs={'autofocus': True})
    )


class GameCodeForm(forms.ModelForm):
    class Meta:
        model = MatchModel
        fields = ['game_code', ]
        help_texts = {
            'game_code': 'Go to Ludo King app to get the code.'
        }

    def clean_game_code(self):
        game_code = self.cleaned_data['game_code']

        if len(game_code) != choices.GAME_CODE_LENGTH:
            raise forms.ValidationError("Game code length must be 8")
        return game_code


class GameOutputForm(forms.ModelForm):
    class Meta:
        model = GameOutputModel
        fields = ['user_says', 'screenshot', ]
        widgets = {
            'user_says': forms.RadioSelect()
        }
        labels = {
            'user_says': 'Game Result'
        }
        help_texts = {
            'screenshot': 'No need to upload screenshot if you choose Lost option.'
        }

    def clean_screenshot(self):
        ss = self.cleaned_data['screenshot']
        user_says = self.cleaned_data['user_says']

        if user_says != choices.LOST and not ss:
            raise forms.ValidationError("Screenshot is required if you choose other option than LOST")
        return ss


class SupportForm(forms.ModelForm):

    class Meta:
        model = SupportModel
        fields = ['contact_mobile', 'message', 'attach_screenshot']
        labels = {
            'contact_mobile': 'Your Contact Number',
            'attach_screenshot': 'Attach Screenshot',
        }
        widgets = {
            'message': forms.Textarea(attrs={'rows': 4}),
        }
