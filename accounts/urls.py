from django.conf.urls import url
from views import *

urlpatterns = [
    url(r'^$', AccountList.as_view(), name='accounts'),
    url(r'^add/$', AccountAdd.as_view(), name='account-add'),
    url(r'^(\d{8})/$', AccountTransactions.as_view(), name='transactions'),
    url(r'^add/$', AccountAdd.as_view(), name='account-add'),
]