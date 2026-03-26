import os
import asyncpg
import redis.asyncio as aioredis
from contextlib import asynccontextmanager
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse

CACHE_TTL = 60  # secondes


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup : création du pool asyncpg et du client Redis async
    app.state.db_pool = await asyncpg.create_pool(
        database=os.environ.get('POSTGRES_DB'),
        user=os.environ.get('POSTGRES_USER'),
        password=os.environ.get('POSTGRES_PASSWORD'),
        host='db',
        port=5432,
        min_size=10,
        max_size=10,
        command_timeout=5.0
    )
    app.state.redis = aioredis.Redis(host='redis', port=6379, decode_responses=True)
    yield
    # Shutdown : fermeture propre des connexions
    await app.state.db_pool.close()
    await app.state.redis.aclose()


app = FastAPI(lifespan=lifespan)


@app.get('/')
async def index():
    async with app.state.db_pool.acquire() as conn:
        count = await conn.fetchval('SELECT COUNT(*) FROM housing;')
    return HTMLResponse(f'Connected to PostgreSQL database. Number of rows in housing table: {count}')


@app.get('/stats')
async def stats():
    # on cherche d'abord dans le cache Redis
    cached = await app.state.redis.get('cache:stats')
    if cached:
        return HTMLResponse(cached)

    # sinon on interroge PostgreSQL
    async with app.state.db_pool.acquire() as conn:
        rows = await conn.fetch(
            'SELECT LOCALITY, AVG(PRICE) AS moy FROM housing GROUP BY LOCALITY ORDER BY moy DESC;'
        )

    response = "<h3>Average price of housing by locality:</h3><ul>"
    for row in rows:
        response += f"<li>{row['locality']}: {row['moy']:.2f}</li>"
    response += "</ul>"

    await app.state.redis.setex('cache:stats', CACHE_TTL, response)
    return HTMLResponse(response)


@app.get('/houses')
async def houses(
    locality: str = Query(default='New York'),
    limit: int = Query(default=20),
):  
    
    cache_key = f"cache:houses:{locality}:{limit}"

    # Chercher d'abord dans le cache Redis
    cached = await app.state.redis.get(cache_key)
    if cached:
        return HTMLResponse(cached)
    
    async with app.state.db_pool.acquire() as conn:
        rows = await conn.fetch(
            '''
            SELECT LOCALITY, PRICE, BEDS, BATH, PROPERTYSQFT
            FROM housing
            WHERE LOCALITY = $1
            ORDER BY PRICE DESC
            LIMIT $2;
            ''',
            locality,
            limit,
        )

    result = f"<h3>Houses in {locality}</h3><ul>"
    for r in rows:
        result += f"<li>{r['locality']} — ${r['price']:,.0f} | {r['beds']}bd {r['bath']}ba | {r['propertysqft']}sqft</li>"
    result += "</ul>"

    await app.state.redis.setex(cache_key, CACHE_TTL, result)
    
    return HTMLResponse(result)
