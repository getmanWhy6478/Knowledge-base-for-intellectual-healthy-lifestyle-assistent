"""
Загрузчик карточек знаний в стандартном формате:
---
yaml: frontmatter
---
## Markdown content
"""

import re
import yaml
from pathlib import Path
from typing import List, Optional, Dict
from datetime import date

from models import (
    KnowledgeCard,
    Domain, Category, EvidenceLevel, Audience,
    DocumentStatus
)


# =============================================================================
# КОНФИГУРАЦИЯ
# =============================================================================

# Маппинг заголовков разделов на поля KnowledgeContent
SECTION_MAP = {
    'определение': 'definition',
    'описание': 'description',
    'суть рекомендации': 'description',
    'ключевые свойства': 'key_properties',
    'польза': 'benefits',
    'преимущества': 'benefits',
    'риски': 'risks',
    'риски и ограничения': 'risks',
    'ограничения': 'risks',
    'рекомендации': 'recommendations',
    'практические рекомендации': 'recommendations',
    'практическое применение': 'recommendations',
    'исключения': 'exceptions',
    'исключения и противопоказания': 'exceptions',
    'условия применимости': 'applicability',
    'обоснование': 'justification',
    'доказательная база': 'justification',
    'тип': 'type',
    'вердикт': 'verdict',
    'анализ': 'analysis',
    'разбор': 'analysis',
    'корректная формулировка': 'correct_formulation',
    'синонимы': 'synonyms',
    'контекст использования': 'usage_context',
    'примеры использования': 'usage_examples',
    'примеры употребления': 'usage_examples',
    'источники': 'sources',
    'когда требуется внимание специалиста': 'visit',
    'важное предупреждение': 'warning',
    'формулировка правила': 'rule_statement',

}

# Поля, которые являются списками строк
LIST_FIELDS = {'tags', 'audience', 'sources', 'benefits', 'risks', 'recommendations', 'exceptions', 'synonyms', 'usage_examples'}


# =============================================================================
# ПАРСИНГ ФРОНТМАТТЕРА
# =============================================================================

def parse_frontmatter(raw_text: str) -> tuple[dict, str]:
    """
    Парсит файл с форматом:
    ---
    yaml...
    ---
    # Markdown content
    """
    # Разделяем по разделителям ---
    parts = re.split(r'^---\s*$', raw_text.strip(), maxsplit=2, flags=re.MULTILINE)
    if len(parts) < 3:
        raise ValueError("Файл должен начинаться с --- YAML фронтматтера ---")

    yaml_block = parts[1].strip()
    markdown_body = parts[2].strip()

    # Парсим YAML
    meta = yaml.safe_load(yaml_block)
    if not isinstance(meta, dict):
        raise ValueError("Фронтматтер должен быть YAML-словарём")

    return meta, markdown_body


def normalize_meta(meta: dict) -> dict:
    """
    Приводит метаданные к формату, ожидаемому KnowledgeCard.
    """
    result = meta.copy()

    # 1. related: список строк -> список RelatedDocument
    if 'related' in result and isinstance(result['related'], list):
        result['related'] = [
            {'id': item, 'relation_type': 'relates_to', 'title': None}
            if isinstance(item, str)
            else item
            for item in result['related']
        ]

    # 2. Конвертация enum-полей (строка -> Enum)
    enum_maps = {
        'domain': Domain,
        'category': Category,
        'evidence_level': EvidenceLevel,
        'status': DocumentStatus,
    }
    for field, enum_cls in enum_maps.items():
        if field in result and isinstance(result[field], str):
            result[field] = enum_cls(result[field].lower())

    # 3. audience: список строк -> список Audience
    if 'audience' in result and isinstance(result['audience'], list):
        result['audience'] = [Audience(a.lower()) if isinstance(a, str) else a for a in result['audience']]

    # 4. Даты: строки -> date
    for field in ['date_created', 'date_updated']:
        if field in result and isinstance(result[field], str):
            result[field] = date.fromisoformat(result[field])

    return result


# =============================================================================
# ПАРСИНГ MARKDOWN-ТЕЛА
# =============================================================================

