from fastapi import FastAPI, Request, Depends, HTTPException, status, Form, UploadFile, File, Body, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse
from pydantic import BaseModel
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
import gridfs
import base64
import codecs
from typing import List
from starlette.middleware.sessions import SessionMiddleware
from pymongo import MongoClient
client = MongoClient()
mydb = client["BetterIndia"]
users = mydb["users"]
issues = mydb["issues"]
grid_fs = gridfs.GridFS(mydb)

app = FastAPI()
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import JSONResponse
from secrets import token_hex

SECRET_KEY = token_hex(32)  # Generate a random secret key
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

def flash(response: Response, message: str, category: str = 'message'):
    """
    Store a flash message in cookies. For demonstration purposes only.
    In production, consider using a more secure storage method.
    """
    messages = json.dumps({'category': category, 'message': message})
    response.set_cookie(key="flash_messages", value=messages, httponly=True)

def get_flashed_messages(request: Request):
    """
    Retrieve flash messages from cookies. For demonstration purposes only.
    In production, consider using a more secure storage method.
    """
    messages = request.cookies.get("flash_messages", None)
    if messages:
        try:
            messages = json.loads(messages)
            return [messages]  # Return as a list for compatibility
        except json.JSONDecodeError:
            pass
    return []

@app.get("/example", response_class=HTMLResponse)
async def example(request: Request, response: Response):
    """
    Example endpoint that flashes a message and redirects to the main page.
    """
    flash(response, "This is a test flash message.", "success")
    # Simulate a redirect to the main page
    return "Message flashed. <a href='/'>Go to the main page</a> to see it."

@app.get("/", response_class=HTMLResponse)
async def main(request: Request, response: Response):
    """
    Main page that displays flashed messages, if any.
    """
    # Retrieve flash messages
    messages = get_flashed_messages(request)
    response.delete_cookie("flash_messages")  # Clear the flash cookie
    # Simulate rendering a template with messages
    if messages:
        return f"Flash message: {messages[0]['message']} with category: {messages[0]['category']}"
    return "No flash messages."

@app.get("/home")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/about_us")
async def about_us(request: Request):
    return templates.TemplateResponse("aboutus.html", {"request": request})


class LoginForm(BaseModel):
    email: str
    password: str


@app.get("/login")
async def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
async def login_post(request: Request, form_data: LoginForm = Body(...)):
    if users.find_one({'email': form_data.email}):
        if check_password_hash(users.find_one({'email': form_data.email})['password'], form_data.password):
            request.session['name'] = users.find_one({'email': form_data.email})['name']
            request.session['email'] = form_data.email
            return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
        else:
            return templates.TemplateResponse("login.html", {"request": request, "error": "Incorrect Password"})
    else:
        return RedirectResponse(url="/register", status_code=status.HTTP_302_FOUND)


class RegisterForm(BaseModel):
    name: str
    phone_number: str
    email: str
    password: str


@app.get("/register")
async def register_get(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.post("/register")
async def register_post(request: Request, form_data: RegisterForm = Body(...)):
    if users.find_one({'email': form_data.email}):
        return templates.TemplateResponse("register.html", {"request": request, "error": "Email Already Exists"})
    else:
        password = generate_password_hash(form_data.password)
        users.insert_one({'name': form_data.name, 'phone_number': form_data.phone_number,
                          'email': form_data.email, 'password': password})
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)


@app.get("/logout")
async def logout(request: Request):
    request.session.pop('name', None)
    request.session.pop('email', None)
    return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)


class AddIssueForm(BaseModel):
    title: str
    location: str
    date: str
    details: str
    image: UploadFile = File(...)


@app.get("/addissue")
async def add_issue_get(request: Request):
    if not request.session.get('name'):
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("addissue.html", {"request": request})


@app.post("/addissue")
async def add_issue_post(request: Request, form_data: AddIssueForm = Body(...)):
    if not request.session.get('name'):
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    if issues.find_one({'title': form_data.title, 'location': form_data.location, 'date': form_data.date,
                        'details': form_data.details, 'name': request.session.get('name'),
                        'email': request.session.get('email')}):
        return templates.TemplateResponse("addissue.html", {"request": request, "error": "Issue Already Exists"})

    status = "Open"
    upvote = list()
    messages = list()

    with grid_fs.new_file(filename=form_data.image.filename) as fp:
        fp.write(form_data.image.file.read())
    file_id = fp._id
    grid_fs_file = grid_fs.find_one({'filename': form_data.image.filename})
    base64_data = codecs.encode(grid_fs_file.read(), 'base64')
    imagedata = base64_data.decode('utf-8')

    if grid_fs.find_one(file_id) is not None:
        issues.insert_one({'title': form_data.title, 'location': form_data.location,
                           'date': form_data.date, 'details': form_data.details,
                           'name': request.session.get('name'), 'email': request.session.get('email'), 'status': status,
                           'upvote': upvote, 'messages': messages, 'imageid': file_id,
                           'imagedata': imagedata})
        return RedirectResponse(url="/issues", status_code=status.HTTP_302_FOUND)
    else:
        return templates.TemplateResponse("addissue.html", {"request": request, "error": "Error in Adding Image"})


