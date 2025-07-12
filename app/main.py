import os
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from bson.errors import InvalidId

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
client = AsyncIOMotorClient(MONGO_URI)
db = client["memo_db"]
memos_col = db["memos"]

class Memo(BaseModel):
    id: str = None
    title: str
    content: str
    likes: int = 0

class MemoCreate(BaseModel):
    title: str
    content: str

class MemoUpdate(BaseModel):
    title: str
    content: str

def memo_helper(memo) -> dict:
    return {
        "id": str(memo["_id"]),
        "title": memo["title"],
        "content": memo["content"],
        "likes": memo.get("likes", 0)
    }

@app.get("/memos", response_model=List[Memo])
async def get_memos():
    memos = []
    async for memo in memos_col.find():
        memos.append(memo_helper(memo))
    memos.sort(key=lambda x: x["likes"], reverse=True)
    return memos

@app.post("/memos", response_model=dict)
async def create_memo(memo: MemoCreate):
    doc = memo.dict()
    doc["likes"] = 0
    result = await memos_col.insert_one(doc)
    return {"result": "success", "id": str(result.inserted_id)}

@app.post("/memos/{id}/like", response_model=dict)
async def like_memo(id: str):
    try:
        obj_id = ObjectId(id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="잘못된 id 형식입니다.")
    memo = await memos_col.find_one({"_id": obj_id})
    if not memo:
        raise HTTPException(status_code=404, detail="메모를 찾을 수 없습니다.")
    new_likes = memo.get("likes", 0) + 1
    await memos_col.update_one({"_id": obj_id}, {"$set": {"likes": new_likes}})
    return {"result": "success", "likes": new_likes}

@app.delete("/memos/{id}", response_model=dict)
async def delete_memo(id: str):
    try:
        obj_id = ObjectId(id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="잘못된 id 형식입니다.")
    result = await memos_col.delete_one({"_id": obj_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="메모를 찾을 수 없습니다.")
    return {"result": "success"}

@app.put("/memos/{id}", response_model=dict)
async def update_memo(id: str, memo: MemoUpdate):
    try:
        obj_id = ObjectId(id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="잘못된 id 형식입니다.")
    result = await memos_col.update_one(
        {"_id": obj_id},
        {"$set": {"title": memo.title, "content": memo.content}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="메모를 찾을 수 없습니다.")
    return {"result": "success"}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
static_path = os.path.join(BASE_DIR, "static")
app.mount("/static", StaticFiles(directory=static_path, html=True), name="static")

@app.get("/")
async def root():
    return FileResponse(os.path.join(static_path, "index.html"))
