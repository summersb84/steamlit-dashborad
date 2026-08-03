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
    """<div style="background-color: #f8f9fa; padding: 16px 20px; border-radius: 8px; border: 1px solid #e9ecef; font-size: 13px; line-height: 1.6; color: #333333;">
        <div style="margin-bottom: 10px;">
            <span style="font-size: 15px; font-weight: bold; color: #111111;">📌 Dashboard 목적</span><br>
            본 Dashboard는 데이터 분석에서 화면 작성까지 일련의 흐름을 구성해 보고자 작성한 내용입니다.
        </div>
        <div style="margin-bottom: 10px;">
            <span style="font-size: 15px; font-weight: bold; color: #111111;">🛠️ 환경 구성</span><br>
            • 데이터 출처 : Chinook Database<br>
            • 분석 도구 : Python, Streamlit, SQLite
        </div>
        <div style="margin-bottom: 10px;">
            <span style="font-size: 15px; font-weight: bold; color: #111111;">👤 작성자 정보</span><br>
            • 이름 : 박승배<br>
            • Mail : summersb84@gmail.com
        </div>
        <div style="margin-bottom: 10px;">
            <span style="font-size: 15px; font-weight: bold; color: #111111;">📊 분석 내용</span><br>
            음원 판매 데이터를 기반으로, 매출, 고객, 상품 성과를 분석하여 주요 비즈니스 지표를 확인하고 데이터 기반 의사결정을 지원합니다.
        </div>
        <hr style="margin: 12px 0; border: 0; border-top: 1px solid #cccccc;">
        <div style="font-size: 11px; color: #6c757d;">
            Created : 2026-08-02 | Version : v0.8 | Last Updated : 2026-08-03
        </div>
    </div>""",
    unsafe_allow_html=True
)


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

# [기존 쿼리 & 테이블 출력 동일]
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
    artist_df.index = range(1, len(artist_df) + 1)

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

    # 전체 기간 인사이트
    total_artist_sales_query = f"""
        SELECT SUM(il.UnitPrice * il.Quantity) as GrandTotal
        FROM InvoiceLine il
        JOIN Invoice i ON il.InvoiceId = i.InvoiceId
        {where_clause}
    """
    grand_total_df = run_query(total_artist_sales_query, params)
    grand_total_sales = grand_total_df["GrandTotal"].iloc[0] or 1

    top_artist_name = artist_df.iloc[0]["Artist"]
    top_artist_sales = artist_df.iloc[0]["TotalRevenue"]
    top_artist_tracks = artist_df.iloc[0]["TracksSold"]
    top10_total_sales = artist_df["TotalRevenue"].sum()
    top10_share = (top10_total_sales / grand_total_sales) * 100

    st.info(f"""
    💡 **전체 기간 아티스트 판매 인사이트**
    * **최고 실적 아티스트:** **{top_artist_name}**가 **${top_artist_sales:,.2f}** ({top_artist_tracks:,}개 트랙 판매)의 매출을 올려 **1위**를 기록했습니다.
    * **Top 10 기여도:** 상위 10개 아티스트가 전체 매출의 **{top10_share:.1f}%**를 차지하고 있습니다.
    """)

    # ------------------
    # [수정] 하위 분석: 최근 3개월(월 단위) 인기 아티스트 분석
    # ------------------
    with st.expander("📌 최근 3개월(월 단위) 인기 아티스트 트렌드 및 하위 분석 보기", expanded=False):
        # 1. DB 기준 최신 날짜 및 최신 월 기준 3개월 전 시작일(월 시작일) 계산
        recent_date_query = f"""
            SELECT 
                MAX(i.InvoiceDate) as max_date,
                date(MAX(i.InvoiceDate), 'start of month', '-2 months') as start_3m_month
            FROM Invoice i
            {where_clause}
        """
        recent_date_df = run_query(recent_date_query, params)
        max_date_str = recent_date_df["max_date"].iloc[0]
        start_3m_str = recent_date_df["start_3m_month"].iloc[0]

        # 월 표시 형식 추출 (예: 2013-10 ~ 2013-12)
        start_month_fmt = start_3m_str[:7] if start_3m_str else ""
        max_month_fmt = max_date_str[:7] if max_date_str else ""

        st.markdown(f"**🗓️ 분석 대상 월:** `{start_month_fmt}` ~ `{max_month_fmt}` (월 단위 최근 3개월)")

        # 2. 월 단위 최근 3개월 조건 추가 쿼리
        recent_where = f"WHERE i.InvoiceDate >= '{start_3m_str}'"
        if selected_country != "ALL":
            recent_where += " AND i.BillingCountry = ?"

        recent_artist_query = f"""
            SELECT 
                ar.Name as Artist,
                COUNT(il.TrackId) as TracksSold,
                SUM(il.UnitPrice * il.Quantity) as TotalRevenue
            FROM InvoiceLine il
            JOIN Invoice i ON il.InvoiceId = i.InvoiceId
            JOIN Track t ON il.TrackId = t.TrackId
            JOIN Album al ON t.AlbumId = al.AlbumId
            JOIN Artist ar ON al.ArtistId = ar.ArtistId
            {recent_where}
            GROUP BY ar.ArtistId
            ORDER BY TotalRevenue DESC
            LIMIT 5
        """
        recent_artist_df = run_query(recent_artist_query, params)

        if not recent_artist_df.empty:
            recent_artist_df.index = range(1, len(recent_artist_df) + 1)
            
            sub_col1, sub_col2 = st.columns([3, 2])

            with sub_col1:
                st.caption(f"🔥 최근 3개월({start_month_fmt} ~ {max_month_fmt}) 매출 Top 5 아티스트")
                st.dataframe(
                    recent_artist_df.rename(columns={
                        "Artist": "아티스트명",
                        "TracksSold": "판매 트랙 수",
                        "TotalRevenue": "총 매출액"
                    }).style.format({
                        "총 매출액": "${:,.2f}",
                        "판매 트랙 수": "{:,} 개"
                    }),
                    use_container_width=True
                )

            with sub_col2:
                recent_top1 = recent_artist_df.iloc[0]["Artist"]
                recent_top1_sales = recent_artist_df.iloc[0]["TotalRevenue"]
                recent_top_tracks = recent_artist_df.iloc[0]["TracksSold"]
                
                is_same_top = (top_artist_name == recent_top1)
                comparison_text = "전체 기간 1위 아티스트가 최근 3개월 동안도 인기 상위를 유지하고 있습니다." if is_same_top else f"전체 기간 1위({top_artist_name})와 달리, 최근 3개월은 **{recent_top1}**가 단기 급상승 1위를 차지했습니다."

                st.caption("💡 최근 3개월 주요 포인트")
                st.success(f"""
                * **최근 3개월 1위:** **{recent_top1}** (${recent_top1_sales:,.2f})
                * **단기 트렌드:** {comparison_text}
                * **운영 제언:** 최근 3개월 급상승 아티스트 관련 프로모션 강화 추천.
                """)
        else:
            st.warning("해당 기간 내 구매 데이터가 존재하지 않습니다.")