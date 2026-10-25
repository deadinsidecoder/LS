import secrets
import string
import html

import uvicorn
from fastapi import FastAPI, Form, Path
from fastapi.requests import Request
from fastapi.responses import HTMLResponse, RedirectResponse
import validators

import database as db




app = FastAPI()
connection = db.connect("vault.db")
generate_short = lambda: "".join(secrets.choice(string.ascii_uppercase) for _ in range(4))


@app.post("/api/links")
def add(long: str):
    if not validators.url(long):
        return {"status": "error", "message": "Invalid url"}
    if (result := db.add(connection, generate_short(), long)) is not None:
        return {"status": "success", "data": result}
    return {"status": "error", "message": "Short collision"}


@app.get("/api/links")
def get(short: str):
    if (result := db.get(connection, short)) is not None:
        return {"status": "success", "data": result}
    return {"status": "error", "message": "Not found"}


@app.post("/htmx/shorten", response_class=HTMLResponse)
def shorten(request: Request, long: str = Form(...)):
    response = add(long)
    match response:
        case {"status": "success", "data": link}:
            url = f"{request.base_url}{html.escape(link.short)}"
            return f"""<input value="{url}"> <a href="{url}"><button>Open</button></a>"""
        case {"status": "error", "message": message}:
            return f"Error: {message}"


@app.get("/", response_class=HTMLResponse)
def index():
    with open("index.html") as file:
        return file.read()


@app.get("/error", response_class=HTMLResponse)
def error():
    with open("error.html") as file:
        return file.read()
    

@app.get("/{short}", response_class=RedirectResponse)
def redirect(short: str = Path(...)):
    if (link := db.get(connection, short)) is not None:
        return link.long
    return "/error"




if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, reload=True)