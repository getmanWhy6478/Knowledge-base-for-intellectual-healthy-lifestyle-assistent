import os

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from models import SearchQuery, APIResponse
from search_engine import SearchEngine
from safety import (
    check_query_safety,
    build_api_response,
    evaluate_card_safety,
    format_safety_footer
)

search_engine: SearchEngine

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:

    global search_engine

    print("🔄 Инициализация поискового движка...")
    try:
        search_engine = SearchEngine(kb_path="knowledge_base")
        print("✅ Поисковый движок готов!")
    except Exception as e:
        print(f"❌ Ошибка инициализации поискового движка: {e}")
        search_engine = None

    yield  # Приложение работает

    # Очистка при остановке (если нужно)
    print("Остановка приложения...")

app = FastAPI(
    title="Health Lifestyle Assistant",
    version="1.0",
    description="Интеллектуальный помощник по здоровому образу жизни",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def root():
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Ошибка: index.html не найден</h1>", status_code=500)


@app.post("/api/search", response_model=APIResponse)
async def search_endpoint(query: SearchQuery):
    """Поиск по базе знаний ЗОЖ"""
    if not search_engine:
        raise HTTPException(status_code=503, detail="Search engine not initialized")
    if search_engine.validator:
        is_valid, error_msg, suggestions = search_engine.validator.validate(query.query)
        if not is_valid and error_msg:
            return APIResponse(
                success=True,
                results=[],
                message=error_msg,
                meta={"suggestions": suggestions} if suggestions else None
            )
    # 1. Проверка безопасности запроса
    safety_warning = check_query_safety(query.query)

    # 2. Если критично — возвращаем предупреждение без поиска
    if safety_warning.is_critical:
        return build_api_response([], safety_warning)

    # 3. Выполняем поиск Метод search() существует в SearchEngine
    results = search_engine.search(query)

    # 4. Формируем ответ
    return build_api_response(
        results=results,
        safety_warning=safety_warning if safety_warning.action_recommended != "none" else None,
        message=f"Найдено {len(results)} рекомендаций"
    )


@app.get("/api/card/{card_id}")
async def get_card(card_id: str):
    if not search_engine:
        raise HTTPException(status_code=503, detail="Search engine not initialized")

    card = search_engine.get_card_by_id(card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    return {
        "success": True,
        "card": card,
        "safety_note": format_safety_footer(card) if evaluate_card_safety(card) else None
    }


@app.get("/api/stats")
async def get_stats():
    if not search_engine:
        return {"total_cards": 0, "error": "Search engine not initialized"}

    return search_engine.get_statistics()

DOMAIN_TITLES: Dict[str, str] = {
    "mental": "Ментальное здоровье",
    "nutrition": "Питание",
    "sport": "Спорт",
    "global": "Общее",
}

CATEGORY_TITLES: Dict[str, str] = {
    "cross": "Междисциплинарные связи",
    "glossary": "Глоссарий",
    "ontology": "Онтология",
    "fact": "Факты",
    "myth": "Мифы",
    "partially_true": "Частично верно",
    "rule": "Правила",
    "condition": "Расстройтсва",
    "habit": "Привычки",
    "self_help": "Самопомощь",
    "technique": "Техники",
    "diet": "Диеты",
    "nutrient": "Нутриенты",
    "product": "Продукты",
    "special_groups": "Для специальных групп",
    "activity": "Занятия",
    "exercise": "Упражнения",
    "injury": "Травмы",
    "program": "Программы",
    "sports": "Виды спорта",
    "audience": "Профили аудитории"
}


@app.get("/api/browse/domains")
async def browse_domains():
    if not search_engine:
        raise HTTPException(status_code=503, detail="Search engine not initialized")

    counts: Dict[str, int] = {}
    for c in search_engine.cards:
        d = getattr(c.domain, "value", c.domain)
        counts[d] = counts.get(d, 0) + 1

    domains = [
        {"id": d, "title": DOMAIN_TITLES.get(d, d), "count": counts[d]}
        for d in sorted(counts.keys())
    ]

    return {"success": True, "domains": domains, "total": len(search_engine.cards)}


@app.get("/api/browse/domains/{domain_id}/categories")
async def browse_categories(domain_id: str):
    if not search_engine:
        raise HTTPException(status_code=503, detail="Search engine not initialized")

    domain_id = domain_id.strip().lower()
    categories_count: Dict[str, int] = {}
    for c in search_engine.cards:
        d = getattr(c.domain, "value", c.domain)
        if d != domain_id:
            continue
        cat = getattr(c.category, "value", c.category)
        categories_count[cat] = categories_count.get(cat, 0) + 1

    if not categories_count:
        raise HTTPException(status_code=404, detail="Domain not found or empty")

    categories = [
        {
            "id": cat,
            "title": CATEGORY_TITLES.get(cat, cat),
            "count": categories_count[cat],
        }
        for cat in sorted(categories_count.keys())
    ]
    return {"success": True, "domain": domain_id, "categories": categories}


@app.get("/api/browse/domains/{domain_id}/categories/{category_id}/cards")
async def browse_cards(domain_id: str, category_id: str):
    if not search_engine:
        raise HTTPException(status_code=503, detail="Search engine not initialized")

    domain_id = domain_id.strip().lower()
    category_id = category_id.strip().lower()

    cards = []
    for c in search_engine.cards:
        d = getattr(c.domain, "value", c.domain)
        cat = getattr(c.category, "value", c.category)
        if d != domain_id or cat != category_id:
            continue
        cards.append(
            {
                "id": c.id,
                "title": c.title,
                "evidence_level": getattr(c.evidence_level, "value", c.evidence_level),
                "tags": c.tags,
                "audience": [getattr(a, "value", a) for a in (c.audience or [])],
                "updated": c.date_updated.isoformat() if getattr(c, "date_updated", None) else None,
            }
        )

    if not cards:
        raise HTTPException(status_code=404, detail="No cards found for domain/category")

    cards.sort(key=lambda x: (x["title"] or "").lower())
    return {"success": True, "domain": domain_id, "category": category_id, "cards": cards, "count": len(cards)}


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "search_engine_ready": search_engine is not None,
        "cards_loaded": len(search_engine.cards) if search_engine else 0
    }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)