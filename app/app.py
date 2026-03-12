import os 
from flask import Flask, request
from psycopg2 import connect, sql

app = Flask(__name__)

def get_db_connection():
    conn = connect(
        dbname=os.environ['POSTGRES_DB'],
        user=os.environ['POSTGRES_USER'],
        password=os.environ['POSTGRES_PASSWORD'],
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
        conn.close()

    result = f"<h3>Houses in {locality}</h3><ul>"
    for r in rows:
        result += f"<li>{r[0]} — ${r[1]:,.0f} | {r[2]}bd {r[3]}ba | {r[4]}sqft</li>"
    result += "</ul>"
    return result

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)