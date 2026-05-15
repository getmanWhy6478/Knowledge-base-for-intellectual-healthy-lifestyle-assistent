"""
Интеллектуальный поиск по базе знаний ЗОЖ.
Использует векторные эмбеддинги и фильтрацию по метаданным.
"""

import numpy as np
from typing import List, Optional, Dict
from sentence_transformers import SentenceTransformer

from models import (
    KnowledgeCard, SearchQuery, SearchResult,
    EvidenceLevel
)
from loader import load_knowledge_base
from query_validator import QueryValidator, create_validator_from_cards

class SearchEngine:
    """
    Движок семантического поиска с поддержкой:
    - векторной схожести (cosine similarity)
    - фильтрации по домену, категории, аудитории, уровню доказательности
    - ранжирования по релевантности + доказательности
    """

    def __init__(
        self,
        kb_path: str = "knowledge_base",
        model_name: str = 'paraphrase-multilingual-MiniLM-L12-v2',
        load_on_init: bool = True
    ):
        self.model = SentenceTransformer(model_name)
        self.cards: List[KnowledgeCard] = []
        self.embeddings: Optional[np.ndarray] = None
        self.validator = None

        if load_on_init:
            self.load_knowledge_base(kb_path)

    def load_knowledge_base(self, directory: str):
        """Загружает и индексирует карточки из директории"""
        print(f"🔄 Загрузка базы знаний из {directory}...")

        self.cards = load_knowledge_base(directory)
        self.validator = create_validator_from_cards(self.cards)
        if not self.cards:
            print("⚠️ База знаний пуста!")
            return

        # Генерируем эмбеддинги для поиска
        search_texts = [card.get_search_text() for card in self.cards]

        self.embeddings = self.model.encode(search_texts, show_progress_bar=True)

        print(f"✅ Индексировано {len(self.cards)} карточек. Векторы: {self.embeddings.shape}")

    def search(self, query: SearchQuery, min_score: float = 0.3) -> List[SearchResult]:
        """
        Выполняет поиск с учётом фильтров из запроса.
        Возвращает отсортированные результаты с оценкой релевантности.
        """
        if not self.cards or self.embeddings is None:
            return []
        if self.validator:
            is_valid, error_msg, suggestions = self.validator.validate(query.query)
            if not is_valid and error_msg:
                # Возвращаем пустой результат с подсказками
                return []  # Или можно кастомизировать ответ
        # 1. Векторизуем запрос
        normalized_query = (query.query or "").strip().lower()
        query_embedding = self.model.encode([normalized_query])[0]

        # 2. Вычисляем косинусное сходство
        similarities = self._cosine_similarity(query_embedding, self.embeddings)

        # 3. Применяем фильтры из запроса
        valid_indices = []
        for idx, card in enumerate(self.cards):
            if not self._matches_filters(card, query):
                continue
            if similarities[idx] >= min_score:
                valid_indices.append((idx, similarities[idx]))

        # 4. Сортируем: сначала по релевантности, потом по уровню доказательности
        evidence_weights = {
            EvidenceLevel.HIGH: 3,
            EvidenceLevel.MODERATE: 2,
            EvidenceLevel.LOW: 1,
            EvidenceLevel.EXPERT_OPINION: 0
        }

        valid_indices.sort(
            key=lambda x: (x[1], evidence_weights.get(self.cards[x[0]].evidence_level, 0)),
            reverse=True
        )

        # 5. Формируем результаты
        results = []
        for idx, score in valid_indices[:query.top_k]:
            card = self.cards[idx]
            highlights = self._extract_highlights(card, query.query)

            results.append(SearchResult(
                card=card,
                score=float(score),
                match_highlights=highlights if highlights else None
            ))

        return results

    def _cosine_similarity(self, query_vec: np.ndarray, doc_vecs: np.ndarray) -> np.ndarray:
        """Вычисляет косинусное сходство между вектором запроса и документами"""
        query_norm = np.linalg.norm(query_vec)
        doc_norms = np.linalg.norm(doc_vecs, axis=1)
        doc_norms = np.where(doc_norms == 0, 1e-10, doc_norms)

        similarities = np.dot(doc_vecs, query_vec) / (doc_norms * query_norm)
        return np.clip(similarities, 0, 1)

    def _matches_filters(self, card: KnowledgeCard, query: SearchQuery) -> bool:
        """Проверяет, удовлетворяет ли карточка фильтрам запроса"""
        def _val(x):
            return getattr(x, "value", x)

        if query.domain_filter and _val(card.domain) not in {_val(d) for d in query.domain_filter}:
            return False
        if query.category_filter and _val(card.category) not in {_val(c) for c in query.category_filter}:
            return False
        if query.audience_filter and not {_val(a) for a in card.audience}.intersection({_val(a) for a in query.audience_filter}):
            return False
        if query.min_evidence:
            evidence_order = [
                EvidenceLevel.HIGH,
                EvidenceLevel.MODERATE,
                EvidenceLevel.LOW,
                EvidenceLevel.EXPERT_OPINION,
            ]
            evidence_order_vals = [_val(e) for e in evidence_order]
            if evidence_order_vals.index(_val(card.evidence_level)) > evidence_order_vals.index(_val(query.min_evidence)):
                return False
        return True

    def _extract_highlights(self, card: KnowledgeCard, query: str) -> Optional[Dict[str, List[str]]]:
        """Находит фрагменты текста карточки, содержащие слова из запроса"""
        import re
        query_words = set(re.findall(r'[а-яa-z]{3,}', query.lower(), re.I))
        if not query_words:
            return None

        highlights = {}
        fields_to_check = [
            ('title', card.title),
            ('definition', card.content.definition),
            ('description', card.content.description),
            ('benefits', ' '.join(card.content.benefits or [])),
            ('recommendations', ' '.join(card.content.recommendations or []))
        ]

        for field_name, text in fields_to_check:
            if not text:
                continue
            sentences = re.split(r'[.!?]+', text)
            matches = []
            for sent in sentences:
                sent_stripped = sent.strip()
                if len(sent_stripped) < 10:
                    continue
                sent_lower = sent_stripped.lower()
                if any(word in sent_lower for word in query_words):
                    matches.append(sent_stripped[:200] + "..." if len(sent_stripped) > 200 else sent_stripped)
            if matches:
                highlights[field_name] = matches[:3]

        return highlights if highlights else None

    def get_card_by_id(self, card_id: str) -> Optional[KnowledgeCard]:
        """Получает карточку по ID"""
        for card in self.cards:
            if card.id.upper() == card_id.upper():
                return card
        return None

    def get_statistics(self) -> dict:
        """Возвращает статистику по базе знаний"""
        if not self.cards:
            return {"total_cards": 0}

        from collections import Counter
        return {
            "total_cards": len(self.cards),
            "by_domain": dict(Counter(c.domain for c in self.cards)),
            "by_category": dict(Counter(c.category for c in self.cards)),
            "by_evidence": dict(Counter(c.evidence_level for c in self.cards)),
            "approved_count": sum(1 for c in self.cards if c.is_approved())
        }