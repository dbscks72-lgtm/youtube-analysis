"""
app.py

유튜브 채널 워치리스트 대시보드. 로컬 실행(run.bat)뿐 아니라
Streamlit Community Cloud에 비공개(초대된 사람만 접속)로 배포하는 것도 지원한다.

- 왼쪽 사이드바: 등록한 채널 목록(로고 + 이름), 맨 아래에 설정 탭
- 홈: 인기 급상승(국내, 게임 카테고리) Top 10
- 채널 선택 시: 채널 요약 지표 + 최근 영상 5개
- 설정 탭: API 키 입력, 채널 등록/삭제 (channels.json에 저장)

사용법 (로컬):
    1) pip install -r requirements.txt
    2) export YOUTUBE_API_KEY="발급받은_키"   (또는 설정 탭에서 직접 입력)
    3) run.bat 실행 (또는 streamlit run app.py)

사용법 (Streamlit Community Cloud에 배포할 때):
    - 앱의 Secrets에 YOUTUBE_API_KEY = "발급받은_키" 를 등록해두면,
      초대된 사람은 키를 몰라도 되고 설정 탭에는 키 입력창 대신
      "관리자가 설정한 키 사용 중" 안내만 보인다.
    - Secrets에 ACCESS_CODE = "원하는_코드" 를 추가로 등록해두면,
      이 코드를 아는 사람만 화면 전체(사이드바 포함)를 볼 수 있게 되는
      접속 게이트가 앞단에 생긴다. 설정하지 않으면 게이트 없이 바로 들어간다.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

from youtube_channel_fetcher import analyze_channel, get_trending_videos, resolve_channel

WATCHLIST_PATH = Path(__file__).parent / "channels.json"

st.set_page_config(page_title="유튜브 채널 분석", layout="wide")


def _load_managed_api_key():
    """운영자가 미리 설정해둔 API 키를 찾는다 (환경변수 우선, 그다음 Streamlit Secrets)."""
    env_key = os.environ.get("YOUTUBE_API_KEY")
    if env_key:
        return env_key
    try:
        return st.secrets.get("YOUTUBE_API_KEY", "")
    except Exception:
        # secrets.toml이 아예 없는 로컬 환경 등에서는 조용히 무시한다.
        return ""


# 이 값이 있으면(=운영자가 미리 등록) 설정 탭에서 편집 가능한 키 입력창을 숨긴다.
# 초대된 뷰어가 "Show password" 버튼 등으로 실제 키 값을 볼 수 없게 하기 위함.
MANAGED_API_KEY = _load_managed_api_key()


def _load_access_code():
    """운영자가 접속 코드를 설정해뒀는지 확인한다 (환경변수 우선, 그다음 Streamlit Secrets)."""
    code = os.environ.get("ACCESS_CODE")
    if code:
        return code
    try:
        return st.secrets.get("ACCESS_CODE", "")
    except Exception:
        return ""


# 이 값이 있으면(=운영자가 접속 코드를 설정) 코드를 입력해야만 앱을 볼 수 있다.
# 로컬 개인 사용처럼 코드를 설정하지 않은 경우엔 게이트 없이 바로 들어간다.
ACCESS_CODE = _load_access_code()


# ---------- 워치리스트 저장/불러오기 (로컬 JSON) ----------

def load_watchlist():
    if WATCHLIST_PATH.exists():
        try:
            return json.loads(WATCHLIST_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
    return []


def save_watchlist(channels):
    WATCHLIST_PATH.write_text(json.dumps(channels, ensure_ascii=False, indent=2), encoding="utf-8")


if "watchlist" not in st.session_state:
    st.session_state.watchlist = load_watchlist()
if "nav" not in st.session_state:
    st.session_state.nav = "home"
if "api_key" not in st.session_state:
    st.session_state.api_key = MANAGED_API_KEY
if "authenticated" not in st.session_state:
    # 접속 코드가 설정되어 있지 않으면(로컬 개인 사용 등) 게이트 없이 통과시킨다.
    st.session_state.authenticated = not ACCESS_CODE


def get_api_key():
    return st.session_state.api_key


# ---------- 접속 코드 게이트 ----------

def render_access_gate():
    st.markdown("<div style='height:12vh;'></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<h1 style='text-align:center;'>📺 유튜브 채널 분석</h1>", unsafe_allow_html=True)
        st.markdown(
            "<p style='text-align:center; color: gray;'>접속 코드를 입력해주세요</p>",
            unsafe_allow_html=True,
        )
        with st.form("access_gate_form"):
            code_input = st.text_input(
                "접속 코드", type="password", label_visibility="collapsed", placeholder="코드 입력"
            )
            submitted = st.form_submit_button("입장하기", use_container_width=True, type="primary")
        if submitted:
            if code_input == ACCESS_CODE:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("코드가 올바르지 않습니다.")


if not st.session_state.authenticated:
    render_access_gate()
    st.stop()


# ---------- 사이드바: 채널 목차 + 맨 아래 설정 ----------

st.markdown(
    """
    <style>
    [data-testid="stSidebarUserContent"],
    [data-testid="stSidebarUserContent"] > div {
        height: 100%;
    }
    [data-testid="stSidebarUserContent"] [data-testid="stVerticalBlock"] {
        height: 100%;
        display: flex;
        flex-direction: column;
    }
    [data-testid="stElementContainer"]:has(.nav-spacer) {
        flex: 1 1 auto;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("## 📺 유튜브 분석")

    if st.button(
        "🏠 홈 (트렌드)",
        use_container_width=True,
        type="primary" if st.session_state.nav == "home" else "secondary",
    ):
        st.session_state.nav = "home"

    st.markdown("#### 등록된 채널")
    if not st.session_state.watchlist:
        st.caption("설정 탭에서 채널을 추가해주세요.")
    for ch in st.session_state.watchlist:
        col_logo, col_name = st.columns([1, 4])
        with col_logo:
            if ch.get("thumbnail_url"):
                st.image(ch["thumbnail_url"], width=32)
        with col_name:
            is_active = st.session_state.nav == ch["channel_id"]
            if st.button(
                ch.get("title") or ch["channel_id"],
                key=f"nav_{ch['channel_id']}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                st.session_state.nav = ch["channel_id"]

    st.markdown('<div class="nav-spacer"></div>', unsafe_allow_html=True)
    st.divider()
    if st.button(
        "⚙️ 설정",
        use_container_width=True,
        type="primary" if st.session_state.nav == "settings" else "secondary",
    ):
        st.session_state.nav = "settings"


# ---------- 화면별 렌더링 ----------

def render_home():
    st.title("🔥 인기 급상승 · 게임 (국내 Top 10)")
    api_key = get_api_key()
    if not api_key:
        st.info("먼저 왼쪽 아래 **설정**에서 YouTube API 키를 입력해주세요.")
        return

    try:
        with st.spinner("인기 급상승 영상을 가져오는 중..."):
            trending = get_trending_videos(api_key, region_code="KR", category_id="20", max_results=10)
    except Exception as e:
        st.error(f"트렌드 영상을 가져오지 못했습니다: {e}")
        return

    if not trending:
        st.warning("표시할 트렌드 영상이 없습니다.")
        return

    for i in range(0, len(trending), 5):
        row = trending[i:i + 5]
        cols = st.columns(len(row))
        for col, video in zip(cols, row):
            with col:
                if video["thumbnail_url"]:
                    st.image(video["thumbnail_url"], use_container_width=True)
                st.markdown(f"**[{video['title']}]({video['url']})**")
                st.caption(f"{video['channel_title']} · 조회수 {video['view_count']:,}")


def render_settings():
    st.title("⚙️ 설정")

    st.subheader("YouTube API 키")
    if MANAGED_API_KEY:
        st.success("✅ 관리자가 설정해둔 API 키를 사용 중입니다. (이 화면에는 키 값이 노출되지 않습니다)")
    else:
        new_key = st.text_input(
            "API 키",
            value=st.session_state.api_key,
            type="password",
            help="환경변수 YOUTUBE_API_KEY로 설정해두면 매번 입력하지 않아도 됩니다.",
        )
        if new_key != st.session_state.api_key:
            st.session_state.api_key = new_key

    st.divider()
    st.subheader("채널 등록")
    with st.form("add_channel_form", clear_on_submit=True):
        handle = st.text_input("채널 핸들 (@ 제외)", placeholder="찹챠")
        submitted = st.form_submit_button("채널 추가")

    if submitted and handle.strip():
        api_key = get_api_key()
        if not api_key:
            st.error("먼저 API 키를 입력해주세요.")
        else:
            try:
                channel = resolve_channel(api_key, handle=handle.strip())
            except Exception as e:
                st.error(f"채널을 찾지 못했습니다: {e}")
            else:
                cid = channel["id"]
                if any(c["channel_id"] == cid for c in st.session_state.watchlist):
                    st.warning("이미 등록된 채널입니다.")
                else:
                    snippet = channel.get("snippet", {})
                    st.session_state.watchlist.append({
                        "channel_id": cid,
                        "handle": handle.strip(),
                        "title": snippet.get("title"),
                        "thumbnail_url": (snippet.get("thumbnails", {}).get("default") or {}).get("url"),
                        "added_at": datetime.now(timezone.utc).isoformat(),
                    })
                    save_watchlist(st.session_state.watchlist)
                    st.success(f"'{snippet.get('title')}' 채널을 등록했습니다.")
                    st.rerun()

    st.divider()
    st.subheader("등록된 채널 관리")
    if not st.session_state.watchlist:
        st.caption("등록된 채널이 없습니다.")
    for ch in list(st.session_state.watchlist):
        col_logo, col_name, col_remove = st.columns([1, 4, 1])
        with col_logo:
            if ch.get("thumbnail_url"):
                st.image(ch["thumbnail_url"], width=32)
        with col_name:
            st.write(ch.get("title") or ch["channel_id"])
        with col_remove:
            if st.button("삭제", key=f"remove_{ch['channel_id']}"):
                st.session_state.watchlist = [
                    c for c in st.session_state.watchlist if c["channel_id"] != ch["channel_id"]
                ]
                save_watchlist(st.session_state.watchlist)
                if st.session_state.nav == ch["channel_id"]:
                    st.session_state.nav = "home"
                st.rerun()


def render_channel(channel_id):
    api_key = get_api_key()
    if not api_key:
        st.info("먼저 왼쪽 아래 **설정**에서 YouTube API 키를 입력해주세요.")
        return

    try:
        with st.spinner("채널 데이터를 가져오는 중..."):
            result = analyze_channel(api_key, channel_id=channel_id, video_sample=20)
    except Exception as e:
        st.error(f"채널 데이터를 가져오지 못했습니다: {e}")
        return

    col_logo, col_title = st.columns([1, 8])
    with col_logo:
        if result.get("thumbnail_url"):
            st.image(result["thumbnail_url"], width=64)
    with col_title:
        st.title(result["title"] or channel_id)
        if result.get("custom_url"):
            st.caption(result["custom_url"])

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("구독자", f"{result['subscriber_count']:,}")
    m2.metric("총 조회수", f"{result['total_view_count']:,}")
    m3.metric("참여율", f"{result['engagement_rate_pct']}%")
    m4.metric("숏폼 비중", f"{result['shorts_ratio_pct']}%")

    with st.expander("상세 지표 보기"):
        st.write(f"- 분석 대상 영상 수: {result['sample_size']}개")
        st.write(f"- 최근 평균 조회수: {result['avg_views_recent']:,}")
        st.write(f"- 최근 중앙값 조회수: {result['median_views_recent']:,}")
        st.write(f"- 평균 업로드 주기: {result['avg_upload_interval_days']}일" if result["avg_upload_interval_days"] is not None else "- 평균 업로드 주기: 계산 불가")

    st.divider()
    st.subheader("최근 영상")
    recent = result.get("recent_videos", [])
    if not recent:
        st.caption("최근 영상이 없습니다.")
    else:
        cols = st.columns(len(recent))
        for col, video in zip(cols, recent):
            with col:
                if video["thumbnail_url"]:
                    st.image(video["thumbnail_url"], use_container_width=True)
                st.markdown(f"**[{video['title']}]({video['url']})**")
                st.caption(f"조회수 {video['view_count']:,}")


nav = st.session_state.nav
if nav == "home":
    render_home()
elif nav == "settings":
    render_settings()
else:
    render_channel(nav)
