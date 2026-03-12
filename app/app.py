import os 
from flask import Flask, request
from psycopg2 import pool 
from psycopg2 import connect, sql

app = Flask(__name__)

connection_pool = pool.SimpleConnectionPool(
    minconn=2,   # connexions ouvertes dès le départ
    maxconn=10,  # maximum de connexions simultanées vers PG
    dbname=os.environ.get('POSTGRES_DB'),
    user=os.environ.get('POSTGRES_USER'),
    password=os.environ.get('POSTGRES_PASSWORD'),
    host='db',
    port='5432'
)
def get_db_connection():
    return connection_pool.getconn()

def release_connection(conn):
    connection_pool.putconn(conn)


@app.route('/')
def index():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM housing;')
        count = cur.fetchone()[0]
        cur.close()
    finally:
        release_connection(conn)
    return f'Connected to PostgreSQL database. Number of rows in housing table: {count}'

@app.route('/stats')
def stats():
    conn = get_db_connection()
    try: 
        cur = conn.cursor()
        cur.execute('SELECT LOCALITY, AVG(PRICE) AS moy FROM housing GROUP BY LOCALITY ORDER BY moy DESC;')
        rows = cur.fetchall()
        cur.close()
    finally:
        release_connection(conn)
    response= "<h3>Average price of housing by locality:</h3><ul>"
    for row in rows:
        response += f"<li>{row[0]}: {row[1]:.2f}</li>"
    response += "</ul>"
    return response

@app.route('/houses')
def houses():
    locality = request.args.get('locality', 'New York')
    limit    = request.args.get('limit', 20, type=int)

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('''
            SELECT LOCALITY, PRICE, BEDS, BATH, PROPERTYSQFT
            FROM housing
            WHERE LOCALITY = %s
            ORDER BY PRICE DESC
            LIMIT %s;
        ''', (locality, limit))
        rows = cur.fetchall()
        cur.close()
    finally:
        release_connection(conn)

    result = f"<h3>Houses in {locality}</h3><ul>"
    for r in rows:
        result += f"<li>{r[0]} — ${r[1]:,.0f} | {r[2]}bd {r[3]}ba | {r[4]}sqft</li>"
    result += "</ul>"
    return result

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)