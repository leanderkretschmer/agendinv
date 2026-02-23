import json
import subprocess
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, Form, Header, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from app.auth import (
    create_access_token,
    create_api_key,
    get_user_by_username,
    get_user_from_api_key,
    get_user_from_token,
    hash_password,
    verify_password,
)
from app.connectors import ConnectorError, SUPPORTED_PROVIDERS, fetch_provider_data
from app.db import get_session, init_db
from app.models import DataEndpoint, User
from app.schemas import EndpointCreate, LoginInput, TokenOut, UserCreate

ROOT = Path(__file__).resolve().parent.parent
app = FastAPI(title="AgendaInv Universal API", version="0.1.0")
app.mount("/static", StaticFiles(directory=ROOT / "app" / "static"), name="static")
templates = Jinja2Templates(directory=str(ROOT / "app" / "templates"))


@app.on_event("startup")
def startup_event() -> None:
    init_db()


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "message": None})


@app.post("/register", response_model=dict)
def register_user(payload: UserCreate, session: Session = Depends(get_session)):
    if get_user_by_username(session, payload.username):
        raise HTTPException(status_code=400, detail="Username existiert bereits")

    user = User(
        username=payload.username,
        hashed_password=hash_password(payload.password),
        api_key=create_api_key(),
        is_admin=payload.is_admin,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return {"id": user.id, "username": user.username, "api_key": user.api_key, "is_admin": user.is_admin}


@app.post("/login", response_model=TokenOut)
def login(payload: LoginInput, session: Session = Depends(get_session)):
    user = get_user_by_username(session, payload.username)
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Ungültige Zugangsdaten")
    return TokenOut(access_token=create_access_token(user.username))


@app.post("/web/login", response_class=HTMLResponse)
def web_login(request: Request, username: str = Form(...), password: str = Form(...), session: Session = Depends(get_session)):
    user = get_user_by_username(session, username)
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse("login.html", {"request": request, "message": "Login fehlgeschlagen"})
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie("token", create_access_token(user.username), httponly=True)
    return response


def current_web_user(request: Request, session: Session) -> User:
    token = request.cookies.get("token")
    if not token:
        raise HTTPException(status_code=401, detail="Nicht eingeloggt")
    from jose import JWTError, jwt

    try:
        payload = jwt.decode(token, "change-this-in-production", algorithms=["HS256"])
        username = payload.get("sub")
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Ungültige Session") from exc

    user = get_user_by_username(session, username)
    if not user:
        raise HTTPException(status_code=401, detail="Benutzer nicht gefunden")
    return user


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, session: Session = Depends(get_session)):
    try:
        user = current_web_user(request, session)
    except HTTPException:
        return RedirectResponse(url="/", status_code=302)

    endpoints = session.exec(select(DataEndpoint).where(DataEndpoint.owner_id == user.id)).all()
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "providers": SUPPORTED_PROVIDERS,
            "endpoints": endpoints,
            "message": None,
        },
    )


@app.post("/web/endpoints", response_class=HTMLResponse)
def create_endpoint_web(
    request: Request,
    name: str = Form(...),
    provider: str = Form(...),
    config_json: str = Form("{}"),
    session: Session = Depends(get_session),
):
    try:
        user = current_web_user(request, session)
    except HTTPException:
        return RedirectResponse(url="/", status_code=302)

    try:
        config = json.loads(config_json or "{}")
    except json.JSONDecodeError:
        endpoints = session.exec(select(DataEndpoint).where(DataEndpoint.owner_id == user.id)).all()
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "user": user,
                "providers": SUPPORTED_PROVIDERS,
                "endpoints": endpoints,
                "message": "Fehler: config_json ist kein valides JSON",
            },
        )

    endpoint = DataEndpoint(owner_id=user.id, name=name, provider=provider.lower(), config_json=json.dumps(config))
    session.add(endpoint)
    session.commit()
    return RedirectResponse(url="/dashboard", status_code=302)


@app.post("/web/admin/update", response_class=HTMLResponse)
def admin_update_app(request: Request, session: Session = Depends(get_session)):
    try:
        user = current_web_user(request, session)
    except HTTPException:
        return RedirectResponse(url="/", status_code=302)

    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Nur Admin")

    result = subprocess.run(
        ["git", "pull", "origin", "main"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    endpoints = session.exec(select(DataEndpoint).where(DataEndpoint.owner_id == user.id)).all()
    message = f"Update return code {result.returncode}: {result.stdout or result.stderr}"
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "providers": SUPPORTED_PROVIDERS,
            "endpoints": endpoints,
            "message": message,
        },
    )


@app.post("/endpoints", response_model=dict)
def create_endpoint_api(
    payload: EndpointCreate,
    user: User = Depends(get_user_from_token),
    session: Session = Depends(get_session),
):
    endpoint = DataEndpoint(
        owner_id=user.id,
        name=payload.name,
        provider=payload.provider.lower(),
        config_json=json.dumps(payload.config),
    )
    session.add(endpoint)
    session.commit()
    session.refresh(endpoint)
    return {"id": endpoint.id, "name": endpoint.name, "provider": endpoint.provider, "config": payload.config}


@app.get("/endpoints", response_model=list[dict])
def list_endpoints(user: User = Depends(get_user_from_token), session: Session = Depends(get_session)):
    endpoints = session.exec(select(DataEndpoint).where(DataEndpoint.owner_id == user.id)).all()
    return [
        {"id": ep.id, "name": ep.name, "provider": ep.provider, "config": json.loads(ep.config_json)} for ep in endpoints
    ]


@app.get("/api/universal/{endpoint_id}", response_model=dict)
def universal_data_endpoint(
    endpoint_id: int,
    x_api_key: Optional[str] = Header(default=None),
    session: Session = Depends(get_session),
):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="x-api-key Header fehlt")

    user = get_user_from_api_key(x_api_key, session)
    if not user:
        raise HTTPException(status_code=401, detail="API key ungültig")

    endpoint = session.get(DataEndpoint, endpoint_id)
    if not endpoint or endpoint.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Endpoint nicht gefunden")

    config = json.loads(endpoint.config_json)
    try:
        data = fetch_provider_data(endpoint.provider, config)
    except ConnectorError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"endpoint_id": endpoint.id, "provider": endpoint.provider, "data": data}


@app.get("/health")
def health():
    return {"status": "ok", "providers": list(SUPPORTED_PROVIDERS.keys())}
