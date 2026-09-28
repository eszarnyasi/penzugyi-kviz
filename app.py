
# Kiegészítések a korábbi apphoz:
# - 75% sikerességi küszöb
# - hibás kérdések listázása a végén
# - eredmények mentése CSV-be

import streamlit as st
import pandas as pd
import random
import time 
from datetime import datetime, timedelta

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTHQjC2gTbNQYZizic2IV0IgA8C1Q-SRMZlJqEJa-L9A5VPk888a3Zpgzsoz8IXXnO-3j0b5c4DP2kv/pub?gid=0&single=true&output=csv"

PASS_PERCENT = 75
EXAM_QUESTIONS = 60
EXAM_MINUTES = 60

@st.cache_data
def load_data():
    return pd.read_csv(CSV_URL)

df = load_data()

for key, default in {
    "score":0,"wrong":0,"answered":[],
    "wrong_questions":[],"exam_questions":[],
    "current":None,"exam_start":None
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

st.title("📚 Pénzügyi Vizsgafelkészítő")

mode = st.sidebar.radio("Mód", ["Gyakorlás","Vizsga"])

def next_question():
    if mode == "Vizsga":
        if not st.session_state.exam_questions:
            st.session_state.exam_questions = df.sample(min(EXAM_QUESTIONS,len(df))).to_dict("records")
            st.session_state.exam_start = datetime.now()

        remaining = [q for q in st.session_state.exam_questions if q["ID"] not in st.session_state.answered]
        return remaining[0] if remaining else None

    remaining = df[~df["ID"].isin(st.session_state.answered)]
    return remaining.sample(1).iloc[0] if len(remaining) else None

if st.session_state.current is None:
    st.session_state.current = next_question()

if mode == "Vizsga" and st.session_state.exam_start:
    left = (st.session_state.exam_start + timedelta(minutes=EXAM_MINUTES)) - datetime.now()
    if left.total_seconds() > 0:
        st.sidebar.metric("Hátralévő idő", f"{int(left.total_seconds()//60):02d}:{int(left.total_seconds()%60):02d}")
    else:
        st.session_state.current = None

q = st.session_state.current

if q is not None:
    st.subheader(q["Kerdes"])

    ans = st.radio(
        "Válasz",
        ["A","B","C"],
        format_func=lambda x:{
            "A":q["Opciod_A"],
            "B":q["Opciod_B"],
            "C":q["Opciod_C"]
        }[x]
    )

    if st.button("Beküldés"):
        correct = str(q["Helyes_Valasz"]).strip()

    if ans == correct:
        st.session_state.score += 1
        st.success("✅ Helyes")
        time.sleep(3)

    else:
        st.session_state.wrong += 1

        st.error(f"❌ Helytelen. Helyes válasz: {correct}")

        st.session_state.wrong_questions.append({
            "ID": q["ID"],
            "Kérdés": q["Kerdes"],
            "Te válaszod": ans,
            "Helyes": correct
        })

        time.sleep(8)

        st.session_state.answered.append(q["ID"])

        st.session_state.current = next_question()
        st.rerun()

else:
    total = st.session_state.score + st.session_state.wrong
    percent = (st.session_state.score/total*100) if total else 0

    st.header("📊 Eredmény")
    st.write(f"Helyes: {st.session_state.score}")
    st.write(f"Hibás: {st.session_state.wrong}")
    st.write(f"Sikeresség: {percent:.1f}%")

    if percent >= PASS_PERCENT:
        st.success(f"✅ Sikeres vizsga ({PASS_PERCENT}% felett)")
    else:
        st.error(f"❌ Sikertelen vizsga ({PASS_PERCENT}% alatt)")

    if st.session_state.wrong_questions:
        st.subheader("❌ Hibás kérdések")
        st.dataframe(pd.DataFrame(st.session_state.wrong_questions))

        results = pd.DataFrame(st.session_state.wrong_questions)
        results.to_csv("hibas_kerdesek.csv", index=False)

        st.download_button(
            "📥 Hibás kérdések letöltése",
            open("hibas_kerdesek.csv","rb"),
            file_name="hibas_kerdesek.csv"
        )
