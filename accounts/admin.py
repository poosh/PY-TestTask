# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

# Register your models here.

from .models import Account
from .models import Transaction


class AccountAdmin(admin.ModelAdmin):
    list_display = ('id', 'balance', 'currency')

class TransactionAdmin(admin.ModelAdmin):
    list_display = ('src_account', 'src_amount', 'dst_account', 'dst_amount', 'create_timestamp')

admin.site.register(Account, AccountAdmin)
admin.site.register(Transaction, TransactionAdmin)
