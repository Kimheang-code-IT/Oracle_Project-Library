from db_connection import get_connection

def dump_summary():
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT
          user_id,
          COUNT(*)                          AS total_books,
          SUM(CASE WHEN days_late>0 THEN 1 ELSE 0 END) AS num_late,
          SUM(days_late)                    AS total_late_days
        FROM VW_FULL_RETURN_INFO
        GROUP BY user_id
        ORDER BY user_id
    """)
    for row in cur:
        print("SUMMARY:", row)
    cur.close()
    conn.close()

def dump_lates():
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT 
          return_id, user_id, book_title,
          days_late
        FROM VW_LATE_RETURNS
        ORDER BY return_id
    """)
    for row in cur:
        print("LATE:", row)
    cur.close()
    conn.close()

if __name__ == "__main__":
    dump_summary()
    dump_lates()
