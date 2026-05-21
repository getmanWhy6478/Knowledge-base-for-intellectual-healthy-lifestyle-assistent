from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Optional, Dict, Literal
from datetime import date
from enum import Enum
import re


class Domain(str, Enum):
    """Предметные области (Уровень 1 + глобальная)"""
    NUTRITION = "nutrition"
    SPORT = "sport"
    MENTAL = "mental"
    GLOBAL = "global"


class Category(str, Enum):
    """Типы единиц знаний"""
    # Глоссарий и онтология
    GLOSSARY = "glossary"
    ONTOLOGY = "ontology"
    AUDIENCE = "audience"

    # Питание
    PRODUCT = "product"
    NUTRIENT = "nutrient"
    DIET = "diet"

    # Спорт
    ACTIVITY = "activity"
    EXERCISE = "exercise"
    SPORT_TYPE = "sport_type"
    PROGRAM = "program"
    INJURY = "injury"
    SPORTS = "sports"

    # Ментальное здоровье
    TECHNIQUE = "technique"
    CONDITION = "condition"
    HABIT = "habit"
    SELF_HELP = "self_help"

    # Универсальные
    RULE = "rule"
    FACT = "fact"
    MYTH = "myth"
    CROSS = "cross"
    PROFILE = "profile"
    PARTIALLY_TRUE = "partially_true"
    SPECIAL_GROUPS = "special_groups"


class EvidenceLevel(str, Enum):
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    EXPERT_OPINION = "expert_opinion"


class DocumentStatus(str, Enum):
    """Статусы документа"""
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"


class Audience(str, Enum):
    """Целевые аудитории"""
    GENERAL = "general"
    CHILDREN = "children"
    TEENAGERS = "teenagers"
    ADULTS = "adults"
    ELDERLY = "elderly"
    PREGNANT = "pregnant"
    ATHLETES = "athletes"
    BEGINNERS = "beginners"
    CHRONIC_CONDITIONS = "chronic_conditions"
    LIMITED_MOBILITY = "limited_mobility"
    CARDIOVASCULAR = "cardiovascular"
    VEGETARIANS = "vegetarians"
    DIABETES = "diabetes"
    CELIAC = "celiac"
    WEIGHT_MANAGEMENT = "weight_management"
    VEGAN = "vegan"



class RelationType(str, Enum):
    """Типы связей между документами"""
    IS_PART_OF = "is_part_of"
    RELATES_TO = "relates_to"
    DEPENDS_ON = "depends_on"
    CONTRADICTS = "contradicts"
    SUPPLEMENTS = "supplements"
    SPECIALIZES = "specializes"
    GENERALIZES = "generalizes"
    REQUIRES = "requires"
    SYNERGY_WITH = "synergy_with"
    RISK_WITH = "risk_with"

class RelatedDocument(BaseModel):
    """Связанный документ с указанием типа связи"""
    id: str = Field(..., description="ID связанного документа, например 'NUT-PROD-012'")
    relation_type: RelationType = Field(default=RelationType.RELATES_TO)
    title: Optional[str] = Field(None, description="Название документа (для отображения)")

    @field_validator('id')
    @classmethod
    def validate_id_format(cls, v: str) -> str:
        """Проверка формата ID: DOMAIN-CATEGORY-NNN"""
        pattern = r'^(GLB|NUT|SPR|MNT)-[A-Z_]+-\d{3}$'
        if not re.match(pattern, v.upper()):
            raise ValueError(
                f"Неверный формат ID: '{v}'. Ожидалось: ДОМЕН-КАТЕГОРИЯ-НОМЕР (например, NUT-PROD-012)"
            )
        return v.upper()


