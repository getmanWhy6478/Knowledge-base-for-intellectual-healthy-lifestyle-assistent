"""
Валидация пользовательских запросов для базы знаний ЗОЖ.
Многоуровневая проверка: базовая → лексическая → семантическая.
"""

import re
from typing import List, Tuple, Optional
from pymorphy3 import MorphAnalyzer
from difflib import SequenceMatcher

MIN_QUERY_LENGTH = 3

MAX_QUERY_LENGTH = 500

ALLOWED_CHARS_PATTERN = r'^[а-яА-ЯёЁa-zA-Z0-9\s\-\_\.\,\?\!\:\;\(\)\"\'%]+$'

# Стоп-слова (запросы, которые не несут смысла)
STOP_WORDS = {
    'а', 'о', 'и', 'у', 'э', 'ы', 'я', 'е', 'ё', 'ю',
    'ну', 'да', 'нет', 'ок', 'хм', 'мм', 'ээ',
    'привет', 'здравствуйте', 'пока', 'спасибо', 'пожалуйста',
    'тест', 'тестирование', 'проверка', '123', '...', '---', 'мне',
    'ей', ' ему', 'почему', 'зачем', 'как', 'можно', 'нужно', 'надо',
    'хочу', 'хочется',
}

HEALTH_KEYWORDS = {
    # Питание
    'белок', 'жир', 'углевод', 'калория', 'витамин', 'минерал',
    'овощ', 'фрукт', 'мясо', 'рыба', 'молоко', 'хлеб', 'каша',
    'диета', 'похуд', 'набор', 'вес', 'метаболизм', 'нутриент',

    # Спорт
    'трениров', 'упражн', 'кардио', 'силов', 'растяж', 'размин',
    'бег', 'ходьб', 'плаван', 'велосипед', 'пресс', 'присед',
    'вынослив', 'сила', 'гибкость', 'координация',

    # Ментальное здоровье
    'стресс', 'тревож', 'сон', 'отдых', 'медитаци', 'дыхани',
    'настроение', 'мотивация', 'усталость', 'выгорани',
    'концентрация', 'память', 'внимание',

    # Общие темы ЗОЖ
    'здоров', 'иммунитет', 'профилактик', 'гигиен', 'режим',
    'вода', 'питьё', 'гидратация', 'энергия', 'восстановление'
}


class QueryValidator:

    def __init__(self, known_topics: Optional[List[str]] = None):

        self.known_topics = known_topics or []
        self.morph = MorphAnalyzer()

    def _lemmatize(self, word: str) -> str:
        return self.morph.parse(word)[0].normal_form

    def validate(self, query: str) -> Tuple[bool, Optional[str], List[str]]:

        # Уровень 1: Базовая проверка
        is_valid, message, suggestions = self._check_basic(query)
        if not is_valid:
            return False, message, suggestions

        is_valid, message, suggestions = self._check_typos(query)
        if not is_valid:
            return False, message, suggestions

        # Уровень 2: Лексическая проверка
        is_valid, message, suggestions = self._check_lexical(query)
        if not is_valid:
            return False, message, suggestions

        # Все проверки пройдены
        return True, None, []

    def _check_typos(self, query: str) -> Tuple[bool, Optional[str], List[str]]:

        if not self.known_topics:
            return True, None, []

        query_lower = query.lower().strip().split()

        best_match = None
        best_ratio = 0

        for topic in self.known_topics:
            for word in query_lower:
                ratio = SequenceMatcher(None, word, topic.lower()).ratio()
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_match = topic

        if 0.01 < best_ratio < 0.6:
            return False, f"Найдено 0 рекомендация", [best_match]

        return True, None, []

    def _check_basic(self, query: str) -> Tuple[bool, Optional[str], List[str]]:

        query_stripped = query.strip()

        # Пустой запрос
        if not query_stripped:
            return False, "Введите запрос для поиска", []

        # Слишком короткий
        if len(query_stripped) < MIN_QUERY_LENGTH:
            return False, "Запрос слишком короткий (минимум 2 символа)", []

        # Слишком длинный
        if len(query_stripped) > MAX_QUERY_LENGTH:
            return False, f"Запрос слишком длинный (максимум {MAX_QUERY_LENGTH} символов)", []

        # Недопустимые символы
        if not re.match(ALLOWED_CHARS_PATTERN, query_stripped):
            return False, "Запрос содержит недопустимые символы", []

        # Только пробелы/повторы
        if re.match(r'^[\s\-\_\.\,\?\!\:]+$', query_stripped):
            return False, "Введите осмысленный запрос", []

        # Стоп-слова
        if query_stripped.lower() in STOP_WORDS:
            return False, "Этот запрос не содержит полезной информации", [
                "Попробуйте: 'здоровое питание', 'упражнения для спины', 'как улучшить сон'"
            ]

        return True, None, []

    def _check_lexical(self, query: str) -> Tuple[bool, Optional[str], List[str]]:
        query_lower = query.lower()
        words = [self._lemmatize(w) for w in re.findall(r'[а-яёa-z]{3,}', query_lower)]

        if not words:
            return False, "Запрос не содержит осмысленных слов", [
                "Используйте слова: питание, тренировка, сон, стресс, витамины..."
            ]

        has_health_keyword = any(
            any(keyword in word for keyword in HEALTH_KEYWORDS)
            for word in words
        )

        if not has_health_keyword:
            suggestions = self._get_topic_suggestions(query_lower)
            return True, None, suggestions

        return True, None, []

    def _get_topic_suggestions(self, query: str) -> List[str]:

        suggestions = []
        query_lower = query.lower()

        categories = {
            'питание': ['здоровое питание', 'баланс белков', 'витамины', 'калории'],
            'спорт': ['упражнения для дома', 'кардио тренировка', 'растяжка', 'силовые'],
            'сон': ['как улучшить сон', 'режим сна', 'борьба с бессонницей'],
            'стресс': ['управление стрессом', 'техники релаксации', 'дыхательные упражнения'],
            'общее': ['укрепление иммунитета', 'профилактика заболеваний', 'энергия в течение дня']
        }

        for category, examples in categories.items():
            if category in query_lower or any(kw in query_lower for kw in examples[:2]):
                suggestions.extend(examples)
                break

        if not suggestions:
            suggestions = [
                "здоровое питание",
                "упражнения для спины",
                "как улучшить сон",
                "борьба со стрессом",
                "укрепление иммунитета"
            ]

        return suggestions[:5]  # Максимум 5 подсказок

def create_validator_from_cards(cards) -> QueryValidator:
    known_topics = set()

    for card in cards:
        # Теги
        for i in card.tags:
            known_topics.update(i.split())
        # Заголовок и тема
        known_topics.update(card.title.lower().split())
        if hasattr(card, 'content') and card.content.definition:
            known_topics.update(card.content.definition[:100].lower().split())

    return QueryValidator(known_topics=list(known_topics))