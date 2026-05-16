document:
  type: "knowledge_base_architecture"
  title: "Архитектура базы знаний ЗОЖ"
# 1. КЛЮЧЕВЫЕ СУЩНОСТИ ГЛОБАЛЬНОЙ ПРЕДМЕТНОЙ ОБЛАСТИ

global_domain:
  name: "Здоровый Образ Жизни (ЗОЖ)"
  description: "Интегративная система знаний о поддержании и укреплении физического, ментального и социального благополучия"
  
  core_entities:
    - id: "GLB-GLOSS-001"
      name: "Здоровье"
      type: "glossary"
      description: "Состояние полного физического, душевного и социального благополучия"
      
    - id: "MNT-GLOSS-001"
      name: "Ментальное здоровье"
      type: "glossary"
      description: "Компонент общего здоровья, включающий эмоциональное и психологическое благополучие"
      
    - id: "GLB-GLOSS-002"
      name: "Физическое здоровье"
      type: "glossary"
      description: "Компонент общего здоровья, включающий эффективность физиологических систем"
      
    - id: "GLB-GLOSS-003"
      name: "Социальное здоровье"
      type: "glossary"
      description: "Способность формировать и поддерживать удовлетворительные межличностные отношения"
      
    - id: "GLB-GLOSS-004"
      name: "Образ жизни и здоровье"
      type: "glossary"
      description: "Взаимосвязь между повседневными привычками и состоянием здоровья"
      
    - id: "GLB-GLOSS-006"
      name: "Энергетический баланс"
      type: "glossary"
      description: "Соотношение между поступлением энергии и её расходом"

  entity_classes:
    - class: "glossary"
      prefix: "GLB-GLOSS-XXX / NUT-GLOSS-XXX / MNT-GLOSS-XXX / SPR-GLOSS-XXX"
      purpose: "Базовые термины и определения"
      
    - class: "condition"
      prefix: "MNT-COND-XXX"
      purpose: "Состояния, расстройства, заболевания"
      
    - class: "habit"
      prefix: "MNT-HABIT-XXX / NUT-HABIT-XXX / SPR-HABIT-XXX"
      purpose: "Устойчивые паттерны поведения (полезные и вредные)"
      
    - class: "rule"
      prefix: "MNT-RULE-XXX / NUT-RULE-XXX / SPR-RULE-XXX"
      purpose: "Практические рекомендации и протоколы"
      
    - class: "technique"
      prefix: "MNT-TECH-XXX / SPR-TECH-XXX"
      purpose: "Конкретные методики и упражнения"
      
    - class: "self_help"
      prefix: "MNT-SELF-XXX"
      purpose: "Пошаговые алгоритмы действий в конкретных ситуациях"
      
    - class: "fact"
      prefix: "GLB-FACT-XXX / MNT-FACT-XXX"
      purpose: "Научно подтверждённые утверждения"
      
    - class: "myth"
      prefix: "GLB-MYTH-XXX / MNT-MYTH-XXX"
      purpose: "Распространённые заблуждения с опровержениями"
      
    - class: "cross"
      prefix: "GLB-CROSS-XXX"
      purpose: "Межпредметные связи между доменами"

    - class: "diets"
      prefix: "NUT-DIET-XXX"
      purpose: "Полезные диеты"

    - class: "nutrients"
      prefix: "NUT-NUTR-XXX"
      purpose: "Нутриенты и их описания"

    - class: "products"
      prefix: "NUT-PROD-XXX"
      purpose: "Продукты, часто используемые в диетах"
    
    - class: "exercises"
      prefix: "SPR-EXER-XXX"
      purpose: "Наиболее полезные упражнения"
    
    - class: "programs"
      prefix: "SPR-PROG-XXX"
      purpose: "Программы для набора формы и восстановления"

    - class: "sports"
      prefix: "SPR-PROF-XXX"
      purpose: "Виды спорта, наиболее полезные для организма"


# 2. СВЯЗИ МЕЖДУ СУЩНОСТЯМИ