class KnowledgeContent(BaseModel):
    """Базовое содержимое карточки (общее для всех типов)"""
    definition: Optional[str] = Field(None, description="Определение", max_length=500)
    description: str = Field(..., description="Описание", min_length=1)
    related_topics: Optional[List[str]] = Field(
        None,
        description="Связанные темы"
    )

    # Универсальные блоки (используются выборочно в зависимости от типа)
    context: Optional[str] = Field(None, description="Контекст применения")
    key_properties: Optional[Dict[str, str]] = Field(None, description="Ключевые свойства")
    benefits: Optional[List[str]] = Field(None, description="Список преимуществ/пользы")
    risks: Optional[List[str]] = Field(None, description="Риски и ограничения")
    recommendations: Optional[List[str]] = Field(None, description="Практические рекомендации")
    visit: Optional[str] = Field(None, description="Когда требуется внимание специалиста")
    warning: Optional[str] = Field(None, description="Важное предупреждение")

    # Для правил и фактов
    rule_statement: Optional[str] = Field(None, description="Формулировка правила")
    essence: Optional[str] = Field(None, description="Суть рекомендации")
    practical_application: Optional[str] = Field(None, description="Практическое применение")
    applicability: Optional[str] = Field(None, description="Условия применимости")
    justification: Optional[str] = Field(None, description="Обоснование / механизм действия")
    exceptions: Optional[List[str]] = Field(None, description="Исключения и противопоказания")

    # Для фактов/мифов
    type: Optional[Literal["Факт", "Миф", "Частично верно"]] = Field(None, description="Тип")
    verdict:  Optional[str] = Field(None, description="Вердикт для факта/мифа")
    analysis: Optional[str] = Field(None, description="Подробный разбор утверждения")
    correct_formulation: Optional[str] = Field(None, description="Корректная формулировка (для мифов)")

    # Для глоссария
    synonyms: Optional[List[str]] = Field(None, description="Синонимы термина")
    usage_context: Optional[str] = Field(None, description="Контекст использования термина")
    usage_examples: Optional[List[str]] = Field(None, description="Примеры употребления")

    extra_sections: Optional[Dict[str, str]] = Field(
        None,
        description="Дополнительные разделы карточки (заголовок → Markdown-текст)",
    )

class KnowledgeCard(BaseModel):

    model_config = ConfigDict(populate_by_name=True, use_enum_values=True)

    # Метаданные (YAML frontmatter)

    id: str = Field(
        ...,
        description="Уникальный идентификатор: ДОМЕН-КАТЕГОРИЯ-НОМЕР",
        pattern=r'^(GLB|NUT|SPR|MNT)-[A-Z_]+-\d{3}$',
        examples=["NUT-PROD-012", "SPR-ACT-005", "MNT-TECH-007", "GLB-CROSS-001"]
    )

    title: str = Field(..., description="Название единицы знаний", min_length=3, max_length=200)

    domain: Domain = Field(..., description="Предметная область")

    category: Category = Field(..., description="Тип единицы знаний")

    tags: List[str] = Field(
        default_factory=list,
        description="Теги из таксономии (тема, аудитория, тип действия, приоритет)",
        max_length=30
    )

    related: List[RelatedDocument] = Field(
        default_factory=list,
        description="Перекрёстные ссылки на другие документы"
    )

    audience: List[Audience] = Field(
        default_factory=lambda: [Audience.GENERAL],
        description="Целевые аудитории"
    )

    evidence_level: EvidenceLevel = Field(
        default=EvidenceLevel.EXPERT_OPINION,
        description="Уровень научной доказательности"
    )

    sources: List[str] = Field(
        ...,
        description="Список источников (ссылки или библиографические описания)",
        min_length=1  # ✅ Pydantic v2
    )

    author: str = Field(..., description="Имя инженера знаний", min_length=2)

    version: str = Field(default="1.0", description="Версия документа", pattern=r'^\d+\.\d+$')

    date_created: date = Field(..., description="Дата создания (YYYY-MM-DD)")

    date_updated: date = Field(..., description="Дата последнего обновления")

    status: DocumentStatus = Field(default=DocumentStatus.DRAFT, description="Статус документа")

    content: KnowledgeContent = Field(..., description="Основное содержимое карточки")

    file_path: Optional[str] = Field(None, description="Путь к файлу .md в хранилище")

    semantic_embedding: Optional[List[float]] = Field(None, description="Векторное представление для поиска")

    @field_validator('id')
    @classmethod
    def validate_id_format(cls, v: str) -> str:
        """Проверка формата идентификатора"""
        v_upper = v.upper()
        pattern = r'^(GLB|NUT|SPR|MNT)-[A-Z_]+-\d{3}$'
        if not re.match(pattern, v_upper):
            raise ValueError(
                f"Неверный формат ID: '{v}'. "
                f"Ожидалось: ДОМЕН-КАТЕГОРИЯ-НОМЕР, например: NUT-PROD-012, SPR-ACT-015, MNT-TECH-007"
            )
        return v_upper

    @field_validator('date_updated')
    @classmethod
    def validate_dates(cls, date_updated: date, values) -> date:
        date_created = values.data.get('date_created') if hasattr(values, 'data') else None
        if date_created and date_updated < date_created:
            raise ValueError("date_updated не может быть раньше date_created")
        return date_updated

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, tags: List[str]) -> List[str]:
        if not tags:
            return tags

        cleaned = list(set(tag.lower().strip() for tag in tags if tag.strip()))

        tag_pattern = r'^[a-zа-яё0-9_-]+$'

        for tag in cleaned:
            if not re.match(tag_pattern, tag, re.IGNORECASE | re.UNICODE):
                raise ValueError(
                    f"Тег '{tag}' содержит недопустимые символы. "
                    f"Разрешены: кириллица (а-яё), латиница (a-z), цифры (0-9), подчёркивание (_), дефис (-)"
                )

        return cleaned

    @field_validator('sources')
    @classmethod
    def validate_sources(cls, sources: List[str]) -> List[str]:
        if not sources:
            raise ValueError("Поле sources должно содержать хотя бы один источник")
        return [s.strip() for s in sources if s.strip()]

    def get_search_text(self) -> str:

        parts = [self.title, self.content.description]
        if self.content.definition:
            parts.append(self.content.definition)
        if self.content.benefits:
            parts.extend(self.content.benefits)
        if self.content.recommendations:
            parts.extend(self.content.recommendations)
        parts.extend(self.tags)
        parts.extend([r.id for r in self.related])
        return " ".join(filter(None, parts))

    def to_yaml_frontmatter(self) -> str:
        import yaml
        meta = {
            "id": self.id,
            "title": self.title,
            "domain": self.domain,
            "category": self.category,
            "tags": self.tags,
            "related": [r.model_dump() for r in self.related],
            "audience": self.audience,
            "evidence_level": self.evidence_level,
            "sources": self.sources,
            "author": self.author,
            "version": self.version,
            "date_created": self.date_created.isoformat(),
            "date_updated": self.date_updated.isoformat(),
            "status": self.status,
        }
        return yaml.dump(meta, allow_unicode=True, sort_keys=False, default_flow_style=False)

    def is_approved(self) -> bool:
        return self.status == DocumentStatus.APPROVED

    def requires_medical_consultation(self) -> bool:

        warning_keywords = [
            "противопоказ", "врач", "специалист", "заболев", "беремен",
            "хроническ", "лекарств", "диагноз", "лечени"
        ]

        risks_text = " ".join(self.content.risks) if self.content.risks else ""
        exceptions_text = " ".join(self.content.exceptions) if self.content.exceptions else ""
        description_text = self.content.description or ""

        text_to_check = " ".join([
            risks_text,
            exceptions_text,
            description_text
        ]).lower()

        return any(kw in text_to_check for kw in warning_keywords)

