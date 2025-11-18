import streamlit as st
import pandas as pd
from PIL import Image
import wikipedia
import difflib

# 🛠️ 頁面設定
st.set_page_config(page_title="健保藥品查詢介面", layout="centered")
st.title("2024 健保申報藥品數量查詢介面（進化版）")

# 📄 讀取 CSV 檔案（包含支付價欄位）
df = pd.read_csv(
    "merged_pay2024.csv",
    encoding="utf-8",
    usecols=["藥品代碼", "藥品名稱", "數量", "藥商", "支付價"],
    low_memory=False
)

# 🗂️ 別名字典（俗稱 ↔ 學名）
alias_map = {
    "acetylsalicylic acid": ["aspirin", "阿司匹林", "乙醯水楊酸"],
    "acetaminophen": ["paracetamol", "tylenol", "撲熱息痛"],
    "ibuprofen": ["布洛芬", "advil", "motrin"],
    "terlipressin": ["特利加壓素", "TERLIPRESSIN", "特利普雷辛"],
}

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
        options = ", ".join(e.options[:3])
        st.warning(f"主成分名稱過於模糊，請選擇更具體的詞，例如：{options}")

    # 📊 查詢結果
    result = df[df["藥品名稱"].str.contains(normalized, case=False, na=False)].copy()

    if result.empty:
        st.warning("查無符合藥品")
    else:
        # 強制轉換支付價為數值型態
        result["使用量"] = result["數量"].round(1)
        result["支付價"] = pd.to_numeric(result["支付價"], errors="coerce").round(1)

        # 🔴 逐筆明細表格（加上支付價與總金額）
        detail = result[["藥品代碼", "藥品名稱", "藥商", "使用量", "支付價"]].copy()
        detail.insert(0, "序號", range(1, len(detail) + 1))
        detail["總金額"] = (detail["使用量"] * detail["支付價"]).round(1)
        detail = detail.reset_index(drop=True)

        st.write("🔴 查詢結果（逐筆明細）：")
        st.dataframe(detail, hide_index=True)
        st.caption(f"共 {len(detail)} 筆")

        # ✅ 藥品同名稱累計表格（移除支付價，增加百分比）
        summary = result.groupby("藥品名稱", as_index=False).agg(
            {"使用量": "sum", "支付價": "mean"}
        )
        summary.rename(columns={"使用量": "累計總量"}, inplace=True)
        summary["累計總量"] = summary["累計總量"].round(1)
        summary["累計總金額"] = (summary["累計總量"] * summary["支付價"]).round(1)

        total_amount = summary["累計總金額"].sum()
        summary["百分比"] = (summary["累計總金額"] / total_amount * 100).round(1)

        summary = summary[["藥品名稱", "累計總量", "累計總金額", "百分比"]].copy()
        summary.insert(0, "序號", range(1, len(summary) + 1))
        summary = summary.reset_index(drop=True)

        st.write("✅ 查詢結果（藥品同名稱累計）：")
        st.dataframe(summary, hide_index=True)
        st.caption(f"共 {len(summary)} 筆")

        # 🏢 藥商累計總金額表格（只顯示藥商、總金額、百分比）
        company_summary = result.groupby("藥商", as_index=False).agg(
            {"使用量": "sum", "支付價": "mean"}
        )
        company_summary["累計總金額"] = (company_summary["使用量"] * company_summary["支付價"]).round(1)

        total_company_amount = company_summary["累計總金額"].sum()
        company_summary["百分比"] = (company_summary["累計總金額"] / total_company_amount * 100).round(1)

        company_summary = company_summary[["藥商", "累計總金額", "百分比"]].copy()
        company_summary.insert(0, "序號", range(1, len(company_summary) + 1))
        company_summary = company_summary.reset_index(drop=True)

        st.write("🏢 查詢結果（藥商累計總金額）：")
        st.dataframe(company_summary, hide_index=True)
        st.caption(f"共 {len(company_summary)} 家藥商")

        # ⬇️ 提供下載功能（下載藥品累計結果）
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
