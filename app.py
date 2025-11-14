import streamlit as st
import pandas as pd

st.title("2024 健保申報藥品數量查詢介面（初代測試機）")

# 直接讀取同目錄下的 CSV 檔案
df = pd.read_csv("pay2024(UTF-8).csv", encoding="utf-8")

keyword = st.text_input("請輸入主成分")

if keyword:
    # 篩選藥品名稱中包含主成分的項目
    result = df[df["藥品名稱"].str.contains(keyword, case=False, na=False)]

    # 數字格式化：使用量保留一位小數
    result["使用量"] = result["數量"].round(1)

    # 🔴 顯示逐筆明細表格（含代碼）
    detail = result[["藥品代碼", "藥品名稱", "使用量"]].copy()
    detail.insert(0, "序號", range(1, len(detail) + 1))
    st.write("🔴 查詢結果（逐筆明細）：")
    st.dataframe(detail.set_index("序號"))

    # ✅ 顯示加總表格（依藥品名稱）
    summary = result.groupby("藥品名稱", as_index=False)["使用量"].sum()
    summary.rename(columns={"使用量": "累計總量"}, inplace=True)
    summary["累計總量"] = summary["累計總量"].round(1)
    summary.insert(0, "序號", range(1, len(summary) + 1))
    st.write("✅ 查詢結果（同藥品名稱規格累計）：")
    st.dataframe(summary.set_index("序號"))

    
    # 提供下載功能
    csv = summary.to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        label="下載累計查詢結果 CSV",
        data=csv,
        file_name="累計查詢結果.csv",
        mime="text/csv",
    )


