# 유튜브 분석 프로젝트

Claude(Cowork)와 함께 설계한 유튜브 채널 분석 프로젝트입니다. 이 폴더에서 `claude` 를 실행해서 개발을 이어가면 됩니다.

## 폴더 구성

- `youtube_analysis_project_instructions.md` — Claude 프로젝트(대화형 분석)에 넣을 커스텀 지침
- `youtube_channel_api_spec.md` — 채널/영상 데이터 API 명세 (필요 필드, 쿼터 비용, 데이터 모델)
- `vling_style_internal_tool_design.md` — 채널 비교 분석 + 모니터링/알림 기능 설계안 (아키텍처, 로드맵)
- `youtube_channel_fetcher.py` — 실제로 채널 정보/영상 통계를 가져오는 검증된 프로토타입 스크립트
- `app.py` — `youtube_channel_fetcher.py`를 감싼 Streamlit 웹앱 (로컬 실행 + 비공개 클라우드 배포 둘 다 지원)
- `run.bat` — 더블클릭으로 로컬에서 웹앱을 실행하는 launcher (venv 활성화 + 127.0.0.1 바인딩까지 자동 처리)
- `requirements.txt` — 의존성 목록
- `tests/` — 순수 함수(네트워크 호출 없음) 단위 테스트
- `channels.json` — 웹앱에서 등록한 채널 워치리스트 (첫 채널 등록 시 자동 생성, git에는 커밋 안 됨)
- `channel_snapshots.json` — 채널별 일별 스냅샷 (성장 추이 그래프용, 자동 생성, git에는 커밋 안 됨)
- `access_log.json` — 접속 코드 시도 기록 (자동 생성, git에는 커밋 안 됨)
- `.streamlit/secrets.toml.example` — 클라우드 배포용 Secrets 예시 (실제 키는 여기 적지 않음)

## 웹앱 (`app.py`) 화면 구성

- **왼쪽 사이드바**: 등록한 채널 목록(로고 + 채널명), 맨 아래에 ⚙️ 설정 탭
- **홈 (첫 화면)**: 인기 급상승 · 게임 카테고리(국내) Top 10
- **📊 전체 비교**: 등록된 모든 채널을 표 하나에 모아서 구독자/조회수/참여율/숏폼비중/업로드주기를 한눈에 비교
- **채널 선택 시**: 구독자/총조회수/참여율/숏폼비중 요약 지표 + 성장 추이 그래프(스냅샷이 2일치 이상 쌓이면 표시) + 최근 영상 5개
- **설정 탭**: API 키 입력, 채널 핸들로 등록/삭제 (`channels.json`에 저장되어 다음 실행 때도 유지됨), 게이트가 설정되어 있으면 접속 시도 기록도 확인 가능
  - API 키를 환경변수나 Streamlit Secrets로 미리 등록해두면(아래 "비공개로 다른 사람에게 공유하기" 참고), 이 탭에는 키 입력창 대신 "관리자가 설정해둔 키 사용 중" 안내만 뜨고, 초대된 사람은 실제 키 값을 볼 수 없습니다.
- **접속 코드 게이트**: Secrets에 `ACCESS_CODE`(공용 코드 1개) 또는 `[users]`(사람마다 다른 코드)를 등록해두면, 코드를 아는 사람만 화면(사이드바 포함) 전체를 볼 수 있습니다. 브라우저를 새로고침하거나 새 탭에서 열면 코드를 다시 입력해야 합니다 (세션에만 저장, 영구 로그인 아님). 5번 연속 틀리면 60초간 잠기고, 성공/실패 시도는 설정 탭에서 확인할 수 있습니다.
- **사람별 워치리스트**: `[users]`로 사람마다 다른 코드를 부여한 경우, 코드로 "누가 들어왔는지"를 식별해서 각자 별도의 채널 워치리스트를 갖습니다 (사이드바에 "OOO님으로 접속 중"이라고 표시됨). `ACCESS_CODE` 하나만 쓰는 경우엔 예전처럼 모두가 같은 워치리스트를 공유합니다.
- **API 캐싱**: 같은 채널/트렌드 데이터는 15분간 캐시되어, 반복 조회해도 YouTube API 쿼터를 다시 쓰지 않습니다.

## 로컬에서 실행하기

가장 쉬운 방법: 바탕화면의 **"유튜브 채널 분석"** 바로가기(또는 프로젝트 폴더의 `run.bat`)를 더블클릭하면 venv 활성화 → 서버 실행 → 브라우저 자동 오픈까지 한 번에 됩니다.

수동으로 하려면:
1. `pip install -r requirements.txt` 로 의존성 설치
2. `YOUTUBE_API_KEY` 환경변수 설정 (또는 웹 UI의 설정 탭에서 직접 입력)
3. `python youtube_channel_fetcher.py --handle 찹챠` 실행해서 정상 동작 확인
   - 테스트만 돌려보려면: `python -m unittest discover -s tests`
   - 웹 UI로 써보려면: `streamlit run app.py --server.address 127.0.0.1` (다른 기기에서 접근 못 하게 루프백에만 바인딩)

## 비공개로 다른 사람에게 공유하기 (Streamlit Community Cloud)

허용한 사람만 접속하게 하려면, 이 저장소를 Streamlit Community Cloud에 올리고 **접속 코드**로 막는 방식을 씁니다. YouTube API는 초과해도 자동 과금되지 않고 그날 요청이 막히기만 하니(무료 쿼터, 하루 10,000 units), 소수 인원이면 안전합니다.

