"""
Интеллектуальный поиск по базе знаний ЗОЖ.
Использует векторные эмбеддинги + BM25 для гибридного поиска.
"""
import numpy as np
from typing import List, Optional, Dict
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
from models import (
    KnowledgeCard, SearchQuery, SearchResult,
    EvidenceLevel
)
from loader import load_knowledge_base
from query_validator import QueryValidator, create_validator_from_cards
import re


class SearchEngine:

    def __init__(
        self,
        kb_path: str = "knowledge_base",
        model_name: str = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
        load_on_init: bool = True
    ):

        self.model = SentenceTransformer(model_name)
        self.cards: List[KnowledgeCard] = []
        self.embeddings: Optional[np.ndarray] = None

        self.bm25: Optional[BM25Okapi] = None
        self.tokenized_corpus: List[List[str]] = []

        self.validator: Optional[QueryValidator] = None

        if load_on_init:
            self.load_knowledge_base(kb_path)

    def load_knowledge_base(self, directory: str):
        print(f"\n🔄 Загрузка базы знаний из {directory}...")

        self.cards = load_knowledge_base(directory)

        if not self.cards:
            print("⚠️ База знаний пуста!")
            return

        self.validator = create_validator_from_cards(self.cards)

        search_texts = [card.get_search_text() for card in self.cards]

        # 1. Семантические эмбеддинги
        print("Генерация семантических эмбеддингов...")
        self.embeddings = self.model.encode(
            search_texts,
            show_progress_bar=True,
            normalize_embeddings=True
        )

        # 2. BM25 индекс для keyword search
        print("Построение BM25 индекса...")
        self.tokenized_corpus = [self._tokenize(text) for text in search_texts]
        self.bm25 = BM25Okapi(self.tokenized_corpus)

        print(f"\nИндексировано {len(self.cards)} карточек.")
        print(f"   Векторы: {self.embeddings.shape}")
        print(f"   BM25: {len(self.tokenized_corpus)} документов")
        print(f"   Среднее кол-во токенов: {np.mean([len(t) for t in self.tokenized_corpus]):.1f}\n")

    def _tokenize(self, text: str) -> List[str]:

        text = text.lower()
        tokens = re.findall(r'[а-яёa-z0-9]+', text)
        return tokens

    def search(self, query: SearchQuery, min_score: float = 0.72) -> List[SearchResult]:

        if not self.cards or self.embeddings is None or self.bm25 is None:
            print("⚠️ Поиск невозможен: база не загружена")
            return []

        # Валидация запроса
        if self.validator:
            is_valid, error_msg, suggestions = self.validator.validate(query.query)
            if not is_valid and error_msg:
                print(f"⚠️ Запрос не прошёл валидацию: {error_msg}")
                return []

        # 1. Векторизуем запрос (семантика)
        normalized_query = (query.query or "").strip().lower()
        query_embedding = self.model.encode([normalized_query])[0]

        # 2. Косинусное сходство (семантический поиск)
        semantic_scores = self._cosine_similarity(query_embedding, self.embeddings)

        # 3. BM25 scores (keyword поиск)
        query_tokens = self._tokenize(normalized_query)
        bm25_scores = self.bm25.get_scores(query_tokens)

        # 4. Нормализация скоров (приводим к диапазону 0-1)
        semantic_scores_norm = self._normalize_scores(semantic_scores)
        bm25_scores_norm = self._normalize_scores(bm25_scores)

        # 5. ГИБРИДНОЕ СКОРИРОВАНИЕ
        # 70% семантика + 30% keywords (можно настроить)
        ALPHA = 0.7  # Вес семантики
        hybrid_scores = ALPHA * semantic_scores_norm + (1 - ALPHA) * bm25_scores_norm

        # 6. Применяем фильтры из запроса
        valid_indices = []
        for idx, card in enumerate(self.cards):
            if not self._matches_filters(card, query):
                continue
            if hybrid_scores[idx] >= min_score:
                valid_indices.append((idx, hybrid_scores[idx]))

        # 7. Сортировка: по релевантности + уровень доказательности
        evidence_weights = {
            EvidenceLevel.HIGH: 3,
            EvidenceLevel.MODERATE: 2,
            EvidenceLevel.LOW: 1,
            EvidenceLevel.EXPERT_OPINION: 0
        }

        valid_indices.sort(
            key=lambda x: (
                x[1],  # Релевантность
                evidence_weights.get(self.cards[x[0]].evidence_level, 0)  # Доказательность
            ),
            reverse=True
        )

        # 8. Формируем результаты
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

        # Защита от деления на ноль
        doc_norms = np.where(doc_norms == 0, 1e-10, doc_norms)

        similarities = np.dot(doc_vecs, query_vec) / (doc_norms * query_norm)
        return np.clip(similarities, 0, 1)

    def _normalize_scores(self, scores: np.ndarray) -> np.ndarray:

        min_score = scores.min()
        max_score = scores.max()

        if max_score - min_score < 1e-10:
            return np.zeros_like(scores)

        normalized = (scores - min_score) / (max_score - min_score)
        return np.clip(normalized, 0, 1)

    def _matches_filters(self, card: KnowledgeCard, query: SearchQuery) -> bool:
        """Проверяет, удовлетворяет ли карточка фильтрам запроса"""
        def _val(x):
            return getattr(x, "value", x)

        # Фильтр по домену
        if query.domain_filter and _val(card.domain) not in {_val(d) for d in query.domain_filter}:
            return False

        # Фильтр по категории
        if query.category_filter and _val(card.category) not in {_val(c) for c in query.category_filter}:
            return False

        # Фильтр по аудитории
        if query.audience_filter:
            card_audiences = {_val(a) for a in card.audience}
            query_audiences = {_val(a) for a in query.audience_filter}
            if not card_audiences.intersection(query_audiences):
                return False

        # Фильтр по уровню доказательности
        if query.min_evidence:
            evidence_order = [
                EvidenceLevel.HIGH,
                EvidenceLevel.MODERATE,
                EvidenceLevel.LOW,
                EvidenceLevel.EXPERT_OPINION,
            ]
            evidence_order_vals = [_val(e) for e in evidence_order]

            card_level_idx = evidence_order_vals.index(_val(card.evidence_level))
            query_level_idx = evidence_order_vals.index(_val(query.min_evidence))

            if card_level_idx > query_level_idx:
                return False

        return True

    def _extract_highlights(self, card: KnowledgeCard, query: str) -> Optional[Dict[str, List[str]]]:
        """Находит фрагменты текста карточки, содержащие слова из запроса"""
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
                    # Обрезаем до 200 символов
                    matches.append(
                        sent_stripped[:200] + "..." if len(sent_stripped) > 200 else sent_stripped
                    )

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