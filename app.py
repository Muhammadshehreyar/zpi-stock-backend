from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf

app = FastAPI()

# CORS allow
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "ZPI Backend is Running ✅"}

@app.get("/stocks/{symbol}")
def get_stock(symbol: str):
    try:
        stock = yf.Ticker(symbol)
        data = stock.info
        price = data.get('currentPrice', data.get('regularMarketPrice', 0))
        name = data.get('shortName', symbol)
        
        return {
            "symbol": symbol.upper(),
            "name": name,
            "price": price,
            "currency": data.get('currency', 'USD')
        }
    except:
        return {"error": "Stock not found"}
