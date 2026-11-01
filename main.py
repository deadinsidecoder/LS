import secrets
import html
from time import ctime

import uvicorn
from fastapi import FastAPI, Form, Path, HTTPException
from fastapi.requests import Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import validators
import atexit
from jinja2 import Template

import database as db
from config import LENGTH, ALPHABET




app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static") 
connection = db.connect("vault.db")
atexit.register(connection.close)
generate_short = lambda: "".join(secrets.choice(ALPHABET) for _ in range(LENGTH))


@app.post("/api/links")
def create_link(long: str):
    if not validators.url(long):
        raise HTTPException(400, detail="Invalid url")
    if (result := db.add(connection, generate_short(), long)) is not None:
        return result
    raise HTTPException(409, detail="Short collision")


@app.get("/api/links")
def get_links(offset: int, limit: int):
    return db.fetchmany(connection, offset, limit)


@app.get("/api/links/{short}")
def get_link(short: str = Path(...)):
    if (result := db.fetchone(connection, short)) is not None:
        return result
    raise HTTPException(404, detail="Not found")


@app.post("/api/links/{short}/click")
def click_link(short: str = Path(...)):
    if (result := db.click(connection, short)) is not None:
        return result
    raise HTTPException(404, detail="Not found")


@app.post("/htmx/shorten", response_class=HTMLResponse)
def shorten(request: Request, long: str = Form(...)):
    try:
        response = create_link(long)
        url = f"{request.base_url}{html.escape(response.short)}"
        return f"""<input value="{url}"> <a href="{url}"><button>Open</button></a>"""
    except HTTPException as exception:
        return f"Error: {exception.detail}"


@app.get("/htmx/stats", response_class=HTMLResponse)
def table(request: Request, page: int):
    SIZE = 2
    template = Template("""
        {% for link in links %}
        <tr>
            <td>{{ link.id }}</td>
            <td><a href="/{{ link.short }}">{{ link.short }}</a></td>
            <td>{{ link.long }}</td>
            <td>{{ ctime(link.created_at) }}</td>
            <td>{{ link.clicks_count }}</td>
        </tr>
        {% endfor %}"""
    )
    links = get_links(page * SIZE, SIZE + 1)
    if len(links) < SIZE + 1:
        button = """<p id="page-button" hx-swap-oob="true">end of links</p>"""
    else:
        button = f"""<button id="page-button" hx-get="/htmx/stats" hx-vals='{{"page": {page + 1}}}' hx-target="#table" hx-swap="beforeend" hx-swap-oob="true">Load more</button>"""
        links = links[:-1]
    return template.render(links=links, ctime=ctime) + button



@app.get("/", response_class=HTMLResponse)
def index():
    with open("templates/index.html") as file:
        return file.read()


@app.get("/error", response_class=HTMLResponse)
def error():
    with open("templates/error.html") as file:
        return file.read()


@app.get("/stats", response_class=HTMLResponse)
def stats():
    with open("templates/stats.html") as file:
        template = Template(file.read())
    print(db.fetchmany(connection))
    return template.render()


@app.get("/{short}", response_class=RedirectResponse)
def redirect(short: str = Path(...)):
    try:
        response = click_link(short)
        return response.long
    except HTTPException:
        return "/error"




if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, reload=True)