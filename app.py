"""
app.py

youtube_channel_fetcher.py의 분석 로직을 감싼 로컬 전용 Streamlit 웹앱.
외부에 배포하지 않고 `streamlit run app.py`로 본인 컴퓨터에서만 띄워서 쓰는 용도.

사용법:
    1) pip install -r requirements.txt
    2) export YOUTUBE_API_KEY="발급받은_키"   (설정 안 하면 화면에서 직접 입력 가능)
    3) streamlit run app.py
"""

import os

import pandas as pd
import streamlit as st

from youtube_channel_fetcher import analyze_channel

st.set_page_config(page_title="유튜브 채널 분석", layout="wide")
st.title("유튜브 채널 분석")
st.caption("로컬 전용 도구입니다. 배포하지 말고 본인 컴퓨터에서만 실행하세요.")

api_key = os.environ.get("YOUTUBE_API_KEY") or st.text_input(
    "YouTube API 키", type="password", help="환경변수 YOUTUBE_API_KEY로 설정하면 이 입력창을 생략할 수 있습니다."
)

handles_input = st.text_area(
    "채널 핸들 (한 줄에 하나씩, @ 제외)", placeholder="찹챠\n다른채널핸들", height=100
)
sample = st.number_input("분석할 최근 영상 개수", min_value=1, max_value=50, value=20)

if st.button("분석 시작", type="primary"):
    if not api_key:
        st.error("API 키를 입력해주세요.")
    else:
        handles = [h.strip() for h in handles_input.splitlines() if h.strip()]
        if not handles:
            st.error("채널 핸들을 하나 이상 입력해주세요.")
        else:
            results = []
            errors = []
            with st.spinner("채널 데이터를 가져오는 중..."):
                for h in handles:
                    try:
                        results.append(analyze_channel(api_key, handle=h, video_sample=sample))
                    except Exception as e:
                        errors.append(f"{h}: {e}")

            for err in errors:
                st.warning(err)

            if results:
                df = pd.DataFrame(results).rename(
                    columns={
                        "title": "채널명",
                        "subscriber_count": "구독자",
                        "total_view_count": "총조회수",
                        "video_count": "영상수",
                        "avg_views_recent": "최근평균조회수",
                        "median_views_recent": "최근중앙값조회수",
                        "engagement_rate_pct": "참여율(%)",
                        "shorts_ratio_pct": "숏폼비중(%)",
                        "avg_upload_interval_days": "평균업로드주기(일)",
                    }
                )
                display_cols = [
                    "채널명", "구독자", "총조회수", "영상수", "최근평균조회수",
                    "최근중앙값조회수", "참여율(%)", "숏폼비중(%)", "평균업로드주기(일)",
                ]
                st.dataframe(df[display_cols], use_container_width=True, hide_index=True)
