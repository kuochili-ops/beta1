import streamlit as st
import pandas as pd
from PIL import Image
import wikipedia
import difflib

# 🛠️ 頁面設定
st.set_page_config(page_title="健保藥品查詢介面", layout="centered")

# 🏷️ 標題
st.title("2024 健保申報藥品數量查詢介面（進化版）")

# 📄 讀取 CSV 檔案
df = pd.read_csv(
    "merged_pay2024.csv",
    encoding="utf-8",
    usecols=["藥品代碼", "藥品名稱", "數量", "藥商"],
    low_memory=False
)

# 🗂️ 別名字典（俗稱 ↔ 學名）
alias_map = {
    "acetylsalicylic acid": ["aspirin", "阿司匹林", "乙醯水楊酸"],
    "acetaminophen": ["paracetamol", "tylenol", "撲熱息痛"],
    "ibuprofen": ["布洛芬", "advil", "motrin"],
    "terlipressin": ["特利加壓素", "TERLIPRESSIN", "特利普雷辛"],
}

# 建立完整藥品清單（標準名 + 別名）
drug_list = list(alias_map.keys()) + [a for aliases in alias_map.values() for a in aliases]

# 🔍 標準化查詢
def normalize_query(query, alias_map):
    q = query.lower().strip()
    for standard, aliases in alias_map.items():
        if q == standard.lower() or q in [a.lower() for a in aliases]:
            return standard, None
    match = difflib.get_close_matches(q, drug_list, n=1, cutoff=0.7)
    if match:
        return match[0], q
    return q, None

# 🔍 查詢輸入
keyword = st.text_input("請輸入主成分或俗稱")

if keyword:
    normalized, original = normalize_query(keyword, alias_map)

    if original and normalized != original:
        st.info(f"您是不是要查詢：**{normalized}**？（原始輸入：{original}）")
    else:
        st.write(f"🔎 標準化查詢：**{normalized}**")

    # 📘 Wikipedia 查詢用途
    wikipedia.set_lang("zh")
    try:
        summary = wikipedia.summary(normalized, sentences=2)
        st.write("📘 主成分用途（來自 Wikipedia）：")
        st.info(summary)
        page = wikipedia.page(normalized)
        st.markdown(f"[🔗 查看完整 Wikipedia 頁面]({page.url})")
    except wikipedia.exceptions.PageError:
        st.warning("找不到 Wikipedia 頁面，可能需要更精確的主成分名稱。")
    except wikipedia.exceptions.DisambiguationError as e:
        st.warning(f"主成分名稱過於模糊，請選擇更具體的詞，例如：{e.options
