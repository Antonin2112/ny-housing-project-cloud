from flask import Flask
from psycopg2 import connect, sql

app = Flask(__name__)

def get_db_connection():
    conn = connect(
        dbname='ny_housing',
        user='user',
        password='mdpdev',
        host='db',
        port='5432'
    )
    return conn 

@app.route('/')
def index():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM housing;')
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return f'Connected to PostgreSQL database. Number of rows in housing table: {count}'

@app.route('/stats')
def stats():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT LOCALITY, AVG(PRICE) AS moy FROM housing GROUP BY LOCALITY ORDER BY moy DESC;')
    rows = cur.fetchall()
    cur.close()
    conn.close()
    response= "<h3>Average price of housing by locality:</h3><ul>"
    for row in rows:
        response += f"<li>{row[0]}: {row[1]:.2f}</li>"
    response += "</ul>"
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)