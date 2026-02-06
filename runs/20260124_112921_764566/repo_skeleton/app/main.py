from fastapi import FastAPI

app = FastAPI(title="Generated MVP")

@app.get("/")
def read_root():
    return {"status": "ok"}
