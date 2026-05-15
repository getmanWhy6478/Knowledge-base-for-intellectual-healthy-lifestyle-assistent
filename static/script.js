/**
 * Health Lifestyle Assistant - Frontend Script
 * Обработка запросов к API и отображение результатов
 */

// =============================================================================
// КОНФИГУРАЦИЯ
// =============================================================================
const API_BASE_URL = '';  // Пустая строка = тот же домен (localhost:8000)
const SEARCH_ENDPOINT = '/api/search';
const MAX_RESULTS = 10;
const BROWSE_DOMAINS_ENDPOINT = '/api/browse/domains';
const RELEVANCE_THRESHOLD = 0.38;

// =============================================================================
// ЭЛЕМЕНТЫ DOM
// =============================================================================
const searchInput = document.getElementById('queryInput');
const searchButton = document.getElementById('searchButton');
const resultsArea = document.getElementById('resultsArea');
const loader = document.getElementById('loader');
const disclaimerArea = document.getElementById('disclaimerArea');
const tabSearch = document.getElementById('tabSearch');
const tabBrowse = document.getElementById('tabBrowse');
const browsePanel = document.getElementById('browsePanel');
const domainSelect = document.getElementById('domainSelect');
const categorySelect = document.getElementById('categorySelect');
const cardsList = document.getElementById('cardsList');
const cardDetail = document.getElementById('cardDetail');
const browseCount = document.getElementById('browseCount');
const cardMeta = document.getElementById('cardMeta');

// =============================================================================
// ИНИЦИАЛИЗАЦИЯ
// =============================================================================
document.addEventListener('DOMContentLoaded', () => {
    // Привязка обработчиков событий
    if (searchButton) {
        searchButton.addEventListener('click', performSearch);
    }

    if (searchInput) {
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                performSearch();
            }
        });
    }

    // Показываем дисклеймер при загрузке
    showDisclaimer();

    // Переключение режимов
    if (tabSearch) tabSearch.addEventListener('click', () => setMode('search'));
    if (tabBrowse) tabBrowse.addEventListener('click', () => setMode('browse'));

    // Инициализация обзора базы
    if (domainSelect) domainSelect.addEventListener('change', onDomainChange);
    if (categorySelect) categorySelect.addEventListener('change', onCategoryChange);

    console.log('✅ Health Assistant frontend initialized');
});

// =============================================================================
// РЕЖИМЫ: ПОИСК / ОБЗОР БАЗЫ
// =============================================================================
let currentMode = 'search';
let currentBrowse = { domain: '', category: '' };

function setMode(mode) {
    if (mode !== 'search' && mode !== 'browse') return;
    currentMode = mode;

    // Табики
    if (tabSearch) tabSearch.classList.toggle('active', mode === 'search');
    if (tabBrowse) tabBrowse.classList.toggle('active', mode === 'browse');

    // Панели
    if (browsePanel) browsePanel.style.display = mode === 'browse' ? 'block' : 'none';
    if (resultsArea) resultsArea.style.display = mode === 'browse' ? 'none' : 'block';

    // Очистка
    clearResults();
    if (mode === 'browse') {
        initBrowseIfNeeded();
    }
}

// Делаем доступным для inline onclick в HTML
window.setMode = setMode;

let browseInitialized = false;
async function initBrowseIfNeeded() {
    if (browseInitialized) return;
    browseInitialized = true;
    await loadDomains();
}

