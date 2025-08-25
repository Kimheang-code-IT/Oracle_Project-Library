# db_connection.py

import oracledb
from config import DB_USER, DB_PWD, DB_HOST, DB_PORT, DB_SERVICE

def get_connection():
    dsn = f"{DB_HOST}:{DB_PORT}/{DB_SERVICE}"

    # 🔥 NO thick mode, no init_oracle_client, no mode!
    return oracledb.connect(
        user=DB_USER,
        password=DB_PWD,
        dsn=dsn
    )
