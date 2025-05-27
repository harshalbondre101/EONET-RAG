from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from ollamahelper import get_response

app = FastAPI()

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    print("Received a GET request at root endpoint")
    return templates.TemplateResponse(
        request=request, name="index.html"
    )

@app.post("/", response_class=HTMLResponse)
async def post_root(request: Request):
    form_data = await request.form()
    user_input = form_data.get("query", "")
    
    print(f"Received POST request with user input: {user_input}")
    response = get_response(user_input)

    return templates.TemplateResponse(
        request=request, name="index.html", context={"response": response}
    )


