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
- `.streamlit/secrets.toml.example` — 클라우드 배포용 Secrets 예시 (실제 키는 여기 적지 않음)

## 웹앱 (`app.py`) 화면 구성

- **왼쪽 사이드바**: 등록한 채널 목록(로고 + 채널명), 맨 아래에 ⚙️ 설정 탭
- **홈 (첫 화면)**: 인기 급상승 · 게임 카테고리(국내) Top 10
- **채널 선택 시**: 구독자/총조회수/참여율/숏폼비중 요약 지표 + 최근 영상 5개
- **설정 탭**: API 키 입력, 채널 핸들로 등록/삭제 (`channels.json`에 저장되어 다음 실행 때도 유지됨)
  - API 키를 환경변수나 Streamlit Secrets로 미리 등록해두면(아래 "비공개로 다른 사람에게 공유하기" 참고), 이 탭에는 키 입력창 대신 "관리자가 설정해둔 키 사용 중" 안내만 뜨고, 초대된 사람은 실제 키 값을 볼 수 없습니다.

## 로컬에서 실행하기

가장 쉬운 방법: 바탕화면의 **"유튜브 채널 분석"** 바로가기(또는 프로젝트 폴더의 `run.bat`)를 더블클릭하면 venv 활성화 → 서버 실행 → 브라우저 자동 오픈까지 한 번에 됩니다.

수동으로 하려면:
1. `pip install -r requirements.txt` 로 의존성 설치
2. `YOUTUBE_API_KEY` 환경변수 설정 (또는 웹 UI의 설정 탭에서 직접 입력)
3. `python youtube_channel_fetcher.py --handle 찹챠` 실행해서 정상 동작 확인
   - 테스트만 돌려보려면: `python -m unittest discover -s tests`
   - 웹 UI로 써보려면: `streamlit run app.py --server.address 127.0.0.1` (다른 기기에서 접근 못 하게 루프백에만 바인딩)

## 비공개로 다른 사람에게 공유하기 (Streamlit Community Cloud)

허용한 사람만 접속하게 하려면, 이 저장소를 Streamlit Community Cloud에 **비공개 앱**으로 올리고 이메일로 초대하는 방식을 씁니다. YouTube API는 초과해도 자동 과금되지 않고 그날 요청이 막히기만 하니(무료 쿼터, 하루 10,000 units), 소수 인원이면 안전합니다.

1. [share.streamlit.io](https://share.streamlit.io) 에서 본인 GitHub 계정으로 로그인
2. "New app" → 이 저장소(`dbscks72-lgtm/youtube-analysis`) 선택, main file은 `app.py`
3. 배포 전/후 **Settings → Secrets**에 아래 내용 추가 (`.streamlit/secrets.toml.example` 참고):
   ```
   YOUTUBE_API_KEY = "본인의_실제_API_키"
   ```
4. 배포 후 **Settings → Sharing**에서 앱을 **Private**으로 바꾸고, 초대할 사람들의 이메일을 추가
5. 초대된 사람은 자기 구글 계정으로 로그인해야만 접속 가능하고, 앱 안에서 API 키 값은 보지 못합니다 (설정 탭에 안내 메시지만 뜸)

> 참고: 여러 명이 동시에 쓰는 공유 앱이라 `channels.json` 워치리스트도 모두가 같이 보고 편집하는 공용 목록이 됩니다. 또한 클라우드 저장공간은 완전히 영구적이지 않아서(앱이 오래 잠들었다 깨어나면 초기화될 수 있음), 워치리스트가 가끔 비어 보이면 다시 등록해주면 됩니다.

## 다음 단계 (Claude Code에서 이어서 할 일)

1. `youtube_channel_api_spec.md` 의 데이터 모델(channels/videos/channel_snapshots 테이블)을 기준으로 SQLite/Postgres DB 스키마 만들기
2. `vling_style_internal_tool_design.md` 의 로드맵 1~5단계를 순서대로 진행
   - 채널 등록(watchlist) + 매일 스냅샷 크론
   - compare_channels 비교 분석 기능
   - alert_rules + 알림 발송(Slack/이메일)
   - 정기 리포트 → Claude 프로젝트 지식 파일 업데이트 (MVP)
   - 필요시 MCP 서버로 전환해 Claude와 실시간 연동

Claude Code에게 "vling_style_internal_tool_design.md 읽고 2단계부터 시작해줘" 라고 요청하면 이어서 진행할 수 있습니다.