def parse_markdown_body(md_text: str) -> dict:
    """
    Парсит тело карточки с заголовками ## (и ###, встречается в части карточек).
    """
    result = {}

    # Сплитим по заголовкам ## / ###
    # Паттерн: перенос, затем ## или ###, пробел, название раздела
    sections = re.split(r'\n#{2,3}\s+', '\n' + md_text)

    for section in sections:
        section = section.strip()
        if not section:
            continue

        # Первая строка — заголовок, остальное — контент
        lines = section.split('\n', 1)
        header = lines[0].strip().lower()
        content = lines[1].strip() if len(lines) > 1 else ''

        # Маппим заголовок на поле
        field_name = SECTION_MAP.get(header, header.replace(' ', '_'))

        if field_name == 'key_properties':
            parsed = parse_key_value_list(content)
            if parsed:
                if isinstance(result.get(field_name), dict):
                    result[field_name].update(parsed)
                else:
                    result[field_name] = parsed
            continue

        if field_name in LIST_FIELDS:
            parsed = parse_list_items(content)
            if parsed:
                if isinstance(result.get(field_name), list):
                    result[field_name].extend(parsed)
                else:
                    result[field_name] = parsed
            continue

        text_value = content.strip()
        if not text_value:
            continue
        if isinstance(result.get(field_name), str) and result[field_name].strip():
            result[field_name] = result[field_name].rstrip() + "\n\n" + text_value
        else:
            result[field_name] = text_value

    # Описание обязательно
    if 'description' not in result:
        # Берём первый абзац после заголовка карточки (# Тревожность)
        first_para = re.split(r'\n#+\s+', md_text, maxsplit=1)
        if len(first_para) > 1:
            result['description'] = first_para[1].split('\n\n')[0].strip()[:500]

    # Небольшая нормализация списков: удаляем пустые/дубликаты, сохраняем порядок
    for list_field in LIST_FIELDS:
        if list_field in result and isinstance(result[list_field], list):
            seen = set()
            cleaned = []
            for item in result[list_field]:
                item = (item or "").strip()
                if not item:
                    continue
                key = item.lower()
                if key in seen:
                    continue
                seen.add(key)
                cleaned.append(item)
            result[list_field] = cleaned or None

    return result


def parse_list_items(text: str) -> Optional[List[str]]:
    """
    Парсит список из Markdown:
    - маркированный (- / *)
    - нумерованный (1. / 2.)

    Если список не размечен, но текст есть — возвращает 1 элемент (весь блок).
    """
    items = []
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue

        if line.startswith(('-', '*')):
            item = line[1:].strip()
            if item:
                items.append(item)
            continue

        m = re.match(r'^\d+\.\s+(.*)$', line)
        if m:
            item = m.group(1).strip()
            if item:
                items.append(item)
            continue

    if items:
        return items

    block = text.strip()
    return [block] if block else None


def parse_key_value_list(text: str) -> Optional[Dict[str, str]]:
    """Парсит список свойств: - **Ключ**: значение"""
    result = {}
    for line in text.split('\n'):
        line = line.strip()
        if line.startswith(('-', '*')):
            line = line[1:].strip()
        if ':' in line:
            key, _, value = line.partition(':')
            key = key.strip().strip('**')
            value = value.strip()
            if key and value:
                result[key] = value
    return result if result else None


# =============================================================================
# СБОРКА КАРТОЧКИ
# =============================================================================

def build_knowledge_card(file_path: str, meta: dict, content_md: str) -> KnowledgeCard:
    """
    Создаёт KnowledgeCard из метаданных и Markdown-контента.
    """
    # Нормализуем метаданные
    normalized_meta = normalize_meta(meta)

    # Парсим контент
    content_data = parse_markdown_body(content_md)

    # Источники могут встречаться в теле карточки в виде секции "## Источники"
    sources_from_body = content_data.pop('sources', None)
    if sources_from_body and isinstance(sources_from_body, list):
        existing_sources = normalized_meta.get('sources') or []
        merged = []
        seen = set()
        for s in list(existing_sources) + list(sources_from_body):
            s = (s or "").strip()
            if not s:
                continue
            key = s.lower()
            if key in seen:
                continue
            seen.add(key)
            merged.append(s)
        if merged:
            normalized_meta['sources'] = merged

    # Собираем карточку
    card_data = {
        **normalized_meta,
        'content': content_data,
        'file_path': file_path
    }

    return KnowledgeCard(**card_data)


def load_knowledge_base(directory: str = "knowledge_base") -> List[KnowledgeCard]:
    """
    Загружает все карточки из директории.
    """
    cards = []
    kb_path = Path(directory)

    for file_path in kb_path.rglob("*.md"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                raw = f.read()

            meta, content_md = parse_frontmatter(raw)
            card = build_knowledge_card(str(file_path), meta, content_md)

            # Загружаем только утверждённые карточки
            if card.status == DocumentStatus.APPROVED:
                cards.append(card)

        except Exception as e:
            print(f"⚠️ Ошибка загрузки {file_path}: {e}")
            continue

    print(f"✅ Загружено {len(cards)} карточек из {directory}")
    return cards