1. [share.streamlit.io](https://share.streamlit.io) 에서 본인 GitHub 계정으로 로그인
2. "New app" → 이 저장소(`dbscks72-lgtm/youtube-analysis`) 선택, main file은 `app.py`
3. 배포 전/후 **Settings → Secrets**에 아래 내용 추가 (`.streamlit/secrets.toml.example` 참고) — **두 방식 중 하나를 고르세요**:

   **A. 모두 같은 코드 1개, 워치리스트도 공용**
   ```
   YOUTUBE_API_KEY = "본인의_실제_API_키"
   ACCESS_CODE = "초대할 사람에게 알려줄 코드"
   ```

   **B. 사람마다 다른 코드, 각자 자기 워치리스트 (추천)**
   ```
   YOUTUBE_API_KEY = "본인의_실제_API_키"

   [users]
   철수 = "철수전용코드"
   영희 = "영희전용코드"
   ```
   `[users]`를 설정하면 `ACCESS_CODE`는 무시되고 이 방식이 우선 적용됩니다. 사람을 추가/삭제하려면 이 Secrets 화면에서 줄을 추가/삭제하고 저장하면 됩니다 (앱이 자동 재시작됨).

4. 배포되면 링크(`https://xxxx.streamlit.app`)를 공유하고 싶은 사람에게 URL과 **그 사람 전용 코드**(또는 공용 코드)를 전달
5. 접속하면 코드 입력 화면이 먼저 뜨고, 맞는 코드를 입력해야만 안쪽 화면(사이드바 포함)이 보입니다. API 키 값 자체는 화면 어디에도 노출되지 않습니다. `[users]` 방식이면 사이드바에 "OOO님으로 접속 중"이 표시되고, 그 사람만의 채널 목록이 보입니다.

> **접속 코드 게이트의 특징**: 브라우저를 새로고침하거나 새 탭/새 기기에서 열면 코드를 다시 입력해야 합니다 (로그인 쿠키 같은 영구 저장이 아니라 그 세션에서만 유지됨). `[users]` 방식이어도 코드 자체가 그 사람 신원을 "증명"하는 건 아니라서(코드가 새어나가면 다른 사람도 그 이름으로 들어올 수 있음), 강한 보안이 필요하면 Streamlit Cloud 자체의 **Settings → Sharing → Private + 이메일 초대** 기능을 대신(또는 같이) 쓰세요 — 그러면 초대된 구글 계정으로 로그인해야만 접속 가능해집니다.
>
> 참고: 클라우드 저장공간은 완전히 영구적이지 않아서(앱이 오래 잠들었다 깨어나면 초기화될 수 있음), 워치리스트가 가끔 비어 보이면 다시 등록해주면 됩니다.

## 알려진 한계 (구조적이라 지금 당장은 해결 안 한 것들)

- **API 쿼터를 모든 사용자가 공유**: 접속 코드로 초대된 사람 전부가 같은 `YOUTUBE_API_KEY`를 씁니다. 하루 10,000 units를 다 같이 나눠 쓰는 구조라, 인원/사용량이 늘면 그날 쿼터가 바닥날 수 있어요.
- **워치리스트/스냅샷이 완전히 영구적이지 않음**: Streamlit Community Cloud의 저장공간은 앱이 오래 잠들었다 깨어나면 초기화될 수 있습니다. 진짜 영구 저장이 필요하면 SQLite/Postgres 같은 외부 DB로 옮겨야 해요.
- **호스팅 자체의 슬립/콜드스타트**: 무료 Streamlit Cloud는 며칠간 방문자가 없으면 잠들고, 깨어날 때 첫 방문자가 몇십 초 기다려야 할 수 있습니다.
- **`[users]`를 써도 코드 자체는 여전히 "그 사람만 아는 비밀"에 의존**: 코드가 새어나가면 다른 사람이 그 이름으로 들어올 수 있습니다. 특정 한 사람만 확실히 차단하려면 그 사람 코드만 Secrets에서 지우면 되지만(다른 사람에게는 영향 없음), 진짜 신원 인증이 필요하면 Streamlit Cloud의 Private + 이메일 초대 기능을 쓰세요.

## 다음 단계 (Claude Code에서 이어서 할 일)

1. `youtube_channel_api_spec.md` 의 데이터 모델(channels/videos/channel_snapshots 테이블)을 기준으로 SQLite/Postgres DB 스키마 만들기 (지금은 JSON 파일로 대체 중)
2. `vling_style_internal_tool_design.md` 의 로드맵 진행 상황
   - ✅ 채널 등록(watchlist) — `channels.json`
   - ✅ 매일 스냅샷 — 방문할 때마다 하루 1건씩 기록하는 방식으로 구현 (`channel_snapshots.json`), 진짜 크론은 아직 아님
   - ✅ compare_channels 비교 분석 기능 — "📊 전체 비교" 화면
   - ⬜ alert_rules + 알림 발송(Slack/이메일)
   - ⬜ 정기 리포트 → Claude 프로젝트 지식 파일 업데이트 (MVP)
   - ⬜ 필요시 MCP 서버로 전환해 Claude와 실시간 연동

Claude Code에게 "vling_style_internal_tool_design.md 읽고 2단계부터 시작해줘" 라고 요청하면 이어서 진행할 수 있습니다.
