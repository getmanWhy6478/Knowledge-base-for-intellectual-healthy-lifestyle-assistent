
import re
from typing import List, Tuple, Optional

MIN_QUERY_LENGTH = 2

MAX_QUERY_LENGTH = 500

ALLOWED_CHARS_PATTERN = r'^[а-яА-ЯёЁa-zA-Z0-9\s\-\_\.\,\?\!\:\;\(\)\"\'%]+$'

STOP_WORDS = {
    'а', 'о', 'и', 'у', 'э', 'ы', 'я', 'е', 'ё', 'ю',
    'ну', 'да', 'нет', 'ок', 'хм', 'мм', 'ээ',
    'привет', 'здравствуйте', 'пока', 'спасибо', 'пожалуйста',
    'тест', 'тестирование', 'проверка', '123', '...', '---'
}

HEALTH_KEYWORDS = {
    'белок', 'жир', 'углевод', 'калория', 'витамин', 'минерал',
    'овощ', 'фрукт', 'мясо', 'рыба', 'молоко', 'хлеб', 'каша',
    'диета', 'похуд', 'набор', 'вес', 'метаболизм', 'нутриент',

    'трениров', 'упражн', 'кардио', 'силов', 'растяж', 'размин',
    'бег', 'ходьб', 'плаван', 'велосипед', 'пресс', 'присед',
    'вынослив', 'сила', 'гибкость', 'координация',

    'стресс', 'тревож', 'сон', 'отдых', 'медитаци', 'дыхани',
    'настроение', 'мотивация', 'усталость', 'выгорани',
    'концентрация', 'память', 'внимание',

    'здоров', 'иммунитет', 'профилактик', 'гигиен', 'режим',
    'вода', 'питьё', 'гидратация', 'энергия', 'восстановление'
}

SEMANTIC_THRESHOLD = 0.25

class QueryValidator:

    def __init__(self, known_topics: Optional[List[str]] = None):

        self.known_topics = known_topics or []

    def validate(self, query: str) -> Tuple[bool, Optional[str], List[str]]:

        is_valid, message, suggestions = self._check_basic(query)
        if not is_valid:
            return False, message, suggestions

        is_valid, message, suggestions = self._check_lexical(query)
        if not is_valid:
            return False, message, suggestions

        return True, None, []

    def _check_basic(self, query: str) -> Tuple[bool, Optional[str], List[str]]:
        query_stripped = query.strip()

        if not query_stripped:
            return False, "Введите запрос для поиска", []

        if len(query_stripped) < MIN_QUERY_LENGTH:
            return False, "Запрос слишком короткий (минимум 2 символа)", []

        if len(query_stripped) > MAX_QUERY_LENGTH:
            return False, f"Запрос слишком длинный (максимум {MAX_QUERY_LENGTH} символов)", []

        if not re.match(ALLOWED_CHARS_PATTERN, query_stripped):
            return False, "Запрос содержит недопустимые символы", []

        if re.match(r'^[\s\-\_\.\,\?\!\:]+$', query_stripped):
            return False, "Введите осмысленный запрос", []

        if query_stripped.lower() in STOP_WORDS:
            return False, "Этот запрос не содержит полезной информации", [
                "Попробуйте: 'здоровое питание', 'упражнения для спины', 'как улучшить сон'"
            ]

        return True, None, []

    def _check_lexical(self, query: str) -> Tuple[bool, Optional[str], List[str]]:
        query_lower = query.lower()
        words = re.findall(r'[а-яёa-z]{3,}', query_lower)  # Слова от 3 букв

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
            return True, None, suggestions  # Мягкое предупреждение

        return True, None, []

    def _check_semantic(self, query: str, model) -> Tuple[bool, Optional[str], List[str]]:
        if not self.known_topics or not model:
            return True, None, []

        import numpy as np

        query_embedding = model.encode([query])[0]

        topic_embeddings = model.encode(self.known_topics)

        similarities = np.dot(topic_embeddings, query_embedding) / (
                np.linalg.norm(topic_embeddings, axis=1) * np.linalg.norm(query_embedding)
        )

        max_similarity = np.max(similarities)

        if max_similarity < SEMANTIC_THRESHOLD:
            suggestions = self._get_closest_topics(query, self.known_topics, model, top_k=3)
            return False, f"Запрос не соответствует темам базы знаний", suggestions

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

        return suggestions[:5]

    def _get_closest_topics(self, query: str, topics: List[str], model, top_k: int = 3) -> List[str]:
        import numpy as np

        query_embedding = model.encode([query])[0]
        topic_embeddings = model.encode(topics)

        similarities = np.dot(topic_embeddings, query_embedding) / (
                np.linalg.norm(topic_embeddings, axis=1) * np.linalg.norm(query_embedding) + 1e-10
        )

        top_indices = np.argsort(similarities)[::-1][:top_k]
        return [topics[i] for i in top_indices if similarities[i] > 0.1]

def create_validator_from_cards(cards) -> QueryValidator:
    known_topics = set()

    for card in cards:
        known_topics.update(card.tags)
        known_topics.add(card.title.lower())
        if hasattr(card, 'content') and card.content.definition:
            known_topics.add(card.content.definition[:100].lower())

    return QueryValidator(known_topics=list(known_topics))