from django import forms
from models import Account, Transaction


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ('currency',)
