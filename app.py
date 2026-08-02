import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import os

# ------------------
# 설정
# ------------------

st.set_page_config(
    page_title="Music Store BI Dashboard",
    layout="wide"
)


# DB 연결

@st.cache_resource
def get_connection():
    return sqlite3.connect(
        "data/chinook.db",
        check_same_thread=False
    )


conn = get_connection()

st.write(os.listdir())

# DB 연결 확인
st.write("DB 연결 성공")

tables = pd.read_sql("""
SELECT name
FROM sqlite_schema
WHERE type='table'
""", conn)

st.write(tables)



# ------------------
# 데이터 함수
# ------------------

@st.cache_data
def load_data(sql):

    return pd.read_sql(
        sql,
        conn
    )



# ------------------
# KPI
# ------------------

st.title("🎵 Music Store BI Dashboard")


kpi = load_data("""
SELECT
SUM(Total) revenue,
COUNT(*) orders,
COUNT(DISTINCT CustomerId) customers
FROM Invoice
""")


col1,col2,col3 = st.columns(3)


col1.metric(
    "총 매출",
    f"${kpi.revenue[0]:,.0f}"
)

col2.metric(
    "주문 수",
    kpi.orders[0]
)

col3.metric(
    "고객 수",
    kpi.customers[0]
)



# ------------------
# 월별 매출
# ------------------

st.subheader("월별 매출")


monthly = load_data("""
SELECT
strftime('%Y-%m',InvoiceDate) month,
SUM(Total) revenue
FROM Invoice
GROUP BY month
ORDER BY month
""")


fig = px.line(
    monthly,
    x="month",
    y="revenue",
    markers=True
)


st.plotly_chart(
    fig,
    use_container_width=True
)



# ------------------
# 인기 Artist
# ------------------

st.subheader("Top Artist")


artist = load_data("""
SELECT
Artist.Name,
SUM(InvoiceLine.UnitPrice) revenue
FROM Artist
JOIN Album
ON Artist.ArtistId=Album.ArtistId
JOIN Track
ON Album.AlbumId=Track.AlbumId
JOIN InvoiceLine
ON Track.TrackId=InvoiceLine.TrackId
GROUP BY Artist.Name
ORDER BY revenue DESC
LIMIT 10
""")


fig = px.bar(
    artist,
    x="revenue",
    y="Name",
    orientation="h"
)


st.plotly_chart(
    fig,
    use_container_width=True
)



# ------------------
# 장르 분석
# ------------------

st.subheader("Genre Sales")


genre = load_data("""
SELECT
Genre.Name,
COUNT(*) sales
FROM Genre
JOIN Track
ON Genre.GenreId=Track.GenreId
JOIN InvoiceLine
ON Track.TrackId=InvoiceLine.TrackId
GROUP BY Genre.Name
ORDER BY sales DESC
""")


fig = px.pie(
    genre,
    names="Name",
    values="sales"
)


st.plotly_chart(
    fig,
    use_container_width=True)