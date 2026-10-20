#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

# OpenCV / BLAS multi-threading + Python 3.14 regularly heap-corrupt on Windows
# under concurrent camera detect. Force single-threaded native runtimes first.
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")
os.environ.setdefault("OPENCV_FOR_THREADS_NUM", "1")
os.environ.setdefault("CV_OPENCL_RUNTIME", "")
os.environ.setdefault("OPENCV_OPENCL_RUNTIME", "")


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
