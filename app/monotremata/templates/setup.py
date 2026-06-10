import os
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
import socket

def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0



DJANGO_PORT=os.getenv("DJANGO_PORT","8000")
class Command(BaseCommand):
    help = "write / add a value to a list in a script file"

    def add_arguments(self, parser):
        parser.add_argument(
            "-s", "--setup", nargs="?", required=False, default=False, type=bool, help="""makemigrations, migrate, tests, runserver"""
        )
        
        
    def handle(self, *args, **options):
        run_setup = options.get("setup")
        try:
            if run_setup not in [False]:
                call_command("makemigrations")
                call_command("migrate")
                # {{ category }}
                {% if category == "server" %}
                
                call_command("loaddata", "admin_interface_theme_bootstrap.json")
                call_command("loaddata", "admin_interface_theme_foundation.json")
                call_command("loaddata", "admin_interface_theme_uswds.json")
                        
                {% endif %}

                if os.path.exists(settings.BASE_DIR / "user.json"):
                    call_command("loaddata", str(settings.BASE_DIR / "user.json"))

                if os.path.exists(settings.BASE_DIR / "themes.json"):
                    call_command("loaddata", str(settings.BASE_DIR / "themes.json"))

                if os.path.exists(settings.BASE_DIR / "presets.json"):
                    call_command("loaddata", str(settings.BASE_DIR / "presets.json"))

                port = int(DJANGO_PORT)
                x = is_port_in_use(port)
                if not x:
                    call_command("runserver",f"0.0.0.0:{DJANGO_PORT}") 

            else:
                call_command("setup","-h")
        except Exception as e:
            print(e)