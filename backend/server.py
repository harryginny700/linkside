from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import UpdateOne
import os
import logging
import uuid
import jwt
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

JWT_SECRET = os.environ.get('JWT_SECRET', 'dev_secret')
JWT_ALGO = 'HS256'
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

app = FastAPI()
api_router = APIRouter(prefix="/api")
security = HTTPBearer()


# ----------------- Models -----------------
class LoginIn(BaseModel):
    username: str
    password: str


class Banner(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    section: str = "grid"          # top | grid
    image: str = ""
    url: str = ""
    title: str = ""
    orient: str = "square"         # square | wide | tall
    span: int = 1
    order: int = 0
    active: bool = True
    clicks: int = 0
    badge: str = ""                # köşe rozeti (örn. ZİRVE)
    headline: str = ""             # büyük başlık (örn. 3000₺ NAKİT DENEME BONUSU)
    description: str = ""          # alt açıklama (örn. SINIRSIZ ANLIK ÇEKİM İMKANI)
    ctaText: str = ""              # CTA metni (örn. TIKLA KAYIT OL)
    accent: str = ""               # tema rengi hex (boşsa otomatik palet)


class BannerIn(BaseModel):
    section: str = "grid"
    image: str = ""
    url: str = ""
    title: str = ""
    orient: str = "square"
    span: int = 1
    active: bool = True
    badge: str = ""
    headline: str = ""
    description: str = ""
    ctaText: str = ""
    accent: str = ""


class ReorderIn(BaseModel):
    ids: List[str]


class TickerItem(BaseModel):
    text: str = ""
    color: str = "#22d3ee"


DEFAULT_TICKER = [
    {"text": "YENİ ÜYELERE %200 HOŞ GELDİN BONUSU", "color": "#22d3ee"},
    {"text": "ANINDA PARA ÇEKİM GARANTİSİ", "color": "#f5b81c"},
    {"text": "GÜNCEL GİRİŞ ADRESLERİ 7/24 GÜNCELLENİR", "color": "#3b82f6"},
]


class Settings(BaseModel):
    siteTitle: str = "Emre18 — Güncel Giriş"
    brandName: str = "EMRE18"
    headerTitle: str = "EMRE18"
    headerSubtitle: str = "GÜNCEL GİRİŞ VE REKLAM ALANLARI"
    statusLabel: str = "GÜNCEL"
    tickerItems: List[TickerItem] = DEFAULT_TICKER
    footerText: str = "© 2026 EMRE18 — 18+: SORUMLU REKLAM YAYINCILIĞI"
    footerDomains: str = "emre18.com"
    logoSize: int = 36
    gridColumns: int = 3
    ageGateEnabled: bool = False


# ----------------- Auth helpers -----------------
def create_token(username: str) -> str:
    payload = {
        "sub": username,
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)


async def get_current_user(cred: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(cred.credentials, JWT_SECRET, algorithms=[JWT_ALGO])
        return payload.get("sub")
    except Exception:
        raise HTTPException(status_code=401, detail="Gecersiz veya suresi dolmus oturum")


def clean(doc: dict) -> dict:
    doc.pop("_id", None)
    return doc


# ----------------- Auth routes -----------------
@api_router.post("/auth/login")
async def login(data: LoginIn):
    user = await db.admin_users.find_one({"username": data.username})
    if not user or not pwd_context.verify(data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Kullanici adi veya sifre hatali")
    return {"token": create_token(data.username), "username": data.username}


@api_router.get("/auth/me")
async def me(username: str = Depends(get_current_user)):
    return {"username": username}


# ----------------- Banner routes -----------------
@api_router.get("/banners")
async def get_banners(all: bool = False):
    query = {} if all else {"active": True}
    banners = await db.banners.find(query).sort("order", 1).to_list(1000)
    return [clean(b) for b in banners]


@api_router.post("/banners")
async def create_banner(data: BannerIn, username: str = Depends(get_current_user)):
    banners = await db.banners.find({}, {"order": 1}).sort("order", -1).to_list(1)
    max_order = banners[0]["order"] if banners else 0
    b = Banner(**data.dict(), order=max_order + 1)
    await db.banners.insert_one(b.dict())
    return b.dict()


@api_router.put("/banners/{banner_id}")
async def update_banner(banner_id: str, data: dict, username: str = Depends(get_current_user)):
    data.pop("id", None)
    data.pop("_id", None)
    res = await db.banners.update_one({"id": banner_id}, {"$set": data})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Banner bulunamadi")
    doc = await db.banners.find_one({"id": banner_id})
    return clean(doc)


@api_router.delete("/banners/{banner_id}")
async def delete_banner(banner_id: str, username: str = Depends(get_current_user)):
    await db.banners.delete_one({"id": banner_id})
    return {"ok": True}


@api_router.post("/banners/reorder")
async def reorder(data: ReorderIn, username: str = Depends(get_current_user)):
    if data.ids:
        ops = [UpdateOne({"id": bid}, {"$set": {"order": i}}) for i, bid in enumerate(data.ids)]
        await db.banners.bulk_write(ops)
    return {"ok": True}


@api_router.post("/banners/{banner_id}/click")
async def click_banner(banner_id: str):
    await db.banners.update_one({"id": banner_id}, {"$inc": {"clicks": 1}})
    await _bump_daily("clicks")
    return {"ok": True}


# ----------------- Settings -----------------
@api_router.get("/settings")
async def get_settings():
    s = await db.settings.find_one({"_id": "singleton"})
    if not s:
        default = Settings().dict()
        default["_id"] = "singleton"
        default["totalViews"] = 0
        await db.settings.insert_one(default)
        s = default
    # Eski kayıtlarda eksik alanları varsayılanlarla tamamla
    merged = Settings().dict()
    merged.update({k: v for k, v in s.items() if k != "_id"})
    return clean(merged)


@api_router.put("/settings")
async def update_settings(data: dict, username: str = Depends(get_current_user)):
    data.pop("_id", None)
    # Sayısal alanları zorla (yanlış tip gelirse düzelt/at)
    if "logoSize" in data:
        try:
            data["logoSize"] = max(16, min(140, int(float(data["logoSize"]))))
        except (TypeError, ValueError):
            data.pop("logoSize")
    if "gridColumns" in data:
        try:
            data["gridColumns"] = max(1, min(6, int(float(data["gridColumns"]))))
        except (TypeError, ValueError):
            data.pop("gridColumns")
    await db.settings.update_one({"_id": "singleton"}, {"$set": data}, upsert=True)
    s = await db.settings.find_one({"_id": "singleton"})
    merged = Settings().dict()
    merged.update({k: v for k, v in s.items() if k != "_id"})
    return clean(merged)


# ----------------- Views & Stats -----------------
def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


async def _bump_daily(field: str):
    await db.daily_stats.update_one(
        {"date": _today()},
        {"$inc": {field: 1}, "$setOnInsert": {"date": _today()}},
        upsert=True,
    )


@api_router.post("/view")
async def record_view():
    await _bump_daily("views")
    await db.settings.update_one({"_id": "singleton"}, {"$inc": {"totalViews": 1}}, upsert=True)
    return {"ok": True}


@api_router.get("/stats/overview")
async def stats_overview(username: str = Depends(get_current_user)):
    banners = await db.banners.find({}, {"clicks": 1, "active": 1}).to_list(1000)
    total_clicks = sum(b.get("clicks", 0) for b in banners)
    active = sum(1 for b in banners if b.get("active"))
    daily = await db.daily_stats.find({}, {"views": 1}).to_list(1000)
    total_views = sum(d.get("views", 0) for d in daily)
    ctr = round((total_clicks / total_views * 100), 1) if total_views else 0
    return {
        "totalViews": total_views,
        "totalClicks": total_clicks,
        "activeBanners": active,
        "ctr": ctr,
    }


@api_router.get("/stats/daily")
async def stats_daily(username: str = Depends(get_current_user)):
    out = []
    today = datetime.now(timezone.utc)
    for i in range(13, -1, -1):
        d = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        row = await db.daily_stats.find_one({"date": d})
        out.append({
            "date": d[5:],
            "views": row.get("views", 0) if row else 0,
            "clicks": row.get("clicks", 0) if row else 0,
        })
    return out


# ----------------- Upload -----------------
@api_router.post("/upload")
async def upload(file: UploadFile = File(...), username: str = Depends(get_current_user)):
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Dosya cok buyuk (maks 5MB)")
    if (file.content_type or "") and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Sadece gorsel dosyalari yuklenebilir")
    ext = Path(file.filename or "").suffix[:8].lower() or ".png"
    if not ext.lstrip(".").isalnum():
        ext = ".png"
    doc = {
        "id": str(uuid.uuid4()) + ext,
        "content_type": file.content_type or "image/png",
        "data": content,
    }
    await db.uploads.insert_one(doc)
    return {"url": f"/api/uploads/{doc['id']}"}


@api_router.get("/uploads/{name}")
async def serve_upload(name: str):
    doc = await db.uploads.find_one({"id": name})
    if not doc:
        raise HTTPException(status_code=404, detail="Dosya bulunamadi")
    return Response(content=bytes(doc["data"]), media_type=doc.get("content_type", "image/png"))


@api_router.get("/")
async def root():
    return {"message": "Reklam API"}


# ----------------- Startup seed -----------------
SEED_BANNERS = [
    {"section": "top", "image": "https://kara8.com/uploads/banners/6a861dbf85213.jpg", "url": "https://sloganbahis.click/?refId=39", "title": "SloganBahis 8000TL", "orient": "wide", "span": 2, "order": 0, "active": True, "clicks": 1284},
    {"section": "grid", "image": "https://kara8.com/uploads/bonus_cards/6a861d9e2fcb1.png", "url": "https://sloganbahis.click/?refId=39", "title": "SloganBahis 8.000TL Nakit", "orient": "square", "span": 1, "order": 1, "active": True, "clicks": 642},
    {"section": "grid", "image": "https://kara8.com/uploads/bonus_cards/6a6788c39b25c.jpg", "url": "https://jiletbahisaffiliate.com/redirect-1/fici-aff", "title": "JiletBahis 20 Bin Yatir", "orient": "square", "span": 1, "order": 2, "active": True, "clicks": 531},
    {"section": "grid", "image": "https://kara8.com/uploads/bonus_cards/6a5f512316d09.png", "url": "https://kisal.site/padisah", "title": "MilanBahis 3.000TL Deneme", "orient": "square", "span": 1, "order": 3, "active": True, "clicks": 418},
    {"section": "grid", "image": "https://kara8.com/uploads/bonus_cards/6a8cb64dc0b3d.jpg", "url": "https://t2m.co/padiisah", "title": "HerkulBet 3000TL Deneme", "orient": "square", "span": 1, "order": 4, "active": True, "clicks": 377},
]


@app.on_event("startup")
async def seed():
    if await db.admin_users.count_documents({}) == 0:
        await db.admin_users.insert_one({
            "username": "admin",
            "password": pwd_context.hash("admin123"),
        })
    if await db.banners.count_documents({}) == 0:
        for b in SEED_BANNERS:
            await db.banners.insert_one(Banner(**b).dict())
    if await db.settings.find_one({"_id": "singleton"}) is None:
        s = Settings().dict()
        s["_id"] = "singleton"
        s["totalViews"] = 0
        await db.settings.insert_one(s)
    import random
    if await db.daily_stats.count_documents({}) == 0:
        today = datetime.now(timezone.utc)
        for i in range(13, -1, -1):
            d = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            await db.daily_stats.insert_one({
                "date": d,
                "views": random.randint(200, 700),
                "clicks": random.randint(80, 340),
            })


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
