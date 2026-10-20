import uvicorn
from fastapi import FastAPI, Request, Form, Path
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import atexit
from pydantic import AnyUrl, TypeAdapter, ValidationError

from database import DBManager, GenerationError, NotFoundError




app = FastAPI()
templates = Jinja2Templates("templates")
dbmanager = DBManager("database.sqlite3")

app.mount("/static", StaticFiles(directory="static"), name="style.css")
atexit.register(dbmanager.close)




@app.get("/json/urls")
def get(short: str):
    try:
        record = dbmanager.get(short)
        return {"status": "success", "data": record}
    except NotFoundError:
        return {"status": "error", "message": "not found"}


@app.post("/json/urls")
def add(long: str):
    try:
        TypeAdapter(AnyUrl).validate_strings(long)
        record = dbmanager.add(long)
        return {"status": "success", "data": record}
    except ValidationError:
        return {"status": "error", "message": "invalid URL"}
    except GenerationError:
        return {"status": "error", "message": "generation error"}


@app.post("/htmx/urls", response_class=HTMLResponse)
def htmx_add(request: Request, long: str = Form(...)):
    response = add(long)
    if response["status"] == "success":
        record = response["data"]
        return "".join([
            templates.get_template("components/result.html").render(short=f"{request.base_url}{record.short}"),
            f'<input id="long-url" class="nes-input" name="long" hx-swap-oob="true" value="{long}">',
        ])
    return "".join([
        templates.get_template("components/error.html").render(message=response["message"]),
        f'<input id="long-url" class="nes-input is-error" hx-get="/htmx/retry" hx-trigger="input once" name="long" hx-swap-oob="true" value="{long}">'
    ])


@app.get("/htmx/retry", response_class=HTMLResponse)
def htmx_retry(long: str):
    return f'<input id="long-url" class="nes-input" name="long" hx-swap-oob="true" value="{long}">'


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"form": templates.get_template("components/form.html").render()}
    )


@app.get("/stats")
def stats():
    return dbmanager.connection.execute("SELECT * FROM urls").fetchall()


@app.get("/{short}")
def get_url(request: Request, short: str = Path(...)):
    response = get(short)
    if response["status"] == "success":
        record = response["data"]
        return RedirectResponse(record.long, status_code=302)
    return templates.TemplateResponse(request, "notfound.html")




if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, reload=True)