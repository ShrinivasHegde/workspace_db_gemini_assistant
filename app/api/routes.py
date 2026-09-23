from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Response, status

from app.db.history import HistoryStore
from app.db.schema_extractor import extract_schema
from app.exceptions import AppError
from app.models.schemas import ChatResponse, MessageCreate, SchemaResponse, SessionCreate, SessionResponse
from app.services.gemini import answer_question


def build_router(store: HistoryStore) -> APIRouter:
    router = APIRouter(prefix="/api")

    @router.get("/health")
    def health():
        return {"status": "ok"}

    @router.get("/schema", response_model=SchemaResponse)
    def schema():
        try:
            return {"content": extract_schema(), "synced_at": datetime.now(timezone.utc)}
        except AppError as error:
            raise HTTPException(status_code=503, detail=str(error)) from error

    @router.get("/sessions", response_model=list[SessionResponse])
    def list_sessions():
        return store.list_sessions()

    @router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
    def create_session(payload: SessionCreate):
        return store.create_session(payload.title)

    @router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_session(session_id: str):
        if not store.delete_session(session_id):
            raise HTTPException(status_code=404, detail="Chat session not found.")
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @router.get("/sessions/{session_id}/messages")
    def session_messages(session_id: str):
        if not store.get_session(session_id):
            raise HTTPException(status_code=404, detail="Chat session not found.")
        return store.messages(session_id)

    @router.post("/sessions/{session_id}/messages", response_model=ChatResponse)
    def chat(session_id: str, payload: MessageCreate):
        if not store.get_session(session_id):
            raise HTTPException(status_code=404, detail="Chat session not found.")
        try:
            schema = extract_schema()
            history = store.messages(session_id)
            user_message = store.add_message(session_id, "user", payload.content)
            answer = answer_question(schema, history, payload.content)
            assistant_message = store.add_message(session_id, "assistant", answer)
            return {"user_message": user_message, "assistant_message": assistant_message}
        except AppError as error:
            raise HTTPException(status_code=503, detail=str(error)) from error

    return router
