#Development Test Task
@author Raymond Puisha


# Requirements
- python 2.7
- Django 1.11
- sqlparse module for python (only if you want to create a new database)

## Package install via pip:
```
$ pip install django
$ pip install sqlparse
```

# Test-running
## DB Init
Test project is using SQLite database. Test database is already included, so this step can be omitted.
But if you wish to create a new database then execute:
``$ python manage.py migrate``

For admin access (optional) create a superuser:
``$ python manage.py createsuperuser``

###Superuser's credentials for Test database:
- user: admin
- pass: admin123

## Launching Test Server
``$ python manage.py runserver``

## Accessing Web Server
open http://127.0.0.1:8000/ in your web browser
admin site is also available @ http://127.0.0.1:8000/admin/
