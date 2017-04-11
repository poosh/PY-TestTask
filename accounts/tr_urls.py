from django.conf.urls import url
from views import *

urlpatterns = [
    url(r'^$', TransactionAdd.as_view(), name='trx-add'),
]