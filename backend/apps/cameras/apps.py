import os
import sys

from django.apps import AppConfig


class CamerasConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.cameras"
    label = "cameras"

    def ready(self):
        # Django autoreload parent process
        if os.environ.get("RUN_MAIN") == "false":
            return
        # Only boot workers with the web server, not migrate/shell/test.
        argv0 = os.path.basename(sys.argv[0]) if sys.argv else ""
        command = sys.argv[1] if len(sys.argv) > 1 else ""
        web_servers = {"runserver", "uvicorn", "gunicorn"}
        if command not in web_servers and argv0 not in web_servers:
            return
        try:
            from apps.cameras.continuous_recorder import recorder_manager

            recorder_manager.ensure_started()
        except Exception:
            pass
        try:
            from apps.cameras.detection import boot_person_watcher

            boot_person_watcher()
        except Exception:
            pass
