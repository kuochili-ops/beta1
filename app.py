import streamlit as st
import pandas as pd
from PIL import Image
import wikipedia
from rapidfuzz import process

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

# 🗂️ 別名字典
alias_map = {
    "acetaminophen": ["paracetamol", "tylenol", "撲熱息痛"],
    "ibuprofen": ["布洛芬", "advil", "motrin"],
    # 可以持續擴充
}

drug_list = list(alias_map.keys()) + [a for aliases in alias_map.values() for a in aliases]

def normalize_query(query):
    q = query.lower().strip()
    # Step 1: 別名比對
    for standard, aliases in alias_map.items():
        if q == standard or q in [a.lower() for a in aliases]:
            return standard
    # Step 2: 拼字修正
    match = process.extractOne(q, drug_list)
    if match and match[1] > 70:
        return match[0]
    return q  # 如果沒找到，就用原始輸入

# 🔍 查詢輸入
keyword = st.text_input("請輸入主成分或俗稱")

if keyword:
    normalized = normalize_query(keyword)
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
        st.warning(f"主成分名稱過於模糊，請選擇更具體的詞，例如：{e.options[:3]}")

    # 📊 查詢結果
    result = df[df["藥品名稱"].str.contains(normalized, case=False, na=False)].copy()

    if result.empty:
        st.warning("查無符合藥品")
    else:
        result["使用量"] = result["數量"].round(1)

        # 🔴 逐筆明細表格
        detail = result[["藥品代碼", "藥品名稱", "藥商", "使用量"]].copy()
        detail.insert(0, "序號", range(1, len(detail) + 1))
        st.write("🔴 查詢結果（逐筆明細）：")
        st.dataframe(detail.set_index("序號"))

        # ✅ 累計表格
        summary = result.groupby("藥品名稱", as_index=False)["使用量"].sum()
        summary.rename(columns={"使用量": "累計總量"}, inplace=True)
        summary["累計總量"] = summary["累計總量"].round(1)
        summary.insert(0, "序號", range(1, len(summary) + 1))
        st.write("✅ 查詢結果（藥品同規格分類累計）：")
        st.dataframe(summary.set_index("序號"))

        # ⬇️ 提供下載功能
        csv = summary.to_csv(index=False, encoding="utf-8-sig")
        file_name = f"{normalized}_累計查詢結果.csv"
        st.download_button(
            label="下載累計查詢結果 CSV",
            data=csv,
            file_name=file_name,
            mime="text/csv",
        )
else:
    st.info("請輸入主成分以進行查詢")

# 🖼️ 郵票圖片
stamp = Image.open("white6_stamp.jpg")
st.image(stamp, caption="白六航空 壹圓 郵票", width=90)
