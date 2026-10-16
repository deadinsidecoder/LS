import uvicorn
from fastapi import FastAPI, Request, Form, Path
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import atexit

from database import DBManager




app = FastAPI()
templates = Jinja2Templates("templates")
dbmanager = DBManager("database.sqlite3")

app.mount("/static", StaticFiles(directory="static"), name="style.css")
atexit.register(dbmanager.close)




@app.post("/htmx/urls", response_class=HTMLResponse)
def add(request: Request, long: str = Form(...)):
    if not long.startswith(("http://", "https://")):
        return templates.get_template("components/error.html").render()
    try:
        short = dbmanager.add(long)
        return templates.get_template("components/result.html").render(short=f"{request.base_url}{short}")
    except Exception:
        return templates.get_template("components/error.html").render()


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
    long = dbmanager.get(short)
    if long is not None:
        return RedirectResponse(long, status_code=302)
    return templates.TemplateResponse(request, "notfound.html")




if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, reload=True)