"""
Модуль безопасности: фильтрация опасных запросов и маркировка чувствительного контента.
"""

from typing import List, Optional
from models import KnowledgeCard, SafetyWarning, APIResponse

# =============================================================================
# ТРИГГЕРЫ БЕЗОПАСНОСТИ
# =============================================================================

# 🔴 Критические симптомы — требуют немедленного обращения к врачу
CRITICAL_SYMPTOMS = [
    # Сердечно-сосудистые
    "боль в груди", "давящая боль", "сердцебиение", "перебои в сердце",
    "онемение руки", "боль отдает в челюсть",

    # Неврологические
    "потеря сознания", "судороги", "паралич", "нарушение речи",
    "внезапная головная боль", "двоение в глазах",

    # Дыхательные
    "одышка в покое", "удушье", "синюшность", "кровь в мокроте",

    # ЖКТ и общее
    "рвота с кровью", "чёрный стул", "острая боль в животе",
    "высокая температура", "температура выше 39", "не сбивается температура",

    # Психическое здоровье
    "суицид", "хочу умереть", "паническая атака", "не могу дышать от страха",
    "слышу голоса", "теряю связь с реальностью",

    # Травмы
    "сильное кровотечение", "открытый перелом", "травма головы", "ожог"
]

# 🟡 Предупреждения — требуют осторожности и консультации специалиста
CAUTION_KEYWORDS = [
    "беремен", "кормл", "ребёнк", "дет", "подрост",
    "хроническ", "диабет", "гипертон", "астм", "аллерг",
    "лекарств", "препарат", "таблетк", "противопоказ",
    "операци", "восстановл", "реабилитаци",
    "похуд", "диет", "голод", "детокс", "очищени"
]

# 🟢 Контексты, где важно подчеркнуть индивидуальность
PERSONALIZATION_CONTEXTS = [
    "сколько мне", "мне нужно", "я хочу", "как мне",
    "подходит ли", "можно ли мне", "безопасно ли"
]


def check_query_safety(query: str) -> SafetyWarning:
    """
    Анализирует запрос пользователя на наличие опасных триггеров.
    Возвращает объект предупреждения.
    """
    query_lower = query.lower()
    triggered_critical = []
    triggered_caution = []

    # Проверка критических симптомов
    for keyword in CRITICAL_SYMPTOMS:
        if keyword in query_lower:
            triggered_critical.append(keyword)

    if triggered_critical:
        return SafetyWarning(
            is_critical=True,
            message=(
                "ВНИМАНИЕ: Требуется медицинская помощь\n\n"
                "Ваш запрос содержит симптомы, которые могут указывать на серьёзное состояние. "
                "Я — помощник по образу жизни, а не врач.\n\n"
            ),
            action_recommended="emergency" if len(triggered_critical) > 2 else "consult_doctor",
            triggered_by=triggered_critical
        )

    # Проверка предупреждений
    for keyword in CAUTION_KEYWORDS:
        if keyword in query_lower:
            triggered_caution.append(keyword)

    if triggered_caution:
        return SafetyWarning(
            is_critical=False,
            message=(
                "ℹ️ Обратите внимание\n\n"
                "Запрос касается темы, где важны индивидуальные особенности здоровья. "
                "Рекомендации ниже носят общий характер.\n\n"
                "💡 Совет: Перед изменением питания, режима тренировок или приёмом добавок "
                "проконсультируйтесь с врачом, особенно если у вас есть хронические заболевания."
            ),
            action_recommended="caution",
            triggered_by=triggered_caution
        )

    return SafetyWarning(
        is_critical=False,
        message="",
        action_recommended="none"
    )


def evaluate_card_safety(card: KnowledgeCard) -> bool:
    """
    Определяет, требует ли карточка дополнительного предупреждения.
    Использует встроенный метод модели + эвристики.
    """
    # Если модель уже помечает как требующую консультации — доверяем ей
    if card.requires_medical_consultation():
        return True

    # Дополнительная проверка по аудитории
    high_risk_audiences = {"pregnant", "children", "chronic_conditions"}
    if set(card.audience).intersection(high_risk_audiences):
        return True

    # Проверка по уровню доказательности
    if card.evidence_level in {"low", "expert_opinion"} and any(
            kw in (card.content.description + " " + str(card.content.recommendations)).lower()
            for kw in ["принимать", "доз", "курс", "леч", "терапия"]
    ):
        return True

    return False


def format_safety_footer(card: KnowledgeCard) -> str:
    """Формирует текстовый футер с предупреждениями для карточки"""
    warnings = []

    if card.requires_medical_consultation():
        warnings.append("⚠️ Проконсультируйтесь с врачом перед применением")

    if card.content.risks:
        warnings.append(f"Риски: {'; '.join(card.content.risks[:2])}")

    if card.evidence_level in {"low", "expert_opinion"}:
        warnings.append("📚 Информация основана на экспертном мнении")

    if not warnings:
        return ""

    return "\n\n" + " | ".join(warnings)


def build_api_response(
        results: List,
        safety_warning: Optional[SafetyWarning] = None,
        message: str = ""
) -> APIResponse:
    """
    Создаёт унифицированный ответ API с учётом безопасности.
    """
    # Если есть критическое предупреждение — не показываем результаты
    if safety_warning and safety_warning.is_critical:
        return APIResponse(
            success=True,
            warning=safety_warning,
            message="По вашему запросу не могут быть предоставлены рекомендации ЗОЖ.",
            meta=None
        )

    # Добавляем предупреждения к карточкам, если нужно
    enriched_results = []
    for res in results:
        card = res.card
        if evaluate_card_safety(card):
            # Можно добавить поле в карточку или оставить в футере
            pass
        enriched_results.append(res)

    return APIResponse(
        success=True,
        results=enriched_results,
        warning=safety_warning if safety_warning and not safety_warning.is_critical else None,
        message=message or (
            f"Найдено рекомендаций: {len(enriched_results)}"
            if enriched_results
            else "По запросу ничего не найдено"
        ),
        meta=None,
    )