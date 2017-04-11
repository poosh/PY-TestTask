# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.views.generic import ListView, CreateView
from django.db.models import Q
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.http import JsonResponse

from CdsTestProj.settings import BASE_DIR
from .models import Account, Transaction, ErrorCodes


class AccountList(ListView):
    model = Account
    template_name = os.path.join(BASE_DIR, 'accounts/templates/account_list.html')

    def get_queryset(self):
        f_currency = self.request.GET.get('currency', None)
        if f_currency:
            return Account.objects.filter(currency=f_currency)
        return Account.objects.all()

    def get_context_data(self, **kwargs):
        context = super(AccountList, self).get_context_data(**kwargs)
        context['currencies'] = Account.CURRENCIES
        # context['messages'] = ['Test message 1', 'Test message 2']
        return context

# class AccountAdd(FormView):
#     template_name = 'account_form.html'
#     form_class = AccountForm
#     success_url = '/accounts/'
#
#     def form_valid(self, form):
#         # This method is called when valid form data has been POSTed.
#         # It should return an HttpResponse.
#         # form.send_email()
#         return super(AccountAdd, self).form_valid(form)

class AjaxableResponseMixin(object):
    """
    Mixin to add AJAX support to a form.
    Must be used with an object-based FormView (e.g. CreateView)
    """
    def form_invalid(self, form):
        response = super(AjaxableResponseMixin, self).form_invalid(form)
        data = {
            'error' : True,
            'details': form.errors,
        }
        error_data = self.get_error_data(form)
        data.update(self.get_error_data(form))
        return JsonResponse(data, status=400)

    def form_valid(self, form):
        # We make sure to call the parent's form_valid() method because
        # it might do some processing (in the case of CreateView, it will
        # call form.save() for example).

        data = {
            'error' : True,
        }
        try:
            response = super(AjaxableResponseMixin, self).form_valid(form)
            data['error'] = False
            data['data'] = self.get_response_data(form)
        except IntegrityError as e:
            data['code'] = ErrorCodes.ERR_DB
            data['message'] = e.message
            return JsonResponse(data, status=400)
        except ValidationError as e:
            try:
                data['code'] = e.code
                data['message'] = e.message
                return JsonResponse(data, status=400)
            except AttributeError:
                data['code'] = ErrorCodes.ERR_SYSTEM
                data['message'] = 'System error'
                return JsonResponse(data, status=500)
        except Exception as e:
            data['code'] = ErrorCodes.ERR_SYSTEM
            data['message'] = e.message
            return JsonResponse(data, status=400)
        return JsonResponse(data)

    def get_response_data(self, form):
        return None

    def get_error_data(self, form):
        return {
            'code': form.errors.get('err_code', ErrorCodes.ERR_INVALID_INPUT),
            'message' : form.errors.get('err_message', 'Illegal input data'),
        }

class AccountAdd(AjaxableResponseMixin, CreateView):
    model = Account
    template_name = os.path.join(BASE_DIR, 'accounts/templates/account_form.html')
    success_url = '/accounts/'
    fields = ['currency',]

    def get_response_data(self, form):
        return { 'accountNumber': str(self.object.id), }


class TransactionAdd(AjaxableResponseMixin, CreateView):
    model = Transaction
    template_name = os.path.join(BASE_DIR, 'accounts/templates/transaction_form.html')
    success_url = '/'
    fields = ['src_account', 'src_amount', 'dst_account']

    def get_response_data(self, form):
        return { 'transactionId': self.object.id, }


class AccountTransactions(ListView):
    model = Transaction
    template_name = os.path.join(BASE_DIR, 'accounts/templates/account_transactions.html')

    def get_queryset(self):
        self.account = get_object_or_404(Account, id=self.args[0])
        return Transaction.objects.filter(Q(dst_account=self.account) | Q(src_account=self.account))


    def get_context_data(self, **kwargs):
        context = super(AccountTransactions, self).get_context_data(**kwargs)
        context['account'] = self.account
        return context

