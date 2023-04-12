import uvicorn

if __name__ == "__main__":
    uvicorn.run("configuration.server_db:app", port=9001, reload=True)


