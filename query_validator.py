"""
Валидация пользовательских запросов для базы знаний ЗОЖ.
Многоуровневая проверка: базовая → лексическая → семантическая.
"""

import re
from typing import List, Tuple, Optional

# =============================================================================
# КОНФИГУРАЦИЯ
# =============================================================================

# Минимальная длина запроса
MIN_QUERY_LENGTH = 2

# Максимальная длина (защита от спама)
MAX_QUERY_LENGTH = 500

# Разрешённые символы (кириллица, латиница, цифры, базовая пунктуация)
ALLOWED_CHARS_PATTERN = r'^[а-яА-ЯёЁa-zA-Z0-9\s\-\_\.\,\?\!\:\;\(\)\"\'%]+$'

# Стоп-слова (запросы, которые не несут смысла)
STOP_WORDS = {
    'а', 'о', 'и', 'у', 'э', 'ы', 'я', 'е', 'ё', 'ю',
    'ну', 'да', 'нет', 'ок', 'хм', 'мм', 'ээ',
    'привет', 'здравствуйте', 'пока', 'спасибо', 'пожалуйста',
    'тест', 'тестирование', 'проверка', '123', '...', '---'
}

# Ключевые слова домена ЗОЖ (для быстрой фильтрации)
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

# Порог семантической релевантности (0.0 - 1.0)
SEMANTIC_THRESHOLD = 0.25


# =============================================================================
# КЛАСС ВАЛИДАТОРА
# =============================================================================

class QueryValidator:
    """
    Многоуровневый валидатор запросов.
    Возвращает: (is_valid: bool, message: Optional[str], suggestions: List[str])
    """

    def __init__(self, known_topics: Optional[List[str]] = None):
        """
        Инициализация.

        Args:
            known_topics: Список известных тем/тегов из базы знаний
                         (для семантической проверки)
        """
        self.known_topics = known_topics or []

    def validate(self, query: str) -> Tuple[bool, Optional[str], List[str]]:
        """
        Полная валидация запроса.

        Returns:
            (is_valid, error_message, suggestions)
        """
        # Уровень 1: Базовая проверка
        is_valid, message, suggestions = self._check_basic(query)
        if not is_valid:
            return False, message, suggestions

        # Уровень 2: Лексическая проверка
        is_valid, message, suggestions = self._check_lexical(query)
        if not is_valid:
            return False, message, suggestions

        # Уровень 3: Семантическая проверка (если есть эмбеддинги)
        # is_valid, message, suggestions = self._check_semantic(query)
        # if not is_valid:
        #     return False, message, suggestions

        # Все проверки пройдены
        return True, None, []

    def _check_basic(self, query: str) -> Tuple[bool, Optional[str], List[str]]:
        """Базовая проверка: длина, символы, пустота"""
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
        """Лексическая проверка: наличие слов из домена ЗОЖ"""
        query_lower = query.lower()
        words = re.findall(r'[а-яёa-z]{3,}', query_lower)  # Слова от 3 букв

        if not words:
            return False, "Запрос не содержит осмысленных слов", [
                "Используйте слова: питание, тренировка, сон, стресс, витамины..."
            ]

        # Проверка: есть ли хотя бы одно слово из домена ЗОЖ?
        has_health_keyword = any(
            any(keyword in word for keyword in HEALTH_KEYWORDS)
            for word in words
        )

        if not has_health_keyword:
            # Не блокируем, но предупреждаем
            suggestions = self._get_topic_suggestions(query_lower)
            return True, None, suggestions  # Мягкое предупреждение

        return True, None, []

    def _check_semantic(self, query: str, model) -> Tuple[bool, Optional[str], List[str]]:
        """
        Семантическая проверка: близость к известным темам.

        Args:
            model: sentence-transformers модель для эмбеддингов
        """
        if not self.known_topics or not model:
            return True, None, []  # Пропускаем, если нет данных

        import numpy as np

        # Эмбеддинг запроса
        query_embedding = model.encode([query])[0]

        # Эмбеддинги известных тем
        topic_embeddings = model.encode(self.known_topics)

        # Косинусное сходство
        similarities = np.dot(topic_embeddings, query_embedding) / (
                np.linalg.norm(topic_embeddings, axis=1) * np.linalg.norm(query_embedding)
        )

        max_similarity = np.max(similarities)

        if max_similarity < SEMANTIC_THRESHOLD:
            suggestions = self._get_closest_topics(query, self.known_topics, model, top_k=3)
            return False, f"Запрос не соответствует темам базы знаний", suggestions

        return True, None, []

    def _get_topic_suggestions(self, query: str) -> List[str]:
        """Генерирует подсказки на основе частичного совпадения"""
        suggestions = []
        query_lower = query.lower()

        # Группы подсказок по категориям
        categories = {
            'питание': ['здоровое питание', 'баланс белков', 'витамины', 'калории'],
            'спорт': ['упражнения для дома', 'кардио тренировка', 'растяжка', 'силовые'],
            'сон': ['как улучшить сон', 'режим сна', 'борьба с бессонницей'],
            'стресс': ['управление стрессом', 'техники релаксации', 'дыхательные упражнения'],
            'общее': ['укрепление иммунитета', 'профилактика заболеваний', 'энергия в течение дня']
        }

        # Простое сопоставление по ключевым словам
        for category, examples in categories.items():
            if category in query_lower or any(kw in query_lower for kw in examples[:2]):
                suggestions.extend(examples)
                break

        # Если ничего не подошло — общие примеры
        if not suggestions:
            suggestions = [
                "здоровое питание",
                "упражнения для спины",
                "как улучшить сон",
                "борьба со стрессом",
                "укрепление иммунитета"
            ]

        return suggestions[:5]  # Максимум 5 подсказок

    def _get_closest_topics(self, query: str, topics: List[str], model, top_k: int = 3) -> List[str]:
        """Находит ближайшие темы по эмбеддингам (для семантических подсказок)"""
        import numpy as np

        query_embedding = model.encode([query])[0]
        topic_embeddings = model.encode(topics)

        similarities = np.dot(topic_embeddings, query_embedding) / (
                np.linalg.norm(topic_embeddings, axis=1) * np.linalg.norm(query_embedding) + 1e-10
        )

        top_indices = np.argsort(similarities)[::-1][:top_k]
        return [topics[i] for i in top_indices if similarities[i] > 0.1]


# =============================================================================
# УТИЛИТЫ ДЛЯ ИНТЕГРАЦИИ
# =============================================================================

def create_validator_from_cards(cards) -> QueryValidator:
    """
    Создаёт валидатор на основе загруженных карточек.
    Извлекает теги и заголовки как известные темы.
    """
    known_topics = set()

    for card in cards:
        # Теги
        known_topics.update(card.tags)
        # Заголовок и тема
        known_topics.add(card.title.lower())
        if hasattr(card, 'content') and card.content.definition:
            known_topics.add(card.content.definition[:100].lower())

    return QueryValidator(known_topics=list(known_topics))