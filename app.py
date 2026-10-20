import json
import os
from datetime import date
import streamlit as st

st.set_page_config(page_title="ZelenBot", page_icon="🤖", layout="centered")

DATA_FILE = "knowledge.json"
DEFAULT_KNOWLEDGE = {
    "JJS": [],
    "Forsaken": [],
    "Residence Massacre": [],
    "Общие советы": []
}

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                for key, value in DEFAULT_KNOWLEDGE.items():
                    data.setdefault(key, value.copy())
                return data
        except Exception:
            st.warning("Не удалось прочитать knowledge.json. Используется пустая база.")
    return {k: v.copy() for k, v in DEFAULT_KNOWLEDGE.items()}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def find_relevant_notes(question, knowledge, limit=5):
    terms = [t.strip(".,!?;:()[]{}\"'").lower() for t in question.split()]
    terms = [t for t in terms if len(t) > 2]
    results = []
    for category, items in knowledge.items():
        for item in items:
            title = item.get("title", "")
            content = item.get("content", "")
            tags = " ".join(item.get("tags", []))
            blob = f"{category} {title} {content} {tags}".lower()
            score = sum(1 for term in terms if term in blob)
            if score:
                results.append((score, category, item))
    results.sort(key=lambda x: x[0], reverse=True)
    return results[:limit]

def local_reply(question, knowledge):
    q = question.lower()
    if any(word in q for word in ["привет", "здравств", "хай", "ку", "hello", "hi"]):
        return "Привет! 💚 Я ZelenBot. Могу помочь с заметками и советами по Roblox. Спроси, например: «Что записано про JJS?»"
    if any(word in q for word in ["кто ты", "что ты умеешь", "что умеешь"]):
        return ("Я ZelenBot 🤖 — помощник по твоей базе знаний. Я умею искать сохранённые советы, "
                "помогать формулировать заметки и объяснять игровые стратегии. Сам я пока не захожу в Roblox и не управляю персонажем.")
    found = find_relevant_notes(question, knowledge)
    if found:
        lines = ["Нашёл в твоей базе знаний:"]
        for _, category, item in found:
            lines.append(f"**{category} — {item.get('title', 'Заметка')}**\n{item.get('content', '')}")
        lines.append("Если заметка устарела, проверь её в самой игре.")
        return "\n\n".join(lines)
    if any(word in q for word in ["добав", "запис", "заметк"]):
        return "Чтобы добавить совет, открой вкладку «➕ Добавить», выбери игру, напиши заголовок и сам совет, затем нажми «Добавить в базу»."
    return ("Пока я не нашёл подходящей заметки. Попробуй назвать игру и тему точнее "
            "(например, «JJS защита»), или добавь совет во вкладке «➕ Добавить».\n\n"
            "Это базовый режим без подключения внешней ИИ-модели. Чтобы включить полноценные ответы ИИ, "
            "нужен API-ключ, настроенный в секретах Streamlit; не отправляй ключ в чат и не публикуй его на GitHub.")

def ai_reply(question, history, knowledge):
    # Optional online AI mode. The key must be stored in Streamlit secrets, never in source code.
    api_key = None
    try:
        api_key = st.secrets.get("OPENAI_API_KEY")
    except Exception:
        api_key = os.environ.get("OPENAI_API_KEY")

    if not api_key:
        return local_reply(question, knowledge), False

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        notes = []
        for category, items in knowledge.items():
            for item in items[:30]:
                notes.append({
                    "game_or_section": category,
                    "title": item.get("title", ""),
                    "content": item.get("content", ""),
                    "tags": item.get("tags", [])
                })
        system_prompt = (
            "Ты ZelenBot — дружелюбный русскоязычный помощник по Roblox. "
            "Отвечай понятно и не слишком длинно. Помогай советами, объясняй термины и помогай "
            "оформлять заметки. Не утверждай, что ты можешь входить в Roblox, видеть экран или управлять персонажем. "
            "Не придумывай факты об игре: если не уверен, скажи об этом и предложи проверить актуальный источник. "
            "Не помогай с читами, эксплойтами, кражей аккаунтов или обходом правил. "
            "Сохранённые заметки пользователя — это контекст, а не гарантированно проверенные факты.\n\n"
            "Заметки из базы знаний пользователя:\n" + json.dumps(notes, ensure_ascii=False)
        )
        messages = [{"role": "system", "content": system_prompt}]
        for item in history[-10:]:
            if item.get("role") in ("user", "assistant"):
                messages.append({"role": item["role"], "content": item["content"]})
        messages.append({"role": "user", "content": question})
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=600,
        )
        answer = response.choices[0].message.content
        return (answer or "Я не смог сформулировать ответ. Попробуй ещё раз."), True
    except Exception as exc:
        return ("Не получилось получить ответ от ИИ. Проверь настройку API-ключа в Streamlit Secrets "
                "и доступность сервиса. Техническая ошибка: " + str(exc)[:250]), False

st.title("🤖 ZelenBot")
st.caption("Помощник по Roblox: база знаний + чат. Не является автономным игровым ботом.")

if "knowledge" not in st.session_state:
    st.session_state.knowledge = load_data()
data = st.session_state.knowledge
if "bot_name" not in st.session_state:
    st.session_state.bot_name = "ZELELBOT"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