class SearchQuery(BaseModel):
    """Запрос пользователя к базе знаний"""
    model_config = ConfigDict(use_enum_values=True)
    query: str = Field(..., min_length=2, max_length=500, description="Текст запроса")
    domain_filter: Optional[List[Domain]] = Field(None, description="Фильтр по предметным областям")
    category_filter: Optional[List[Category]] = Field(None, description="Фильтр по типам карточек")
    audience_filter: Optional[List[Audience]] = Field(None, description="Фильтр по целевой аудитории")
    min_evidence: Optional[EvidenceLevel] = Field(None, description="Минимальный уровень доказательности")
    top_k: int = Field(default=10, ge=1, le=20, description="Количество результатов")


class SearchResult(BaseModel):
    """Результат поиска: карточка + метаданные релевантности"""
    card: KnowledgeCard
    score: float = Field(..., ge=0.0, le=1.0, description="Оценка релевантности (косинусное сходство)")
    match_highlights: Optional[Dict[str, List[str]]] = Field(
        None, description="Подсвеченные совпадения: {поле: [фрагменты]}"
    )


class SafetyWarning(BaseModel):
    """Структура предупреждения безопасности"""
    is_critical: bool
    message: str
    action_recommended: Literal["consult_doctor", "emergency", "caution", "none"]
    triggered_by: Optional[List[str]] = None  # Какие триггеры сработали


class APIResponse(BaseModel):
    """Унифицированный ответ API"""
    success: bool
    data: Optional[List[SearchResult]] = Field(None, alias="results")
    warning: Optional[SafetyWarning] = None
    message: str = ""
    disclaimer: str = Field(
        default="Информация носит ознакомительный характер и не заменяет консультацию врача. "
                "При наличии симптомов обратитесь к специалисту."
    )
    meta: Optional[Dict] = Field(None, description="Пагинация, статистика и пр.")
    model_config = ConfigDict(populate_by_name=True)
