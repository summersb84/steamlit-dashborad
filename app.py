import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

# ------------------
# 1. 페이지 및 DB 연결 설정
# ------------------
st.set_page_config(
    page_title="Music Store BI Dashboard",
    page_icon="🎵",
    layout="wide"
)

@st.cache_resource
def get_connection():
    return sqlite3.connect(
        "data/Chinook.db",
        check_same_thread=False
    )

conn = get_connection()


st.markdown(
    """
    <div style="
        background-color:#f8f9fa;
        padding:15px;
        border-radius:8px;
        font-size:14px;
        line-height:1.6;
    ">
    <b>Dashboard 목적</b><br>
    본 Dashboard는 데이터 분석에서 화면 작성까지 일련의 흐름을
    구성해 보고자 작성한 내용입니다.<br><br>

    <b>환경 구성</b><br>
    데이터 출처 : Chinook Databse<br>
    분석 도구 : Python, Streamlit, SQLite<br><br>

    <b>작성자 정보</b><br>
    • 이름 : 박승배<br>
    • Mail : summersb84@gmail.com<br><br>

    <b>분석 내용</b><br>
    음원 판매 데이터를 기반으로, 매출, 고객, 상품 성과를 분석하여<br>
    주요 비즈니스 지표를 확인하고 데이터 기반 의사결정을 지원합니다.<br><br>

    Created : 2026-08-02<br>
    Version : v0.7<br>
    Last Updated : 2026-08-03<br>
    </div>
    """,
    unsafe_allow_html=True
)


st.markdown("<br>", unsafe_allow_html=True)


# ------------------
# 2. 데이터 쿼리 함수 (데이터 캐싱 처리)
# ------------------
@st.cache_data
def run_query(query, _params=()):
    """SQL 쿼리를 실행하여 Pandas DataFrame으로 반환"""
    return pd.read_sql_query(query, conn, params=_params)


# ------------------
# 3. 사이드바 - 필터링 옵션
# ------------------
st.sidebar.header("🔍 검색 및 필터")

# 국가 목록 가져오기
countries_df = run_query("SELECT DISTINCT BillingCountry FROM Invoice ORDER BY BillingCountry")
country_list = ["ALL"] + countries_df["BillingCountry"].tolist()

selected_country = st.sidebar.selectbox("국가 선택", country_list)

# SQL 조건문 동적 생성
where_clause = ""
params = ()
if selected_country != "ALL":
    where_clause = "WHERE i.BillingCountry = ?"
    params = (selected_country,)


# ------------------
# 4. 메인 대시보드 헤더
# ------------------
st.title("🎵 Chinook Music Store BI Dashboard")
st.markdown("음원 판매, 고객, 장르별 성과 분석 대시보드입니다.")
st.divider()

# ------------------
# 5. 핵심 KPI 지표 (Metrics)
# ------------------
kpi_query = f"""
    SELECT 
        COUNT(DISTINCT i.InvoiceId) as total_orders,
        SUM(i.Total) as total_revenue,
        COUNT(DISTINCT i.CustomerId) as total_customers
    FROM Invoice i
    {where_clause}
"""
kpi_df = run_query(kpi_query, params)

total_revenue = kpi_df["total_revenue"].iloc[0] or 0
total_orders = kpi_df["total_orders"].iloc[0] or 0
total_customers = kpi_df["total_customers"].iloc[0] or 0
avg_order_val = (total_revenue / total_orders) if total_orders > 0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("총 매출액", f"${total_revenue:,.2f}")
col2.metric("총 주문 건수", f"{total_orders:,} 건")
col3.metric("구매 고객 수", f"{total_customers:,} 명")
col4.metric("평균 주문 금액", f"${avg_order_val:,.2f}")

st.divider()

# ------------------
# 6. 차트 시각화
# ------------------
row1_col1, row1_col2 = st.columns(2)

with row1_col1:
    st.subheader("📊 장르별 판매 비중 (매출 기준)")
    genre_query = f"""
        SELECT 
            g.Name as Genre,
            SUM(il.UnitPrice * il.Quantity) as TotalSales
        FROM InvoiceLine il
        JOIN Invoice i ON il.InvoiceId = i.InvoiceId
        JOIN Track t ON il.TrackId = t.TrackId
        JOIN Genre g ON t.GenreId = g.GenreId
        {where_clause}
        GROUP BY g.Name
        ORDER BY TotalSales DESC
        LIMIT 10
    """
    genre_df = run_query(genre_query, params)
    
    fig_genre = px.bar(
        genre_df,
        x="TotalSales",
        y="Genre",
        orientation="h",
        title="Top 10 장르 매출",
        labels={"TotalSales": "매출 ($)", "Genre": "장르"},
        color="TotalSales",
        color_continuous_scale="Viridis"
    )
    fig_genre.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
    st.plotly_chart(fig_genre, use_container_width=True)

with row1_col2:
    st.subheader("📈 월별 매출 추이")
    trend_query = f"""
        SELECT 
            strftime('%Y-%m', i.InvoiceDate) as Month,
            SUM(i.Total) as MonthlyRevenue
        FROM Invoice i
        {where_clause}
        GROUP BY Month
        ORDER BY Month
    """
    trend_df = run_query(trend_query, params)
    
    fig_trend = px.line(
        trend_df,
        x="Month",
        y="MonthlyRevenue",
        title="월별 매출 흐름",
        labels={"MonthlyRevenue": "매출 ($)", "Month": "년-월"},
        markers=True
    )
    st.plotly_chart(fig_trend, use_container_width=True)

# ------------------
# 7. 상위 아티스트 / 상세 데이터 테이블
# ------------------
st.divider()
st.subheader("🏆 Top 10 인기 아티스트")

artist_query = f"""
    SELECT 
        ar.Name as Artist,
        COUNT(il.TrackId) as TracksSold,
        SUM(il.UnitPrice * il.Quantity) as TotalRevenue
    FROM InvoiceLine il
    JOIN Invoice i ON il.InvoiceId = i.InvoiceId
    JOIN Track t ON il.TrackId = t.TrackId
    JOIN Album al ON t.AlbumId = al.AlbumId
    JOIN Artist ar ON al.ArtistId = ar.ArtistId
    {where_clause}
    GROUP BY ar.ArtistId
    ORDER BY TotalRevenue DESC
    LIMIT 10
"""
artist_df = run_query(artist_query, params)

st.dataframe(
    artist_df.style.format({"TotalRevenue": "${:,.2f}", "TracksSold": "{:,}"}),
    use_container_width=True
)