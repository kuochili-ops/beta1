import streamlit as st
import pandas as pd

st.title("2024 健保申報藥品數量查詢介面（初代測試機）")

df = pd.read_csv(
    "merged_pay2024.csv",
    encoding="utf-8",
    usecols=["藥品代碼", "藥品名稱", "數量", "藥商"],  # 加入藥商欄位
    low_memory=False
)

keyword = st.text_input("請輸入主成分")

if keyword:
    result = df[df["藥品名稱"].str.contains(keyword, case=False, na=False)].copy()

    if result.empty:
        st.warning("查無符合藥品")
    else:
        result["使用量"] = result["數量"].round(1)

        # 🔴 逐筆明細表格：增加「藥商」欄位
        detail = result[["藥品代碼", "藥品名稱", "藥商", "使用量"]].copy()
        detail.insert(0, "序號", range(1, len(detail) + 1))
        st.write("🔴 查詢結果（逐筆明細）：")
        st.dataframe(detail.set_index("序號"))

        # ✅ 累計表格：維持原有顯示方式
        summary = result.groupby("藥品名稱", as_index=False)["使用量"].sum()
        summary.rename(columns={"使用量": "累計總量"}, inplace=True)
        summary["累計總量"] = summary["累計總量"].round(1)
        summary.insert(0, "序號", range(1, len(summary) + 1))
        st.write("✅ 查詢結果（同藥品名稱規格累計）：")
        st.dataframe(summary.set_index("序號"))

        # 提供下載功能
        csv = summary.to_csv(index=False, encoding="utf-8-sig")
        file_name = f"{keyword}_累計查詢結果.csv"
        st.download_button(
            label="下載累計查詢結果 CSV",
            data=csv,
            file_name=file_name,
            mime="text/csv",
        )
else:
    st.info("請輸入主成分以進行查詢")
