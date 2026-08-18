# 채널별 상세 정보 수집 API — 필요 데이터 명세 (YouTube Data API v3 기준)

Claude 프로젝트가 "성과 분석 / 경쟁 벤치마킹 / 콘텐츠 기획"을 하려면, 이 API가 채널당 최소 아래 데이터를 구조화해서 반환해야 합니다. 공식 YouTube Data API v3를 기준으로 정리했습니다.

---

## 1. 채널 레벨 정보 (`channels.list`)

API 키만으로 조회 가능 (OAuth 불필요). `part` 파라미터별로 필요한 필드:

| part | 가져올 필드 | 용도 |
|---|---|---|
| `snippet` | 채널명, 설명, 커스텀 URL(@handle), 개설일, 국가, 기본 언어, 썸네일(프로필 이미지) | 기본 프로필, 채널 정체성 파악 |
| `statistics` | 구독자 수(반올림됨), 총 누적 조회수, 공개 영상 수 | 채널 규모 비교의 기준값 |
| `contentDetails` | **uploads 재생목록 ID** (이 채널이 올린 모든 영상 목록을 가져오는 키) | 영상 목록 수집의 진입점 |
| `brandingSettings` | 채널 키워드(SEO), 배너 이미지, 예고편(트레일러) 영상 ID | 채널 포지셔닝/SEO 분석 |
| `topicDetails` | 채널 주제 카테고리(위키피디아 기반 태그) | 카테고리 자동 분류, 경쟁군 그룹핑 |
| `status` | 공개 여부, 아동용(Made for Kids) 여부 | 데이터 필터링 |

> **참고**: 채널 조회 시 `id`, `forHandle`(@핸들), `forUsername`(레거시) 중 하나로 조회 가능 → 사용자가 URL만 줘도 핸들만 파싱해서 조회 가능.

## 2. 영상 레벨 정보 (`videos.list`)

`contentDetails.relatedPlaylists.uploads`로 얻은 재생목록을 `playlistItems.list`로 순회 → 영상 ID 리스트 확보 → `videos.list`로 상세 조회.

| part | 가져올 필드 | 용도 |
|---|---|---|
| `snippet` | 제목, 설명, 태그, 카테고리ID, 게시일, 썸네일, 언어 | 제목/썸네일 패턴 분석, SEO 분석 |
| `statistics` | 조회수, 좋아요 수, 댓글 수 (⚠️ 싫어요 수는 2021년부터 비공개) | 참여율 계산 |
| `contentDetails` | 영상 길이(duration), 화질, 자막 유무, 라이선스, 프로젝션(360도 여부) | 숏폼/롱폼 구분, 포맷 분석 |
| `status` | 공개 상태, 라이선스 타입, 임베드 허용 여부 | 필터링 |
| `liveStreamingDetails` | 실제 방송 시작/종료 시각, 동시 시청자 수(방송 중일 때) | 라이브 콘텐츠 분석 시 |
| `topicDetails` | 영상 주제 태그 | 콘텐츠 분류 |

## 3. 댓글 데이터 (`commentThreads.list`) — 선택적

| 필드 | 용도 |
|---|---|
| 댓글 본문, 작성일, 좋아요 수, 답글 수 | 반응/여론 분석, 자주 나오는 키워드 추출 |

- 채널 소유자가 댓글을 막았거나 비공개 처리한 영상은 조회 불가.
- 대량 수집 시 텍스트 마이닝(빈도 분석, 감성 분석)은 별도 후처리 필요.

## 4. API로는 못 가져오는 것 (반드시 인지해야 할 제약)

이 부분이 실제로 가장 중요합니다. **타 채널의 다음 데이터는 YouTube Data API v3로 절대 조회 불가**하며, 오직 **채널 소유자 본인이 OAuth 인증한 YouTube Analytics API**를 통해서만 자기 채널 데이터를 볼 수 있습니다.

- 평균 시청 지속시간(Average View Duration), 시청 지속률(Retention 그래프)
- 트래픽 소스(검색/추천/외부 유입 비율)
- 시청자 인구통계(연령, 성별, 지역)
- 클릭률(CTR), 노출수(Impressions)
- 정확한 실시간 구독자 증감 추이

→ 경쟁 채널 분석에서는 이 지표들을 **직접 볼 수 없다는 전제**로 설계해야 하고, 대신 조회수/좋아요/댓글수/업로드 주기 같은 "공개 지표"로 대리 추정(proxy)하는 방식을 써야 합니다. Claude 프로젝트 지침에도 이 한계를 안내 문구로 넣어두는 게 좋습니다.

## 5. 직접 계산해야 하는 파생 지표

API가 원시값만 주므로, 아래는 수집 후 서버에서 계산해서 반환하는 게 좋습니다.

- **참여율(Engagement Rate)** = (좋아요+댓글) / 조회수
- **업로드 주기** = 최근 N개 영상 게시일 간격 평균
- **평균 조회수 / 중앙값 조회수** (최근 10~20개 영상 기준)
- **채널 성장률** — API는 시계열을 주지 않으므로, **매일/매주 스냅샷을 직접 DB에 저장**해서 자체적으로 시계열을 쌓아야 함 (예: 구독자 수, 조회수를 크론잡으로 매일 기록)
- **숏폼 비중** = duration ≤ 60초 영상 수 / 전체 영상 수

## 6. 경쟁 채널 탐색이 필요할 때 (`search.list`)

- 키워드나 카테고리로 새 채널을 찾을 때만 사용. **쿼터 비용이 1회 100 units로 매우 비쌈** (기본 일일 쿼터가 10,000 units이므로 100회만 호출해도 소진).
- 가능하면 사용자가 비교할 채널 URL을 직접 입력하게 하고, `search.list`는 "이 카테고리의 새 채널 발굴" 같은 제한적 용도로만 아껴서 사용.

## 7. 데이터 모델 제안 (테이블 스키마 개요)

```
channels
  channel_id (PK), handle, title, description, country, created_at,
  subscriber_count, total_view_count, video_count, uploads_playlist_id,
  category_tags[], keywords[], last_synced_at

videos
  video_id (PK), channel_id (FK), title, description, tags[], category_id,
  published_at, duration_sec, view_count, like_count, comment_count,
  is_short (bool), thumbnail_url, last_synced_at

channel_snapshots   -- 시계열 (크론으로 매일 적재)
  channel_id (FK), snapshot_date, subscriber_count, total_view_count, video_count

comments (선택)
  comment_id (PK), video_id (FK), text, like_count, published_at
```

## 8. 쿼터 관리 팁

- 일일 기본 쿼터 10,000 units. `channels.list`, `videos.list`, `playlistItems.list`, `commentThreads.list`는 호출당 약 1 unit(최대 50개씩 배치 조회 가능) — 저렴함.
- `search.list`만 100 units로 압도적으로 비싸므로 최소화.
- 같은 채널을 반복 조회하지 않도록 **캐싱 + TTL**(예: 채널 정보는 6~12시간 캐시) 설계 권장.
- 쿼터 부족 시 Google Cloud Console에서 증량 신청 가능(사용 사례 심사 필요).

---

### 참고 자료 (Sources)
- [Channels — YouTube Data API](https://developers.google.com/youtube/v3/docs/channels)
- [Implementation: Channels — YouTube Data API](https://developers.google.com/youtube/v3/guides/implementation/channels)
- [YouTube Data API Overview / Quota](https://developers.google.com/youtube/v3/getting-started)
- [YouTube API Quota Limits 2026 — getphyllo](https://www.getphyllo.com/post/youtube-api-limits-how-to-calculate-api-usage-cost-and-fix-exceeded-api-quota)
