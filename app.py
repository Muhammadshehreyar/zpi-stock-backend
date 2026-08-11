from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS allow kar do taake frontend connect ho sake
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
    return {"symbol": symbol, "price": "Test Data"}
