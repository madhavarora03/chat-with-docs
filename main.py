from fastapi import FastAPI

app = FastAPI(
    title="Check Karo Baabeyo!",
    description="This is a description",
    version="1.0.0",
)


@app.get("/")
def root():
    return {"message": "Hello World"}


if __name__ == "__main__":
    import os
    import uvicorn

    uvicorn.run(
        app="main:app", host="0.0.0.0", port=8000, reload=os.getenv("ENV") == "dev"
    )
