import asyncio
import json
from datetime import datetime, timedelta

import requests
from fastapi import FastAPI
import aiohttp
import uuid
import redis
import xml.etree.ElementTree as ET

app = FastAPI()
db = redis.Redis(host='redis', port=6379, charset='utf-8', decode_responses=True)

COMPLETED = 'COMPLETED'
PENDING = 'PENDING'


async def update_exchange_rate():
    today_date = datetime.today().strftime('%d.%m.%Y')
    url = 'https://www.nationalbank.kz/rss/get_rates.cfm'
    response = requests.get(url, params={'fdate': today_date})
    tree = ET.fromstring(response.text)
    for item in tree.findall('item'):
        currency = item.find('title').text
        rate = item.find('description').text
        quantity = item.find('quant').text
        final_rate = float(rate) / float(quantity)
        db.set(currency, str(final_rate))
    db.set('KZT', '1')


async def call_periodic():
    while True:
        await update_exchange_rate()
        now = datetime.now()
        update_at = datetime(year=now.year, month=now.month, day=now.day, hour=12)
        if now > update_at:
            update_at = update_at + timedelta(days=1)
        await asyncio.sleep((update_at-now).seconds)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(call_periodic())

def handle_request_a(task):
    search_id = task.get_name()
    db.set(search_id+'a', COMPLETED)
    db.set(search_id+'a_result', task.result())


def handle_request_b(task):
    search_id = task.get_name()
    db.set(search_id+'b', COMPLETED)
    db.set(search_id+'b_result', task.result())


async def postponed_func(url):
    async with aiohttp.ClientSession() as session:
        async with session.post(url) as resp:
            return await resp.text()


@app.post("/search")
async def search():
    search_id = str(uuid.uuid4())
    task_a = asyncio.create_task(postponed_func('http://provider-a/search'), name=search_id)
    task_b = asyncio.create_task(postponed_func('http://provider-b/search'), name=search_id)
    task_a.add_done_callback(handle_request_a)
    task_b.add_done_callback(handle_request_b)

    return {
        "search_id": search_id
    }


@app.get("/results/{search_id}/{currency}")
async def results(search_id: str, currency: str):
    def insert_price(item):
        from_price = float(item['pricing']['total'])
        from_currency = item['pricing']['currency']
        exchange_rate_from = float(db.get(from_currency))
        exchange_rate_to = float(db.get(currency))
        final_price = from_price * exchange_rate_from / exchange_rate_to
        item['price'] = {
            "amount": str(final_price),
            "currenct": currency
        }
        return item

    status_a = db.get(search_id + 'a')
    status_b = db.get(search_id + 'b')

    result = {
        'search_id': search_id,
        'status': PENDING,
        'items': []
    }

    if status_a == COMPLETED and status_b == COMPLETED:
        a_result = json.loads(json.loads(db.get(search_id + 'a_result')))
        b_result = json.loads(json.loads(db.get(search_id + 'b_result')))
        items = a_result + b_result
        result['status'] = COMPLETED
        items = list(map(insert_price, items))
        items = sorted(items, key=lambda item: float(item['price']['amount']))
        result['items'] = items

    return result

