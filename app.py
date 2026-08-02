import streamlit as st
import pandas as pd

st.title("나의 첫 Streamlit 앱")

st.write("GitHub + Streamlit Cloud 테스트")

data = {
    "name": ["A", "B", "C"],
    "score": [90, 80, 70]
}

df = pd.DataFrame(data)

st.dataframe(df)