// =============================================================================
// ОБЗОР БАЗЫ: ДОМЕНЫ → КАТЕГОРИИ → КАРТОЧКИ → ПРОСМОТР
// =============================================================================
async function loadDomains() {
    try {
        showLoader(true);
        const res = await fetch(`${API_BASE_URL}${BROWSE_DOMAINS_ENDPOINT}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        const domains = data.domains || [];

        if (!domainSelect) return;
        domainSelect.innerHTML = `<option value="">— выберите —</option>` + domains.map(d =>
            `<option value="${escapeHtml(d.id)}">${escapeHtml(d.title || d.id)} (${d.count})</option>`
        ).join('');

        // Сброс зависимых селектов/панелей
        resetBrowseSelections({ keepDomain: false });
    } catch (e) {
        showError(`Не удалось загрузить структуру базы: ${e.message}`);
    } finally {
        showLoader(false);
    }
}

function resetBrowseSelections({ keepDomain }) {
    if (!keepDomain && domainSelect) domainSelect.value = '';
    if (categorySelect) {
        categorySelect.value = '';
        categorySelect.disabled = true;
        categorySelect.innerHTML = `<option value="">— выберите —</option>`;
    }
    if (cardsList) cardsList.innerHTML = '';
    if (browseCount) browseCount.textContent = '';
    if (cardMeta) cardMeta.textContent = '';
    if (cardDetail) {
        cardDetail.className = 'card-detail-empty';
        cardDetail.textContent = 'Выберите карточку слева, чтобы увидеть содержимое.';
    }
    currentBrowse = { domain: keepDomain && domainSelect ? (domainSelect.value || '') : '', category: '' };
}

async function onDomainChange() {
    const domain = domainSelect ? (domainSelect.value || '') : '';
    currentBrowse.domain = domain;
    currentBrowse.category = '';

    if (!domain) {
        resetBrowseSelections({ keepDomain: false });
        return;
    }

    try {
        showLoader(true);
        const res = await fetch(`${API_BASE_URL}/api/browse/domains/${encodeURIComponent(domain)}/categories`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        const categories = data.categories || [];

        if (!categorySelect) return;
        categorySelect.disabled = false;
        categorySelect.innerHTML = `<option value="">— выберите —</option>` + categories.map(c =>
            `<option value="${escapeHtml(c.id)}">${escapeHtml(c.id)} (${c.count})</option>`
        ).join('');

        // сброс списка карточек/деталей
        if (cardsList) cardsList.innerHTML = '';
        if (browseCount) browseCount.textContent = '';
        if (cardMeta) cardMeta.textContent = '';
        if (cardDetail) {
            cardDetail.className = 'card-detail-empty';
            cardDetail.textContent = 'Выберите категорию, чтобы увидеть карточки.';
        }
    } catch (e) {
        showError(`Не удалось загрузить категории: ${e.message}`);
    } finally {
        showLoader(false);
    }
}

async function onCategoryChange() {
    const domain = domainSelect ? (domainSelect.value || '') : '';
    const category = categorySelect ? (categorySelect.value || '') : '';
    currentBrowse.domain = domain;
    currentBrowse.category = category;

    if (!domain || !category) {
        if (cardsList) cardsList.innerHTML = '';
        if (browseCount) browseCount.textContent = '';
        if (cardMeta) cardMeta.textContent = '';
        if (cardDetail) {
            cardDetail.className = 'card-detail-empty';
            cardDetail.textContent = 'Выберите карточку слева, чтобы увидеть содержимое.';
        }
        return;
    }

    try {
        showLoader(true);
        const res = await fetch(`${API_BASE_URL}/api/browse/domains/${encodeURIComponent(domain)}/categories/${encodeURIComponent(category)}/cards`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        const cards = data.cards || [];

        if (browseCount) browseCount.textContent = `Найдено: ${cards.length}`;
        renderCardsList(cards);

        if (cardDetail) {
            cardDetail.className = 'card-detail-empty';
            cardDetail.textContent = cards.length ? 'Выберите карточку слева, чтобы увидеть содержимое.' : 'В этой категории нет карточек.';
        }
    } catch (e) {
        showError(`Не удалось загрузить карточки: ${e.message}`);
    } finally {
        showLoader(false);
    }
}

function renderCardsList(cards) {
    if (!cardsList) return;
    if (!cards || cards.length === 0) {
        cardsList.innerHTML = `<div class="cards-list-empty">Карточек не найдено.</div>`;
        return;
    }

    cardsList.innerHTML = cards.map(c => `
        <button class="card-item" type="button" data-card-id="${escapeHtml(c.id)}" onclick="openCardById('${escapeHtml(c.id)}')">
            <div class="card-item-title">${escapeHtml(c.title || c.id)}</div>
            <div class="card-item-meta">
                <span class="pill">${escapeHtml(c.evidence_level || '')}</span>
                <span class="pill muted">${escapeHtml((c.updated || '').slice(0, 10))}</span>
            </div>
        </button>
    `).join('');
}

async function openCardById(cardId) {
    if (!cardId) return;
    try {
        showLoader(true);
        // подсветка выбранного элемента
        document.querySelectorAll('.card-item').forEach(el => {
            el.classList.toggle('active', el.dataset && el.dataset.cardId === cardId);
        });

        const res = await fetch(`${API_BASE_URL}/api/card/${encodeURIComponent(cardId)}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        const card = data.card;
        if (!card) throw new Error('Пустой ответ');

        // рендер детальной карточки (используем существующий шаблон для совместимости)
        if (cardMeta) {
            const parts = [
                card.domain ? `domain: ${card.domain}` : '',
                card.category ? `category: ${card.category}` : '',
                card.id ? `id: ${card.id}` : '',
            ].filter(Boolean);
            cardMeta.textContent = parts.join(' • ');
        }
        if (cardDetail) {
            cardDetail.className = 'card-detail';
            cardDetail.innerHTML = createCardHtml(card, null, 0);
        }
    } catch (e) {
        showError(`Не удалось открыть карточку: ${e.message}`);
    } finally {
        showLoader(false);
    }
}

// Доступно из inline onclick списка карточек
window.openCardById = openCardById;

// =============================================================================
// ОСНОВНАЯ ФУНКЦИЯ ПОИСКА
// =============================================================================
async function performSearch() {
    if (currentMode === 'browse') {
        // В режиме обзора Enter/кнопка не должны запускать поиск случайно
        setMode('search');
    }
    const query = searchInput ? searchInput.value.trim() : '';

    // Валидация ввода
    if (!query) {
        showNotification('⚠️ Введите запрос для поиска', 'warning');
        return;
    }

    if (query.length < 2) {
        showNotification('⚠️ Запрос должен содержать минимум 2 символа', 'warning');
        return;
    }

    // Очистка предыдущих результатов
    clearResults();
    showLoader(true);

    try {
        console.log('🔍 Отправка запроса:', query);

        const response = await fetch(`${API_BASE_URL}${SEARCH_ENDPOINT}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: query,
                top_k: MAX_RESULTS
            })
        });

        // Проверка статуса HTTP
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        console.log('✅ Ответ сервера:', data);

        // Обработка ответа
        handleApiResponse(data);

    } catch (error) {
        console.error('❌ Ошибка поиска:', error);
        showError(`Ошибка соединения: ${error.message}`);
    } finally {
        showLoader(false);
    }
}
// =============================================================================
// ОБРАБОТКА ОТВЕТА API
// =============================================================================
function handleApiResponse(data) {
    // 🔍 Поддержка обоих имён поля (data / results)
    const results = data.data || data.results || [];
    if (data.meta?.suggestions && data.meta.suggestions.length > 0) {
        showSuggestions(data.meta.suggestions);
    return;
}
    const warning = data.warning;
    const message = data.message || '';
    const disclaimer = data.disclaimer || '';

    // 1. Если есть критическое предупреждение безопасности
    if (warning && warning.is_critical) {
        showSafetyWarning(warning);
        return;
    }

    // 2. Если есть обычное предупреждение
    if (warning && warning.message) {
        showSafetyWarning(warning);
    }

    // 3. Если результатов нет
    if (!results || results.length === 0) {
        showNoResults(message || 'По вашему запросу ничего не найдено');
        return;
    }

    const maxScore = Math.max(...results.map(r => r.score || 0));

    if (maxScore < RELEVANCE_THRESHOLD) {
        console.log(`⚠️ Низкая релевантность: maxScore = ${maxScore.toFixed(3)} < ${RELEVANCE_THRESHOLD}`);
        showLowRelevance(results.length);
        return;
    }

    // 4. Отображаем результаты
    displayResults(results, message);

    // 5. Показываем дисклеймер
    if (disclaimer) {
        showDisclaimer(disclaimer);
    }
    function showLowRelevance(resultsCount) {
    if (!resultsArea) return;

    resultsArea.innerHTML = `
        <div class="low-relevance">
            <div class="low-relevance-icon">🤔</div>
            <h3>Найдено ${resultsCount} карточек, но они могут не соответствовать запросу</h3>
            <p>Уровень соответствия слишком низкий. Попробуйте уточнить запрос:</p>
            <div class="low-relevance-tips">
                <h4>💡 Рекомендации:</h4>
                <ul>
                    <li>Используйте более конкретные термины (например, "белки" вместо "питание")</li>
                    <li>Добавьте контекст (например, "для похудения", "при диабете")</li>
                    <li>Проверьте орфографию</li>
                    <li>Попробуйте синонимы</li>
                </ul>
            </div>
            <div class="low-relevance-actions">
                <button class="show-results-btn" onclick="forceShowResults()">
                    📋 Всё равно показать результаты
                </button>
            </div>
        </div>
    `;
}
function showSuggestions(suggestions) {
    if (!resultsArea) return;

    resultsArea.innerHTML = `
        <div class="query-suggestions">
            <div class="suggestions-icon">💡</div>
            <h3>Возможно, вы искали:</h3>
            <div class="suggestions-list">
                ${suggestions.map(s =>
                    `<button class="suggestion-chip" onclick="searchWithQuery('${escapeHtml(s)}')">
                        ${escapeHtml(s)}
                    </button>`
                ).join('')}
            </div>
            <p class="suggestions-hint">Нажмите на подсказку, чтобы выполнить поиск</p>
        </div>
    `;
}
function searchWithQuery(newQuery) {
    if (searchInput) searchInput.value = newQuery;
    performSearch();
}
window.searchWithQuery = searchWithQuery;

}

// =============================================================================
// ОТОБРАЖЕНИЕ РЕЗУЛЬТАТОВ
// =============================================================================
function displayResults(results, message) {
    if (!resultsArea) return;

    // Заголовок с количеством результатов
    const headerHtml = `
        <div class="results-header">
            <h2>📚 ${message || `Найдено ${results.length} рекомендаций`}</h2>
        </div>
    `;

    // Карточки результатов
    const cardsHtml = results.map((item, index) => {
        // 🔍 Поддержка разных структур ответа
        const card = item.card || item;
        const score = item.score || null;

        return createCardHtml(card, score, index);
    }).join('');

    resultsArea.innerHTML = headerHtml + cardsHtml;
}

// =============================================================================
// HTML ШАБЛОН КАРТОЧКИ
// =============================================================================
function createCardHtml(card, score, index) {
    if (!card) return '';

    // Безопасное экранирование HTML
    const escapeHtml = (text) => {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    };

    // Теги
    const tagsHtml = (card.tags || []).map(tag =>
        `<span class="tag">${escapeHtml(tag)}</span>`
    ).join('');

    // Оценка релевантности (для отладки)
    const scoreHtml = score ? `
        <div class="relevance-score">
            🔍 Релевантность: ${(score * 100).toFixed(0)}%
        </div>
    ` : '';

    // Ключевые свойства (если есть)
    const propertiesHtml = card.content && card.content.key_properties ? `
        <div class="card-properties">
            <h4>📊 Ключевые свойства:</h4>
            <ul>
                ${Object.entries(card.content.key_properties)
                    .slice(0, 4)
                    .map(([key, value]) => `<li><strong>${processMarkdown(key)}:</strong> ${processMarkdown(value)}</li>`)
                    .join('')}
            </ul>
        </div>
    ` : '';

    // Преимущества
    const benefitsHtml = card.content && card.content.benefits ? `
        <div class="card-benefits">
            <h4>✅ Преимущества:</h4>
            <ul>
                ${(card.content.benefits || []).slice(0, 3).map(b => `<li>${processMarkdown(b)}</li>`).join('')}
            </ul>
        </div>
    ` : '';
    // Формулировка правила (для правил/фактов)
    const ruleStatementHtml = card.content && card.content.rule_statement ? `
        <div class="card-section">
            <h4>📜 Формулировка правила:</h4>
            <div class="card-section-text">${processMarkdown(card.content.rule_statement)}</div>
        </div>
    ` : '';

    // Суть рекомендации (для правил/фактов)
    const essenceHtml = card.content && card.content.essence ? `
        <div class="card-section">
            <h4>💡 Суть рекомендации:</h4>
            <div class="card-section-text">${processMarkdown(card.content.essence)}</div>
        </div>
    ` : '';

    // Практическое применение (для правил/фактов)
    const practicalApplicationHtml = card.content && card.content.practical_application ? `
        <div class="card-section">
            <h4>🔧 Практическое применение:</h4>
            <div class="card-section-text">${processMarkdown(card.content.practical_application)}</div>
        </div>
    ` : '';

    // Важное предупреждение (универсальное)
    const specialwarningHtml = card.content && card.content.warning ? `
        <div class="card-warning" style="margin: 20px 0; padding: 15px 20px; background: var(--warning-light); border-radius: var(--radius-small); border-left: 4px solid var(--warning-color);">
            <strong>⚠️ Важное предупреждение:</strong>
            <div style="margin-top: 8px; color: var(--text-primary);">${processMarkdown(card.content.warning)}</div>
        </div>
    ` : '';

    // Рекомендации
        const recommendationsHtml = card.content && card.content.recommendations ? `
            <div class="card-recommendations">
                <h4>💡 Рекомендации:</h4>
                <ul>
                    ${(card.content.recommendations || []).slice(0, 8).map(r => `<li>${processMarkdown(r)}</li>`).join('')}
                </ul>
            </div>
        ` : '';

    // Источники
    const sourcesHtml = card.sources ? `
        <div class="card-sources">
            <h4>📚 Источники:</h4>
            <ol>
                ${(card.sources || []).slice(0, 3).map(s => `<li>${processMarkdown(s)}</li>`).join('')}
            </ol>
        </div>
    ` : '';
    const relatedTopicsHtml = card.content && card.content.related_topics ? `
    <div class="card-related-topics">
        <h4>🔗 Связанные темы:</h4>
        <div class="related-topics-list">
            ${(card.content.related_topics || []).map(topic => {
                // Парсим: "MNT-COND-001 — Тревожность (relates_to)"
                const match = topic.match(/([A-Z0-9\-]+)\s*—\s*(.+?)\s*\((\w+)\)/);
                if (match) {
                    const cardId = match[1];
                    const title = match[2];
                    const relationType = match[3];
                    return `
                        <a href="#" class="related-topic-link" onclick="openCardById('${cardId}'); return false;">
                            <span class="topic-id">${cardId}</span>
                            <span class="topic-title">${processMarkdown(title)}</span>
                            <span class="topic-type">${processMarkdown(relationType)}</span>
                        </a>
                    `;
                }
                return `<span class="related-topic-plain">${processMarkdown(topic)}</span>`;
            }).join('')}
        </div>
    </div>
` : '';

    // Универсальный рендер секций, которые раньше не выводились
    const renderTextSection = (title, text, icon) => {
        const value = (text || '').trim();
        if (!value) return '';
        return `
            <div class="card-section">
                <h4>${icon ? `${icon} ` : ''}${processMarkdown(title)}</h4>
                <div class="card-section-text">${processMarkdown(value)}</div>
            </div>
        `;
    };

    const renderListSection = (title, items, icon, maxItems = 5) => {
        const list = Array.isArray(items) ? items.filter(Boolean) : [];
        if (!list.length) return '';
        return `
            <div class="card-section">
                <h4>${icon ? `${icon} ` : ''}${processMarkdown(title)}</h4>
                <ul>
                    ${list.slice(0, maxItems).map(x => `<li>${processMarkdown(String(x))}</li>`).join('')}
                </ul>
            </div>
        `;
    };

    // Поля ниже не дублируем: rule_statement / essence / practical_application / warning
    // уже выведены отдельными блоками выше.
    const extraSectionsHtml = (card.content ? `
        ${renderTextSection('Тип', card.content.type, '🏷️')}
        ${renderTextSection('Вердикт', card.content.verdict, '🧾')}
        ${renderTextSection('Разбор', card.content.analysis, '🔎')}
        ${renderTextSection('Доказательная база', card.content.justification, '🧠')}
        ${renderListSection('Риски и ограничения', card.content.risks, '⚠️', 6)}
        ${renderListSection('Исключения и противопоказания', card.content.exceptions, '⛔', 6)}
        ${renderTextSection('Условия применимости', card.content.applicability, '🧭')}
        ${renderTextSection('Контекст', card.content.context, '🗺️')}
        ${renderTextSection('Корректная формулировка', card.content.correct_formulation, '✅')}
        ${renderListSection('Синонимы', card.content.synonyms, '🔁', 8)}
        ${renderTextSection('Контекст использования', card.content.usage_context, '🗣️')}
        ${renderListSection('Примеры употребления', card.content.usage_examples, '✍️', 6)}
        ${renderTextSection('Когда требуется внимание специалиста', card.content.visit, '👨‍️')}
    ` : '');

    return `
        <article class="knowledge-card" data-card-id="${escapeHtml(card.id || '')}">
            <header class="card-header">
                <h3 class="card-title">${escapeHtml(card.title || 'Без названия')}</h3>
                <div class="card-meta">
                    <span class="card-category">${escapeHtml(card.category || '')}</span>
                    <span class="card-domain">${escapeHtml(card.domain || '')}</span>
                    ${scoreHtml}
                </div>
            </header>

            <div class="card-content">
                ${(card.content && card.content.definition) ? `
                    <div class="card-definition">
                        <strong>Определение:</strong> ${processMarkdown(card.content.definition)}
                    </div>
                ` : ''}

                ${(() => {
                    const rawDesc = (card.content && card.content.description) ? String(card.content.description).trim() : '';
                    const rawDef = (card.content && card.content.definition) ? String(card.content.definition).trim() : '';
                    const typeVal = (card.content && card.content.type) ? String(card.content.type).trim() : '';
                    if (!rawDesc) return '';
                    const descNorm = rawDesc.replace(/\r\n/g, '\n');
                    const defNorm = rawDef.replace(/\r\n/g, '\n');
                    if (defNorm && descNorm === defNorm) return '';
                    if (defNorm && /^определение\s*\n/i.test(descNorm)) {
                        const body = descNorm.replace(/^определение\s*\n/i, '').trim();
                        if (body === defNorm) return '';
                    }
                    if (typeVal) {
                        const esc = typeVal.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
                        if (new RegExp(`^тип\\s*\\n\\s*${esc}\\s*$`, 'i').test(descNorm)) return '';
                        if (descNorm === typeVal) return '';
                    }
                    return `
                    <div class="card-description">
                        ${processMarkdown(rawDesc)}
                    </div>`;
                })()}

                ${specialwarningHtml}
                ${ruleStatementHtml}
                ${essenceHtml}
                ${propertiesHtml}
                ${benefitsHtml}
                ${practicalApplicationHtml}
                ${recommendationsHtml}
                ${extraSectionsHtml}
                ${relatedTopicsHtml}
                ${sourcesHtml}
            </div>

            <footer class="card-footer">
                <div class="card-tags">${tagsHtml}</div>
                <div class="card-evidence">
                    📊 Доказательность: <strong>${processMarkdown(card.evidence_level || 'N/A')}</strong>
                </div>
            </footer>
        </article>
    `;
}

// =============================================================================
// ПРЕДУПРЕЖДЕНИЯ БЕЗОПАСНОСТИ
// =============================================================================
function showSafetyWarning(warning) {
    if (!resultsArea) return;

    const icon = warning.is_critical ? '🚨' : '⚠️';
    const className = warning.is_critical ? 'alert-critical' : 'alert-warning';
    const actionText = getActionText(warning.action_recommended);

    resultsArea.innerHTML = `
        <div class="alert ${className}">
            <div class="alert-icon">${icon}</div>
            <div class="alert-content">
                <h3>${warning.is_critical ? 'Требуется медицинская помощь' : 'Обратите внимание'}</h3>
                <p>${escapeHtml(warning.message)}</p>
                ${actionText ? `<div class="alert-action">${actionText}</div>` : ''}
            </div>
        </div>
    `;
}

function getActionText(action) {
    const actions = {
        'emergency': '🚑 Вызовите скорую помощь: 103 или 112',
        'consult_doctor': '👨‍⚕️ Обратитесь к врачу в ближайшее время',
        'caution': '💡 Проконсультируйтесь со специалистом перед применением рекомендаций',
        'none': ''
    };
    return actions[action] || '';
}

// =============================================================================
// ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
// =============================================================================
function showLoader(show) {
    if (loader) {
        loader.style.display = show ? 'block' : 'none';
    }
    if (searchButton) {
        searchButton.disabled = show;
        searchButton.textContent = show ? '🔍 Поиск...' : '🔍 Найти';
    }
    if (searchInput) {
        searchInput.disabled = show;
    }
}

function clearResults() {
    if (resultsArea) {
        resultsArea.innerHTML = '';
    }
}

function showNoResults(message) {
    if (!resultsArea) return;

    resultsArea.innerHTML = `
        <div class="no-results">
            <div class="no-results-icon">🔍</div>
            <h3>Ничего не найдено</h3>
            <p>${escapeHtml(message)}</p>
            <div class="no-results-tips">
                <h4>Попробуйте:</h4>
                <ul>
                    <li>Изменить формулировку запроса</li>
                    <li>Использовать более общие термины</li>
                    <li>Проверить орфографию</li>
                </ul>
            </div>
        </div>
    `;
}

function showError(message) {
    if (!resultsArea) return;

    resultsArea.innerHTML = `
        <div class="alert alert-error">
            <div class="alert-icon">❌</div>
            <div class="alert-content">
                <h3>Ошибка сервера</h3>
                <p>${escapeHtml(message)}</p>
                <button class="retry-button" onclick="performSearch()">🔄 Повторить</button>
            </div>
        </div>
    `;
}

function showNotification(message, type = 'info') {
    // Создаём временное уведомление
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;

    document.body.appendChild(notification);

    // Анимация появления
    setTimeout(() => notification.classList.add('show'), 10);

    // Удаление через 3 секунды
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

function showDisclaimer(customText) {
    if (!disclaimerArea) return;

    const text = customText || 'Информация носит ознакомительный характер и не заменяет консультацию врача. При наличии симптомов обратитесь к специалисту.';

    disclaimerArea.innerHTML = `
        <div class="disclaimer">
            <strong>⚠️ Важное предупреждение:</strong>
            <p>${escapeHtml(text)}</p>
        </div>
    `;
}

// Безопасное экранирование HTML (глобальная функция)
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function processMarkdown(text) {
    if (!text) return '';

    // Сначала экранируем HTML для безопасности
    let processed = escapeHtml(text);

    // ✅ Жирный текст: **текст** → <strong>текст</strong>
    processed = processed.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

    // ✅ Курсив: *текст* → <em>текст</em>
    processed = processed.replace(/\*(.+?)\*/g, '<em>$1</em>');

    // ✅ Переносы строк: \n → <br>
    processed = processed.replace(/\n/g, '<br>');

    return processed;
}
// =============================================================================
// ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ (для будущего расширения)
// =============================================================================

// Поиск по категории
async function searchByCategory(category, top_k = 5) {
    const response = await fetch(`${API_BASE_URL}${SEARCH_ENDPOINT}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            query: '',
            category_filter: [category],
            top_k: top_k
        })
    });
    return await response.json();
}

// Получение карточки по ID
async function getCardById(cardId) {
    const response = await fetch(`${API_BASE_URL}/api/card/${cardId}`);
    if (!response.ok) throw new Error('Card not found');
    return await response.json();
}

// Экспорт результатов в консоль (для отладки)
function exportResultsToConsole() {
    console.log('📊 Экспорт результатов поиска:');
    const cards = document.querySelectorAll('.knowledge-card');
    cards.forEach((card, i) => {
        const titleEl = card.querySelector('.card-title');
        console.log(`${i + 1}. ${titleEl ? titleEl.textContent : ''}`);
    });
}

// Горячие клавиши
document.addEventListener('keydown', (e) => {
    // Ctrl+K или Cmd+K — фокус на поиск
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        if (searchInput) searchInput.focus();
    }

    // Escape — очистка поиска
    if (e.key === 'Escape') {
        if (searchInput) searchInput.blur();
        clearResults();
    }
});