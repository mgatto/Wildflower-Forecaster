from wtforms_alchemy import ModelForm
from models import Account

class AccountForm(ModelForm):
    class Meta:
        model = Account
