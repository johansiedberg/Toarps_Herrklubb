from django.contrib.staticfiles.management.commands.runserver import Command as StaticfilesRunserverCommand

class Command(StaticfilesRunserverCommand):
    default_port = "1981"
