import uvicorn

if __name__ == "__main__":
    uvicorn.run("content_analysis.main:app", host="127.0.0.1", port=8002, reload=True)