import json
import os
from datetime import date
import streamlit as st

st.set_page_config(page_title="ZelenBot", page_icon="🤖", layout="centered")
st.title("🤖 ZelenBot")
st.caption("Личная база знаний для Roblox — это справочник, не автономный игровой бот.")

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

if "knowledge" not in st.session_state:
    st.session_state.knowledge = load_data()

data = st.session_state.knowledge
if "ZELELBOT" not in st.session_state:
    st.session_state.bot_name = "ZELELBOT"

with st.sidebar:
    st.header("Профиль")
    st.text_input("Имя бота", key="bot_name")
    st.caption("Пароль Roblox здесь не нужен и не хранится.")
    st.markdown("---")
    st.write("**Команды, которые можно попросить:**")
    st.code("Найди советы для JJS\nПокажи тактики Forsaken\nДобавь новую заметку\nНайди по слову: блок")

tab1, tab2, tab3 = st.tabs(["📚 Знания", "➕ Добавить", "💾 Сохранить / экспорт"])

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
            st.success("Знание добавлено и сохранено в knowledge.json!")

with tab3:
    st.subheader("Сохранение и перенос")
    if st.button("Сохранить сейчас"):
        save_data(data)
        st.success("База сохранена в knowledge.json в среде, где запущено приложение.")
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
st.caption("Важно: приложение хранит заметки. Оно не входит в Roblox, не читает экран игры и не управляет персонажем. Оно не загружает интернет-гайды автоматически.")