with st.sidebar:
    st.header("Профиль")
    st.text_input("Имя бота", key="bot_name")
    st.caption("Пароль Roblox здесь не нужен и не хранится.")
    st.markdown("---")
    st.write("**Примеры сообщений для чата:**")
    st.code("Привет!\nЧто ты умеешь?\nНайди советы для JJS\nПомоги придумать заметку")

tab_chat, tab1, tab2, tab3 = st.tabs(["💬 Чат с ИИ", "📚 Знания", "➕ Добавить", "💾 Сохранить / экспорт"])

with tab_chat:
    st.subheader(f"Общение с {st.session_state.bot_name}")
    has_key = False
    try:
        has_key = bool(st.secrets.get("OPENAI_API_KEY"))
    except Exception:
        has_key = bool(os.environ.get("OPENAI_API_KEY"))
    if has_key:
        st.caption("Режим ИИ подключён. Ответы могут ошибаться — проверяй важные советы.")
    else:
        st.info("Сейчас работает базовый режим: поиск по сохранённым заметкам и простые ответы. Для полноценного ИИ нужен API-ключ, настроенный в Streamlit Secrets взрослым помощником. Не вставляй секретный ключ в чат или GitHub.")
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    prompt = st.chat_input("Напиши ZelenBot сообщение…")
    if prompt:
        prior_history = st.session_state.chat_history.copy()
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("ZelenBot думает..."):
                answer, online = ai_reply(prompt, prior_history, data)
            st.markdown(answer)
            if online:
                st.caption("Ответ создан ИИ; перепроверь игровые детали.")
        st.session_state.chat_history.append({"role": "assistant", "content": answer})
    if st.button("Очистить историю чата"):
        st.session_state.chat_history = []
        st.rerun()

with tab1:
    st.subheader(f"Знания {st.session_state.bot_name}")
    search = st.text_input("Поиск по заголовкам и заметкам", placeholder="Например: комбо, защита, карта")
    categories = list(data.keys())
    selected = st.selectbox("Раздел", ["Все разделы"] + categories)
    found = 0
    for category, items in data.items():
        if selected != "Все разделы" and category != selected:
            continue
        filtered = []
        for item in items:
            blob = (item.get("title", "") + " " + item.get("content", "") + " " + " ".join(item.get("tags", []))).lower()
            if search.lower() in blob:
                filtered.append(item)
        if filtered:
            st.markdown(f"### {category}")
            for i, item in enumerate(filtered):
                found += 1
                with st.expander(item.get("title", "Заметка")):
                    st.write(item.get("content", ""))
                    if item.get("tags"):
                        st.caption("Теги: " + ", ".join(item["tags"]))
                    if item.get("checked"):
                        st.caption("Проверено в игре")
                    if st.button("Удалить заметку", key=f"del_{category}_{i}_{item.get('title','')}"):
                        data[category].remove(item)
                        save_data(data)
                        st.rerun()
    if found == 0:
        st.info("Ничего не найдено. Попробуй другое слово или добавь заметку на вкладке «Добавить».")

with tab2:
    st.subheader("Добавить знание")
    category_options = list(data.keys()) + ["Новая игра / раздел"]
    category = st.selectbox("Игра или раздел", category_options)
    new_category = ""
    if category == "Новая игра / раздел":
        new_category = st.text_input("Название новой игры или раздела")
    title = st.text_input("Заголовок", placeholder="Например: защита от атаки")
    content = st.text_area("Совет или стратегия", placeholder="Опиши своими словами, что нужно помнить...")
    tags_text = st.text_input("Теги через запятую (необязательно)", placeholder="новичок, тактика")
    checked = st.checkbox("Я проверил этот совет в игре")
    if st.button("Добавить в базу", type="primary"):
        target = new_category.strip() if category == "Новая игра / раздел" else category
        if not target:
            st.error("Введи название раздела.")
        elif not title.strip() or not content.strip():
            st.error("Заполни заголовок и текст совета.")
        else:
            data.setdefault(target, [])
            data[target].append({
                "title": title.strip(),
                "content": content.strip(),
                "tags": [t.strip() for t in tags_text.split(",") if t.strip()],
                "checked": checked,
                "date_added": str(date.today())
            })
            save_data(data)
            st.success("Знание добавлено!")

with tab3:
    st.subheader("Сохранение и перенос")
    if st.button("Сохранить сейчас"):
        save_data(data)
        st.success("База сохранена в среде, где запущено приложение.")
    st.download_button(
        "Скачать копию знаний (JSON)",
        data=json.dumps(data, ensure_ascii=False, indent=2),
        file_name="zelenbot_knowledge.json",
        mime="application/json"
    )
    uploaded = st.file_uploader("Импортировать сохранённую базу JSON", type=["json"])
    if uploaded is not None:
        if st.button("Загрузить импортированную базу"):
            try:
                imported = json.load(uploaded)
                if isinstance(imported, dict):
                    for k, v in DEFAULT_KNOWLEDGE.items():
                        imported.setdefault(k, [])
                    st.session_state.knowledge = imported
                    save_data(imported)
                    st.success("База импортирована.")
                    st.rerun()
                else:
                    st.error("Файл должен содержать объект JSON.")
            except Exception:
                st.error("Не удалось прочитать этот JSON-файл.")

st.markdown("---")
st.caption("Важно: ZelenBot не входит в Roblox, не читает экран игры и не управляет персонажем. Интернет-гайды автоматически не загружает.")
