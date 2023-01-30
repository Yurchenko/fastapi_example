from fastapi import FastAPI, HTTPException
import asyncio

app = FastAPI()


@app.post("/search")
async def search():
    # await asyncio.sleep(60)

    try:
        with open("response_b.json") as f:
            data = f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="response_b.json not found")
    except:
        raise HTTPException(status_code=500, detail="An error occurred while reading the file")

    return data