relationships:
  allowed_types:
    - "is_part_of"
    - "relates_to"
    - "depends_on"
    - "contradicts"
    - "supplements"
    - "specializes"
    - "generalizes"
    - "requires"
    - "synergy_with"
    - "risk_with"

  key_connections:
    - from: "MNT-GLOSS-001"
      to: "GLB-GLOSS-001"
      type: "is_part_of"
      description: "Ментальное здоровье является частью общего здоровья"
      
    - from: "MNT-GLOSS-002"
      to: "MNT-GLOSS-004"
      type: "depends_on"
      description: "Стресс зависит от эмоциональной регуляции"
      
    - from: "MNT-HABIT-003"
      to: "MNT-COND-002"
      type: "risk_with"
      description: "Хронический недосып повышает риск депрессии"
      
    - from: "MNT-RULE-007"
      to: "MNT-COND-001"
      type: "supplements"
      description: "Физическая активность дополняет лечение тревожности"
      
    - from: "GLB-CROSS-001"
      to: "MNT-GLOSS-001"
      type: "synergy_with"
      description: "Питание синергично влияет на ментальное здоровье"

# 3. ТОЧКИ ПЕРЕСЕЧЕНИЯ МЕЖДУ ТРЕМЯ ПРЕДМЕТНЫМИ ОБЛАСТЯМИ

intersection_points:
  nutrition_mental:
    name: "Питание и Ментальное здоровье"
    cross_card: "GLB-CROSS-001"
    key_concepts:
      - "Ось кишечник-мозг"
      - "Нейромедиаторный синтез"
      - "Системное воспаление"
      - "Микробиом кишечника"
    shared_entities:
      - "MNT-GLOSS-027"  # Питание и ментальное здоровье
      - "NUT-GLOSS-009"  # Ось кишечник-мозг
      - "MNT-HABIT-005"  # Практика осознанного питания
      - "MNT-COND-002"   # Депрессия (связь с питанием)
    mechanisms:
      - "Синтез серотонина в кишечнике (90%)"
      - "Влияние омега-3 на нейропластичность"
      - "Воспаление как фактор риска депрессии"
      - "Витамины группы B для нейромедиаторов"

  sport_mental:
    name: "Спорт и Ментальное здоровье"
    cross_card: "GLB-CROSS-002"
    key_concepts:
      - "Нейрохимические изменения"
      - "Физиологическая регуляция стресса"
      - "Психосоциальные факторы"
      - "Самоэффективность"
    shared_entities:
      - "MNT-RULE-007"   # Правило физической активности
      - "SPR-GLOSS-001"  # Тренировочный стимул
      - "MNT-COND-001"   # Тревожность
      - "MNT-FACT-001"   # Факт о физической активности
    mechanisms:
      - "Выработка эндорфинов и BDNF"
      - "Снижение уровня кортизола"
      - "Улучшение вариабельности сердечного ритма"
      - "Социальная вовлечённость в групповых тренировках"

  nutrition_sport:
    name: "Питание и Спорт"
    cross_card: "GLB-CROSS-006"
    key_concepts:
      - "Энергетический баланс"
      - "Восстановление после нагрузки"
      - "Нутриенты для производительности"
      - "Гидратация"
    shared_entities:
      - "GLB-GLOSS-011"  # Энергетический баланс
      - "GLB-GLOSS-012"  # Восстановление
      - "SPR-GLOSS-007"  # Нутриенты для производительности
      - "GLB-GLOSS-013"  # Гидратация
    mechanisms:
      - "Белковый синтез для мышечного восстановления"
      - "Углеводы для гликогена"
      - "Электролитный баланс при нагрузке"
      - "Антиоксиданты для защиты от оксидативного стресса"

  triple_intersection:
    name: "Питание + Спорт + Ментальное здоровье"
    cross_card: "GLB-CROSS-011"
    key_concepts:
      - "Комплексное влияние образа жизни"
      - "Системная регуляция"
      - "Поведенческая взаимозависимость"
      - "Психосоциальное усиление"
    shared_entities:
      - "GLB-GLOSS-006"  # Образ жизни и здоровье
      - "GLB-GLOSS-019"  # Баланс нагрузки и отдыха
      - "GLB-GLOSS-020"  # Индивидуализация подхода
      - "MNT-GLOSS-001"  # Ментальное здоровье
    synergistic_effects:
      - "Качественный сон усиливает эффект от тренировок и питания"
      - "Физическая активность улучшает качество сна и аппетит"
      - "Сбалансированное питание поддерживает энергию для активности"
      - "Социальные связи усиливают приверженность здоровым привычкам"

