import streamlit as st
import pandas as pd
import plotly.express as px

st.title("나의 첫 Streamlit 앱")

st.write("GitHub + Streamlit Cloud 테스트")

data = {
    "name": ["A", "B", "C"],
    "score": [90, 80, 70]
}

df = pd.DataFrame(data)

st.dataframe(df)


st.title("고객 분석 Dashboard")

df = pd.DataFrame({
    "고객": ["A", "B", "C"],
    "매출": [100, 200, 300]
})

fig = px.bar(df, x="고객", y="매출")

st.plotly_chart(fig)