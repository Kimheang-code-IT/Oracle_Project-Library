# config.py

import os

# Credentials
DB_USER = os.getenv("DB_USER", "library")
DB_PWD  = os.getenv("DB_PWD",  "123")

# Network location
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 1521))

# This must be your _service_ name (not SID), e.g. XE, XEPDB1, ORCLPDB1
DB_SERVICE = os.getenv("DB_SERVICE", "free")

