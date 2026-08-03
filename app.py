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
    Version : v0.8<br>
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

# ------------------
# 집계 날짜 표시
# ------------------
date_range_query = f"""
    SELECT 
        MIN(date(i.InvoiceDate)) as min_date,
        MAX(date(i.InvoiceDate)) as max_date
    FROM Invoice i
    {where_clause}
"""
date_df = run_query(date_range_query, params)

min_date = date_df["min_date"].iloc[0]
max_date = date_df["max_date"].iloc[0]

# 서브헤더 및 캡션 형태로 깔끔하게 표시
if min_date and max_date:
    st.caption(f"📅 **데이터 집계 기간:** {min_date} ~ {max_date}")
else:
    st.caption("📅 **데이터 집계 기간:** 데이터 없음")

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
col1.metric("총 매출액", f"${total_revenue:,.1f}")
col2.metric("총 주문 건수", f"{total_orders:,} 건")
col3.metric("구매 고객 수", f"{total_customers:,} 명")
col4.metric("평균 주문 금액", f"${avg_order_val:,.1f}")

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

    # 10개 차트 시각화
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

    # ------------------
    # [신규] 인사이트 섹션 (st.info 또는 st.expander 활용)
    # ------------------
    if not genre_df.empty:
        # 데이터 자동 계산
        total_genre_sales = genre_df["TotalSales"].sum()
        top_1_genre = genre_df.iloc[0]["Genre"]
        top_1_sales = genre_df.iloc[0]["TotalSales"]
        top_1_share = (top_1_sales / total_genre_sales) * 100
        
        top_3_sales = genre_df.head(3)["TotalSales"].sum()
        top_3_share = (top_3_sales / total_genre_sales) * 100
        
        st.info(f"""
        💡 **장르 분석 인사이트**
        * **1위 장르:** **{top_1_genre}** 장르가 전체 매출의 **{top_1_share:.1f}%** (${top_1_sales:,.2f})를 차지하며 가장 높습니다.
        * **매출 집중도:** 상위 3개 장르가 전체 매출의 **{top_3_share:.1f}%**를 견인하고 있습니다.
        * **액션 플랜:** {top_1_genre} 중심의 메인 큐레이션 타겟팅 및 신규 트랙 확보 전략이 유효합니다.
        """)

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
    # [신규] 월별 매출 인사이트 섹션
    # ------------------
    if not trend_df.empty and len(trend_df) > 1:
        # 데이터 자동 계산
        avg_monthly_rev = trend_df["MonthlyRevenue"].mean()
        
        # 최고 매출 월 / 최저 매출 월
        max_row = trend_df.loc[trend_df["MonthlyRevenue"].idxmax()]
        min_row = trend_df.loc[trend_df["MonthlyRevenue"].idxmin()]
        
        # 최근 월 매출 및 전월 대비 변동률 (MoM)
        last_month_rev = trend_df.iloc[-1]["MonthlyRevenue"]
        prev_month_rev = trend_df.iloc[-2]["MonthlyRevenue"]
        mom_growth = ((last_month_rev - prev_month_rev) / prev_month_rev) * 100 if prev_month_rev > 0 else 0
        
        mom_icon = "🔺" if mom_growth >= 0 else "🔻"
        
        st.info(f"""
        💡 **월별 매출 분석 인사이트**
        * **최고 매출 월:** **{max_row['Month']}**에 **${max_row['MonthlyRevenue']:,.2f}**로 가장 높은 실적을 기록했습니다.
        * **평균 월 매출:** 전체 기간 동안 월평균 **${avg_monthly_rev:,.2f}**의 매출이 발생했습니다.
        * **최근 실적 흐름:** 최근 월({trend_df.iloc[-1]['Month']}) 매출은 **${last_month_rev:,.2f}**로, 전월 대비 **{mom_growth:+.1f}%** {mom_icon} 변동했습니다.
        """)
    elif len(trend_df) == 1:
        st.info("💡 **월별 매출 분석 인사이트:** 단일 월 데이터만 존재하는 상태입니다.")

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

if not artist_df.empty:
    # 1부터 시작하는 인덱스로 변경
    artist_df.index = range(1, len(artist_df) + 1)

    # 테이블 출력 (컬럼명 한글 화 및 포맷팅)
    st.dataframe(
        artist_df.rename(columns={
            "Artist": "아티스트명",
            "TracksSold": "판매 트랙 수",
            "TotalRevenue": "총 매출액"
        }).style.format({
            "총 매출액": "${:,.2f}",
            "판매 트랙 수": "{:,} 개"
        }),
        use_container_width=True
    )

    # ------------------
    # [신규] 아티스트 분석 인사이트 섹션
    # ------------------
    # 전체 매출 대비 Top 10 기여도를 계산하기 위한 전체 아티스트 총 매출 조회
    total_artist_sales_query = f"""
        SELECT SUM(il.UnitPrice * il.Quantity) as GrandTotal
        FROM InvoiceLine il
        JOIN Invoice i ON il.InvoiceId = i.InvoiceId
        {where_clause}
    """
    grand_total_df = run_query(total_artist_sales_query, params)
    grand_total_sales = grand_total_df["GrandTotal"].iloc[0] or 1

    # 지표 산출
    top_artist_name = artist_df.iloc[0]["Artist"]
    top_artist_sales = artist_df.iloc[0]["TotalRevenue"]
    top_artist_tracks = artist_df.iloc[0]["TracksSold"]
    
    top10_total_sales = artist_df["TotalRevenue"].sum()
    top10_share = (top10_total_sales / grand_total_sales) * 100
    top1_share_in_top10 = (top_artist_sales / top10_total_sales) * 100

    st.info(f"""
    💡 **아티스트 판매 인사이트**
    * **최고 실적 아티스트:** **{top_artist_name}**가 **${top_artist_sales:,.2f}** ({top_artist_tracks:,}개 트랙 판매)의 매출을 올려 **1위**를 기록했습니다.
    * **Top 10 기여도:** 상위 10개 아티스트가 전체 매출의 **{top10_share:.1f}%**를 차지하고 있습니다.
    * **집중도 분석:** 1위 아티스트({top_artist_name})는 Top 10 전체 매출 중 **{top1_share_in_top10:.1f}%**를 차지하는 대표 핵심 아티스트입니다.
    """)
else:
    st.info("해당 조건의 아티스트 데이터가 없습니다.")