# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import time
import urllib2
import json
from decimal import *
from django.db import models, IntegrityError
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator

class ErrorCodes:
    ERR_SYSTEM = 'ERR_DB'
    ERR_DB = 'ERR_DB'
    ERR_BALANCE = 'ERR_BALANCE'
    ERR_INVALID_INPUT = 'ERR_INVALID_INPUT'
    ERR_INVALID_CURRENCY = 'ERR_INVALID_CURRENCY'
    ERR_INVALID_ACCOUNT = 'ERR_INVALID_ACCOUNT'
    ERR_INVALID_AMOUNT = 'ERR_INVALID_AMOUNT'


# def get_currency_rate(curr_from, curr_to):
class CurrencyExchange(object):
    CURRENCIES = (
        ('USD', 'US Dollars'),
        ('EUR', 'Euro'),
        ('GBP', 'British Pounds'),
        ('CHF', 'Swiss Francs'),
    )
    BASE_URL = 'http://api.fixer.io/latest'

    def __init__(self):
        self.rates = {}

    def load_rates(self, curr):
        curr_found = False
        symbols = []
        for c in CurrencyExchange.CURRENCIES:
            if c[0] == curr:
                curr_found = True
            else:
                symbols.append(c[0])
        if not curr_found:
            raise ValidationError('Invalid currency: {}'.format(curr), ErrorCodes.ERR_INVALID_CURRENCY)

        query = '{0}?base={1}&symbols={2}'.format(CurrencyExchange.BASE_URL, curr, ','.join(symbols))
        response = urllib2.urlopen(query)
        if response.getcode() != 200:
            raise LookupError('Unable to retrieve currency rates for {}'.format(curr), ErrorCodes.ERR_SYSTEM)
        result = json.loads(response.read())
        self.rates[curr] = result['rates']
        self.rates[curr]['date'] = result['date']
        self.rates[curr]['last_update_time'] = time.time()

    def rates_deprecated(self, rate):
        # I wasn't sure how often rates needs to be updated, so I simply assumed once per hour
        return (time.time() - rate.get('last_update_time', 0)) > 3600

    def get_rate(self, curr_from, curr_to):
        if curr_from == curr_to:
            return 1.0
        if curr_from not in self.rates or self.rates_deprecated(self.rates[curr_from]):
            self.load_rates(curr_from)
        if not curr_to in self.rates[curr_from]:
            raise ValidationError('Invalid currency: {}'.format(curr_to), ErrorCodes.ERR_INVALID_CURRENCY)
        return self.rates[curr_from][curr_to]


class CurrencyAmountField(models.DecimalField):
    def __init__(self, **kwargs):
        kwargs.setdefault(b'max_digits', 18)
        kwargs.setdefault(b'decimal_places', 2)
        super(CurrencyAmountField, self).__init__(**kwargs)


class Account(models.Model):
    CURRENCIES = CurrencyExchange.CURRENCIES
    CURRENCY_EXCHANGE = CurrencyExchange()

    id = models.AutoField(
        verbose_name='Account no.',
        primary_key=True,
        editable=False,
    )

    currency = models.CharField(
        verbose_name='Currency code',
        max_length=3,
        choices=CURRENCIES,
    )
    balance = CurrencyAmountField(
        verbose_name='Current balance',
        editable=False,
    )

    def __init__(self, *args, **kwargs):
        self.force_insert = True
        super(Account, self).__init__(*args, **kwargs)

    def __str__(self):
        return "#{0} {1}".format(self.id, self.currency, self.balance)

    def save(self, *args, **kwargs):
        self.balance = 0
        self.full_clean()
        try:
            super(Account, self).save(*args, **kwargs)
        except IntegrityError as e:
            print str(e)
            raise ValidationError("Balance cannot be negative", code=ErrorCodes.ERR_BALANCE)


class Transaction(models.Model):
    # TODO(RP): In production environment consider using BigAutoField for PK
    src_account = models.ForeignKey(
        Account,
        verbose_name='Source account',
        related_name='src_account',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    dst_account = models.ForeignKey(
        Account,
        verbose_name='Destination account',
        related_name='dst_account',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    src_amount = CurrencyAmountField(
        verbose_name="Amount (in source account's currency)",
        validators=[MinValueValidator(0, 'Amount cannot be negative')],
        blank=True,
    )
    dst_amount = CurrencyAmountField(
        verbose_name="Amount (in destination account's currency)",
        validators=[MinValueValidator(0, 'Amount cannot be negative')],
        blank=True,
        editable=False,
    )
    create_timestamp = models.DateTimeField(
        verbose_name='Created at',
        auto_now_add=True,
        editable=False,
    )

    class Meta:
        ordering = ('-create_timestamp',)

    def __str__(self):
        s = ''
        if self.src_account:
            s += '%d (%.2f %s)' % (self.src_account.id, self.src_amount, self.src_account.currency)
        else:
            s += 'DEPOSIT'
        s += ' -> '
        if self.dst_account:
            s += '%d (%.2f %s)' % (self.dst_account.id, self.dst_amount, self.dst_account.currency)
        else:
            s += 'WITHDRAWAL'
        return s

    def same_currency(self):
        return not self.src_account or not self.dst_account or self.src_account.currency == self.dst_account.currency

    def internal(self):
        return self.src_account and self.dst_account

    def external(self):
        return (self.src_account is None) != (self.dst_account is None)

    def clean(self, *args, **kwargs):
        if self.src_account is None and self.dst_account is None:
            raise ValidationError('At least one of accounts must be set', code=ErrorCodes.ERR_INVALID_ACCOUNT)
        if self.src_account == self.dst_account:
            raise ValidationError('The same account cannot be used for both source and destination', code=ErrorCodes.ERR_INVALID_ACCOUNT)

        # User enters only src_amount. We need to calculate dst_amount ourselves
        if not self.dst_amount:
            self.dst_amount = self.src_amount
        elif not self.src_amount:
            self.src_amount = self.dst_amount

        if not self.src_account:
            self.src_amount = None
        elif  not self.src_amount:
            raise ValidationError("Amount is not set", code=ErrorCodes.ERR_INVALID_AMOUNT)

        if not self.dst_account:
            self.dst_amount = None
        elif  not self.dst_amount:
            raise ValidationError("Amount is not set", code=ErrorCodes.ERR_INVALID_AMOUNT)

        if self.internal() and not self.same_currency():
            rate = Account.CURRENCY_EXCHANGE.get_rate(self.src_account.currency, self.dst_account.currency)
            print rate
            self.dst_amount = Decimal(float(self.src_amount) * rate).quantize(Decimal('.01'), rounding=ROUND_HALF_EVEN )
            print self.dst_amount

        super(Transaction, self).clean(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.full_clean()
        try:
            super(Transaction, self).save(*args, **kwargs)
        except IntegrityError as e:
            emsg = str(e)
            if emsg.find('chk_balance') != -1:
                raise ValidationError("Balance cannot be negative", code=ErrorCodes.ERR_BALANCE)
            raise e