# 4. ИЕРАРХИЯ КОНЦЕПТОВ ОТ ОБЩЕГО К ЧАСТНОМУ

concept_hierarchy:
  level_1_most_general:
    name: "Глобальное здоровье"
    entities:
      - "GLB-GLOSS-001"  # Здоровье
      - "GLB-GLOSS-004"  # Образ жизни и здоровье
      - "GLB-GLOSS-006"  # Здоровый образ жизни

  level_2_domain_level:
    name: "Предметные области ЗОЖ"
    entities:
      - "MNT-GLOSS-001"  # Ментальное здоровье
      - "GLB-GLOSS-003"  # Физическое здоровье
      - "GLB-GLOSS-013"  # Здоровое питание

  level_3_specialized:
    name: "Специализированные концепты"
    entities:
      - "MNT-GLOSS-002"  # Стресс
      - "MNT-GLOSS-008"  # Циркадные ритмы
      - "MNT-GLOSS-009"  # Гигиена сна
      - "NUT-GLOSS-025"  # Гомеостаз
      - "NUT-GLOSS-003"  # Калорийность
      - "SPR-GLOSS-001"  # Активный отдых
      - "SPR-GLOSS-018"  # Восстановление

# 5. МЕЖПРЕДМЕТНЫЕ КАРТОЧКИ (CROSS-DOMAIN)

cross_domain_cards:
  - id: "GLB-CROSS-001"
    title: "Влияние питания на ментальное здоровье"
    domains: ["nutrition", "mental"]
    key_mechanisms:
      - "Ось кишечник-мозг"
      - "Синтез нейромедиаторов"
      - "Системное воспаление"
      
  - id: "GLB-CROSS-002"
    title: "Влияние физической активности на ментальное здоровье"
    domains: ["sport", "mental"]
    key_mechanisms:
      - "Нейрохимические изменения"
      - "Физиологическая регуляция стресса"
      - "Психосоциальные факторы"
      
  - id: "GLB-CROSS-003"
    title: "Влияние силовых тренировок на когнитивные функции"
    domains: ["sport", "mental"]
    key_mechanisms:
      - "Нейротрофическая стимуляция"
      - "Сосудистые эффекты"
      - "Гормональная модуляция"
      
  - id: "GLB-CROSS-004"
    title: "Влияние йоги и медитативных практик на стрессоустойчивость"
    domains: ["sport", "mental"]
    key_mechanisms:
      - "Вегетативная регуляция"
      - "Нейровоспаление"
      - "Когнитивно-эмоциональная перестройка"
      
  - id: "GLB-CROSS-005"
    title: "Влияние режима сна на спортивные показатели"
    domains: ["mental", "sport"]
    key_mechanisms:
      - "Гормональная регуляция"
      - "Нейрокогнитивные функции"
      - "Иммунная функция и воспаление"
      
  - id: "GLB-CROSS-006"
    title: "Влияние гидратации на когнитивные функции и настроение"
    domains: ["nutrition", "mental", "sport"]
    key_mechanisms:
      - "Церебральная перфузия"
      - "Электролитный баланс"
      - "Терморегуляция"
      
  - id: "GLB-CROSS-007"
    title: "Влияние белкового питания на восстановление и ментальное состояние"
    domains: ["nutrition", "sport", "mental"]
    key_mechanisms:
      - "Мышечный синтез"
      - "Нейромедиаторный синтез"
      - "Гликемическая стабильность"
      
  - id: "GLB-CROSS-008"
    title: "Влияние углеводов на энергию и эмоциональную стабильность"
    domains: ["nutrition", "mental", "sport"]
    key_mechanisms:
      - "Гликемическая регуляция"
      - "Серотониновый путь"
      - "Когнитивная функция"
      
  - id: "GLB-CROSS-009"
    title: "Влияние микронутриентов на нейропластичность и восстановление"
    domains: ["nutrition", "mental", "sport"]
    key_mechanisms:
      - "Антиоксидантная защита"
      - "Нейротрофическая поддержка"
      - "Минеральная регуляция"
      
  - id: "GLB-CROSS-010"
    title: "Взаимосвязь циркадных ритмов, питания и физической активности"
    domains: ["nutrition", "sport", "mental"]
    key_mechanisms:
      - "Метаболическая синхронизация"
      - "Гормональная регуляция"
      - "Когнитивная продуктивность"
---