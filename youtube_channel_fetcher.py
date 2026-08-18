"""
youtube_channel_fetcher.py

YouTube Data API v3를 사용해 채널의 상세 정보 + 최근 영상 통계를 가져오고,
비교/분석에 쓸 파생 지표(참여율, 평균 조회수, 업로드 주기, 숏폼 비중)를 계산하는 스크립트.

사용법:
    1) API 키를 환경변수로 설정
       export YOUTUBE_API_KEY="발급받은_키"
    2) 필요한 라이브러리 설치
       pip install requests --break-system-packages   (또는 그냥 pip install requests)
    3) 실행
       python youtube_channel_fetcher.py --handle 찹챠
       python youtube_channel_fetcher.py --channel-id UClt0Tr3Jb51xFe7TvdaTeiQ

여러 채널을 비교하고 싶으면 --handle 을 여러 번 넘기면 됩니다:
    python youtube_channel_fetcher.py --handle 찹챠 --handle 다른채널핸들
"""

import os
import sys
import argparse
import statistics
from datetime import datetime, timezone
import requests

API_BASE = "https://www.googleapis.com/youtube/v3"


def get_api_key():
    key = os.environ.get("YOUTUBE_API_KEY")
    if not key:
        sys.exit("환경변수 YOUTUBE_API_KEY 가 설정되어 있지 않습니다. export YOUTUBE_API_KEY=발급받은_키 로 설정해주세요.")
    return key


def resolve_channel(api_key, handle=None, channel_id=None):
    """핸들(@없이) 또는 채널ID로 채널 상세정보를 가져온다."""
    params = {
        "part": "snippet,statistics,contentDetails,brandingSettings,topicDetails",
        "key": api_key,
    }
    if channel_id:
        params["id"] = channel_id
    elif handle:
        params["forHandle"] = handle
    else:
        raise ValueError("handle 또는 channel_id 중 하나는 필요합니다.")

    resp = requests.get(f"{API_BASE}/channels", params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    items = data.get("items", [])
    if not items:
        raise ValueError(f"채널을 찾을 수 없습니다: handle={handle}, channel_id={channel_id}")
    return items[0]


def get_recent_video_ids(api_key, uploads_playlist_id, max_results=20):
    """업로드 재생목록에서 최근 영상 ID 목록을 가져온다."""
    params = {
        "part": "contentDetails",
        "playlistId": uploads_playlist_id,
        "maxResults": min(max_results, 50),
        "key": api_key,
    }
    resp = requests.get(f"{API_BASE}/playlistItems", params=params, timeout=15)
    resp.raise_for_status()
    items = resp.json().get("items", [])
    return [item["contentDetails"]["videoId"] for item in items]


def get_video_stats(api_key, video_ids):
    """영상 ID 리스트로 통계+길이 정보를 배치 조회한다 (최대 50개씩)."""
    if not video_ids:
        return []
    videos = []
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i + 50]
        params = {
            "part": "snippet,statistics,contentDetails",
            "id": ",".join(batch),
            "key": api_key,
        }
        resp = requests.get(f"{API_BASE}/videos", params=params, timeout=15)
        resp.raise_for_status()
        videos.extend(resp.json().get("items", []))
    return videos


def parse_iso8601_duration_to_seconds(duration):
    """PT13M8S 같은 ISO8601 duration을 초 단위로 변환."""
    import re
    match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration)
    if not match:
        return 0
    h, m, s = (int(x) if x else 0 for x in match.groups())
    return h * 3600 + m * 60 + s


def analyze_channel(api_key, handle=None, channel_id=None, video_sample=20):
    channel = resolve_channel(api_key, handle=handle, channel_id=channel_id)

    snippet = channel.get("snippet", {})
    stats = channel.get("statistics", {})
    uploads_playlist_id = channel["contentDetails"]["relatedPlaylists"]["uploads"]

    video_ids = get_recent_video_ids(api_key, uploads_playlist_id, max_results=video_sample)
    videos = get_video_stats(api_key, video_ids)

    view_counts = [int(v["statistics"].get("viewCount", 0)) for v in videos]
    like_counts = [int(v["statistics"].get("likeCount", 0)) for v in videos]
    comment_counts = [int(v["statistics"].get("commentCount", 0)) for v in videos]
    durations = [parse_iso8601_duration_to_seconds(v["contentDetails"]["duration"]) for v in videos]
    published_dates = [
        datetime.fromisoformat(v["snippet"]["publishedAt"].replace("Z", "+00:00")) for v in videos
    ]

    total_views = sum(view_counts) or 1
    engagement_rate = (sum(like_counts) + sum(comment_counts)) / total_views * 100
    avg_views = statistics.mean(view_counts) if view_counts else 0
    median_views = statistics.median(view_counts) if view_counts else 0
    shorts_ratio = (sum(1 for d in durations if d <= 60) / len(durations) * 100) if durations else 0

    upload_interval_days = None
    if len(published_dates) >= 2:
        sorted_dates = sorted(published_dates, reverse=True)
        gaps = [
            (sorted_dates[i] - sorted_dates[i + 1]).total_seconds() / 86400
            for i in range(len(sorted_dates) - 1)
        ]
        upload_interval_days = statistics.mean(gaps)

    return {
        "channel_id": channel["id"],
        "title": snippet.get("title"),
        "custom_url": snippet.get("customUrl"),
        "country": snippet.get("country"),
        "subscriber_count": int(stats.get("subscriberCount", 0)),
        "total_view_count": int(stats.get("viewCount", 0)),
        "video_count": int(stats.get("videoCount", 0)),
        "sample_size": len(videos),
        "avg_views_recent": round(avg_views, 1),
        "median_views_recent": round(median_views, 1),
        "engagement_rate_pct": round(engagement_rate, 2),
        "shorts_ratio_pct": round(shorts_ratio, 1),
        "avg_upload_interval_days": round(upload_interval_days, 1) if upload_interval_days is not None else None,
    }


def print_report(results):
    headers = [
        "채널명", "구독자", "총조회수", "영상수", "최근평균조회수",
        "참여율(%)", "숏폼비중(%)", "평균업로드주기(일)",
    ]
    rows = []
    for r in results:
        rows.append([
            r["title"], r["subscriber_count"], r["total_view_count"], r["video_count"],
            r["avg_views_recent"], r["engagement_rate_pct"], r["shorts_ratio_pct"],
            r["avg_upload_interval_days"],
        ])

    col_widths = [max(len(str(h)), *(len(str(row[i])) for row in rows)) for i, h in enumerate(headers)]
    line = " | ".join(h.ljust(w) for h, w in zip(headers, col_widths))
    print(line)
    print("-" * len(line))
    for row in rows:
        print(" | ".join(str(v).ljust(w) for v, w in zip(row, col_widths)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YouTube 채널 정보 수집 및 비교")
    parser.add_argument("--handle", action="append", default=[], help="채널 핸들(@ 제외), 여러 번 지정 가능")
    parser.add_argument("--channel-id", action="append", default=[], help="채널 ID, 여러 번 지정 가능")
    parser.add_argument("--sample", type=int, default=20, help="분석할 최근 영상 개수 (기본 20)")
    args = parser.parse_args()

    api_key = get_api_key()
    results = []

    for h in args.handle:
        results.append(analyze_channel(api_key, handle=h, video_sample=args.sample))
    for cid in args.channel_id:
        results.append(analyze_channel(api_key, channel_id=cid, video_sample=args.sample))

    if not results:
        sys.exit("--handle 또는 --channel-id 를 하나 이상 지정해주세요.")

    print_report(results)
