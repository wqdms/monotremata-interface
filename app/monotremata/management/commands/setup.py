import os
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
import socket


def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0


DJANGO_PORT = os.getenv("DJANGO_PORT", "8000")


class Command(BaseCommand):
    help = "write / add a value to a list in a script file"

    def add_arguments(self, parser):
        parser.add_argument(
            "-s",
            "--setup",
            nargs="?",
            required=False,
            default=False,
            type=str,
            help="""makemigrations, migrate, tests, runserver, use flag value: '-s r' or '-s run' to run server""",
        )
        parser.add_argument(
            "-d",
            "--database",
            nargs="?",
            required=False,
            default="sqlite3",
            type=str,
            choices=["spatialite","postgres","postgis","sqlite3"],
            help="""database backend engine options""",
        )

    def handle(self, *args, **options):
        run_setup = options.get("setup")
        database = options.get("database")
        try:
            if run_setup not in [False]:
                os.environ.setdefault("DATABASE_ENGINE", database)
                call_command("makemigrations")
                call_command("migrate")
                call_command("loaddata", "admin_interface_theme_bootstrap.json")
                call_command("loaddata", "admin_interface_theme_foundation.json")
                call_command("loaddata", "admin_interface_theme_uswds.json")
                if os.path.exists(settings.BASE_DIR / "user.json"):
                    call_command("loaddata", str(settings.BASE_DIR / "user.json"))

                if os.path.exists(settings.BASE_DIR / "themes.json"):
                    call_command("loaddata", str(settings.BASE_DIR / "themes.json"))

                if os.path.exists(settings.BASE_DIR / "presets.json"):
                    call_command("loaddata", str(settings.BASE_DIR / "presets.json"))

                if run_setup in ["r", "run"]:
                    call_command("runserver", f"0.0.0.0:{DJANGO_PORT}")

            else:
                call_command("setup", "-h")
        except Exception as e:
            print(e)
        print(settings.DATABASES)
