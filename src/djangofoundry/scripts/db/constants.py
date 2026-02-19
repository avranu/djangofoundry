import os

from djangofoundry.scripts.db.functions import get_app_dir

# Default path to the data directory, which we pass directly to postgres
DEFAULT_DATA_PATH = os.environ.get("DJANGO_FOUNDRY_DB_DATA_PATH", get_app_dir("data"))
# Default path to the logfile we want to use.
DEFAULT_LOG_PATH = os.environ.get("DJANGO_FOUNDRY_LOG_PATH", get_app_dir("logs") / "postgres.log")
# Command to use to interact with the DB. This must be in our path.
EXE = os.environ.get("DJANGO_FOUNDRY_POSTGRES_BIN", "pg_ctl")
