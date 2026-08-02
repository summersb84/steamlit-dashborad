import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

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
    
    </div>
    """,
    unsafe_allow_html=True
)


st.markdown("<br>", unsafe_allow_html=True)


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
COUNT(DISTINCT CustomerId) customers,
SUM(Total) / COUNT(*) aov,
SUM(Total) / COUNT(DISTINCT CustomerId) ARPU,
MIN(InvoiceDate) start_date,
MAX(InvoiceDate) end_date
FROM Invoice
""")

start = pd.to_datetime(kpi.start_date[0]).strftime("%Y-%m-%d")
end = pd.to_datetime(kpi.end_date[0]).strftime("%Y-%m-%d")

st.write("")
st.write("")


st.markdown(
    f"""
    <div style='font-size:14px; color:gray;'>
    📅 판매 기간 : {start} ~ {end}
    </div>
    """,
    unsafe_allow_html=True
)


st.write("")


col1,col2,col3,col4,col5 = st.columns(5)


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

col4.metric(
    "건단가",
    f"${kpi.aov[0]:,.1f}"
)

col5.metric(
    "ARPU",
    f"${kpi.ARPU[0]:,.1f}"
)
        

st.divider()

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
    markers=True,
    title = "Monthly Revenue Treand"
)

fig.update_layout(
    yaxis=dict(
        rangemode="tozero",
        tickformat="$,.0f"
    )
)


st.plotly_chart(
    fig,
    use_container_width=True
)


#전월 대비 계산
monthly["prev_revenue"] = monthly["revenue"].shift(1)

monthly["mom"] = (
    (monthly["revenue"] - monthly["prev_revenue"])
    / monthly["prev_revenue"] * 100
).round(1)

# KPI 계산
last = monthly.iloc[-1]
prev = monthly.iloc[-2]

change = (
    (last["revenue"] - prev["revenue"])
    / prev["revenue"] * 100
)

best = monthly.loc[monthly["revenue"].idxmax()]
worst = monthly.loc[monthly["revenue"].idxmin()]


recent_4m = monthly.tail(4)


insight_text = ""

for _, row in recent_4m.iterrows():

    if pd.isna(row["mom"]):
        insight_text += (
            f"- {row['month']} : "
            f"${row['revenue']:,.0f}\n"
        )
    else:
        icon = "▲" if row["mom"] >= 0 else "▼"

        insight_text += (
            f"- {row['month']} : "
            f"${row['revenue']:,.0f} "
            f"({icon} {abs(row['mom']):.1f}%)\n"
        )


st.info(
f"""
📊 **최근 4개월 매출 현황**

{insight_text}
"""
)


st.divider()


# ------------------
# 구매자 지표
# ------------------

st.subheader("Customer Overview")


customer_monthly = load_data("""
WITH first_purchase AS (
    SELECT
        CustomerId,
        MIN(date(InvoiceDate)) AS first_date
    FROM Invoice
    GROUP BY CustomerId
)

SELECT
    i.month,
    i.active_customers,
    n.new_customers,
    i.revenue,
    ROUND(i.revenue / i.active_customers, 2) AS arpu

FROM
(
    SELECT
        strftime('%Y-%m', InvoiceDate) AS month,
        COUNT(DISTINCT CustomerId) AS active_customers,
        SUM(Total) AS revenue
    FROM Invoice
    GROUP BY month
) i

LEFT JOIN
(
    SELECT
        strftime('%Y-%m', first_date) AS month,
        COUNT(CustomerId) AS new_customers
    FROM first_purchase
    GROUP BY month
) n

ON i.month = n.month

ORDER BY i.month
""")


# ------------------
# 구매자 KPI
# ------------------

last_customer = customer_monthly.iloc[-1]


col1, col2, col3 = st.columns(3)


with col1:
    st.metric(
        "Active Customers",
        f"{last_customer['active_customers']:,}"
    )


with col2:
    st.metric(
        "New Customers",
        f"{last_customer['new_customers']:,}"
    )


with col3:
    st.metric(
        "ARPU",
        f"${last_customer['arpu']:,.2f}"
    )


# ------------------
# 사용자 추이
# ------------------

fig_customer = px.line(
    customer_monthly,
    x="month",
    y="active_customers",
    markers=True,
    title="Monthly Active Customers"
)


fig_customer.update_layout(
    yaxis=dict(
        rangemode="tozero"
    )
)


st.plotly_chart(
    fig_customer,
    use_container_width=True
)


# ------------------
# 고객 Insight
# ------------------

recent_customer = customer_monthly.tail(4)


customer_text = ""

for _, row in recent_customer.iterrows():

    customer_text += (
        f"- {row['month']} : "
        f"Active {row['active_customers']:,}명 / "
        f"New {row['new_customers']:,}명 / "
        f"ARPU ${row['arpu']:,.2f}<br>"
    )


st.info(
f"""
📊 **최근 4개월 고객 현황**

{customer_text}
"""
)


st.divider()




# ------------------
# 인기 Artist
# ------------------

st.subheader("Top 10 Artist")


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

fig.update_yaxes(
    autorange="reversed"
)


st.plotly_chart(
    fig,
    use_container_width=True
)

st.divider()

# ------------------
# 장르 분석
# ------------------


col1, divider, col2 = st.columns([5, 0.1, 5])

# 왼쪽 : 전체 장르 점유율
with col1:

    st.subheader("장르별 판매건수")


    genre = load_data("""
    SELECT
        Genre.Name,
        COUNT(*) sales
    FROM Genre
    JOIN Track
        ON Genre.GenreId = Track.GenreId
    JOIN InvoiceLine
        ON Track.TrackId = InvoiceLine.TrackId
    GROUP BY Genre.Name
    ORDER BY sales DESC
    """)


    fig = px.pie(
        genre,
        names="Name",
        values="sales"
    )
    
    fig.update_traces(
    texttemplate="%{label}<br>%{percent}",
    textposition="inside"
    )


    st.plotly_chart(
        fig,
        use_container_width=True
    )


with divider:
    st.markdown(
        """
        <div style="
            border-left:1px solid #ddd;
            height:500px;
        ">
        </div>
        """,
        unsafe_allow_html=True
    )

# 오른쪽 : 지역별 장르 분석
with col2:

    st.subheader("지역별 장르별 판매건수")


    region_genre = load_data("""
    SELECT
        c.Country,
        g.Name AS Genre,
        SUM(il.Quantity) AS sales
    FROM Customer c
    JOIN Invoice i
        ON c.CustomerId = i.CustomerId
    JOIN InvoiceLine il
        ON i.InvoiceId = il.InvoiceId
    JOIN Track t
        ON il.TrackId = t.TrackId
    JOIN Genre g
        ON t.GenreId = g.GenreId
    GROUP BY
        c.Country,
        g.Name
    """)


    country = st.selectbox(
        "지역 선택",
        region_genre["Country"].unique()
    )


    filtered = region_genre[
        region_genre["Country"] == country
    ]


    filtered = (
        filtered
        .sort_values(
            "sales",
            ascending=False
        )
        .head(5)
    )


    fig = px.bar(
        filtered,
        x="sales",
        y="Genre",
        orientation="h"
    )


    fig.update_yaxes(
        autorange="reversed"
    )


    st.plotly_chart(
        fig,
        use_container_width=True
    )