@app.get("/issues")
async def all_issues(request: Request):
    if not request.session.get('name'):
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    infos = list(issues.find({}))
    return templates.TemplateResponse("issues.html", {"request": request, "infos": infos})


class EditIssueForm(BaseModel):
    title: str
    location: str
    date: str
    details: str
    image: UploadFile = File(...)


@app.get("/editissue/{idx}")
async def edit_issue_get(request: Request, idx: str):
    if not request.session.get('name'):
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    data = issues.find_one({'_id': ObjectId(idx)})
    return templates.TemplateResponse("editissue.html", {"request": request, "data": data})


@app.post("/editissue/{idx}")
async def edit_issue_post(request: Request, idx: str, form_data: EditIssueForm = Body(...)):
    if not request.session.get('name'):
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    with grid_fs.new_file(filename=form_data.image.filename) as fp:
        fp.write(form_data.image.file.read())
    file_id = fp._id
    grid_fs_file = grid_fs.find_one({'filename': form_data.image.filename})
    base64_data = codecs.encode(grid_fs_file.read(), 'base64')
    imagedata = base64_data.decode('utf-8')

    if grid_fs.find_one(file_id) is not None:
        issues.find_one_and_update({'_id': ObjectId(idx)}, {
            "$set": {'title': form_data.title, 'location': form_data.location,
                     'date': form_data.date, 'details': form_data.details,
                     'name': request.session.get('name'), 'email': request.session.get('email'), 'imageid': file_id,
                     'imagedata': imagedata}})
        return RedirectResponse(url="/issues", status_code=status.HTTP_302_FOUND)


@app.get("/deleteissue/{idx}")
async def delete_issue(request: Request, idx: str):
    if not request.session.get('name'):
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    issues.delete_one({'_id': ObjectId(idx)})
    return RedirectResponse(url="/myissues", status_code=status.HTTP_302_FOUND)


@app.get("/myissues")
async def my_issues(request: Request):
    # if not request.session.get('name'):
    #     return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    # infos = list(issues.find({'name': request.session.get('name'), 'email': request.session.get('email')}))
    return templates.TemplateResponse("myissues.html", {"request": request})


@app.get("/issues/{idx}/messages")
async def messages(request: Request, idx: str):
    if not request.session.get('name'):
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    data = issues.find_one({'_id': ObjectId(idx)})
    return templates.TemplateResponse("message.html", {"request": request, "data": data})


class AddMessageForm(BaseModel):
    comment: str


@app.post("/issues/{idx}/messages/add")
async def add_message(request: Request, idx: str, form_data: AddMessageForm = Body(...)):
    if not request.session.get('name'):
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    if idx is None:
        return RedirectResponse(url="/issues", status_code=status.HTTP_302_FOUND)

    message = {'name': request.session.get('name'), 'comment': form_data.comment}
    issues.update_one({'_id': ObjectId(idx)}, {"$push": {'messages': message}})
    return RedirectResponse(url=f"/issues/{idx}/messages", status_code=status.HTTP_302_FOUND)


@app.get("/upvote/{idx}")
async def upvote(request: Request, idx: str):
    if not request.session.get('name'):
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    upvote_data = {'name': request.session.get('name'), 'email': request.session.get('email')}
    issues.update_one({'_id': ObjectId(idx)}, {"$addToSet": {'upvote': upvote_data}})
    return RedirectResponse(url="/issues", status_code=status.HTTP_302_FOUND)


class UpdateStatusForm(BaseModel):
    status: str


@app.get("/issues/{idx}/updatestatus")
async def update_status_get(request: Request, idx: str):
    if not request.session.get('name'):
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    data = issues.find_one({'_id': ObjectId(idx)})
    return templates.TemplateResponse("update_status.html", {"request": request, "data": data})


@app.post("/issues/{idx}/updatestatus")
async def update_status_post(request: Request, idx: str, form_data: UpdateStatusForm = Body(...)):
    if not request.session.get('name'):
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    issues.update_one({'_id': ObjectId(idx)}, {"$set": {'status': form_data.status}})
    return RedirectResponse(url="/issues", status_code=status.HTTP_302_FOUND)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)