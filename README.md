# 유튜브 분석 프로젝트

Claude(Cowork)와 함께 설계한 유튜브 채널 분석 프로젝트입니다. 이 폴더에서 `claude` 를 실행해서 개발을 이어가면 됩니다.

## 폴더 구성

- `youtube_analysis_project_instructions.md` — Claude 프로젝트(대화형 분석)에 넣을 커스텀 지침
- `youtube_channel_api_spec.md` — 채널/영상 데이터 API 명세 (필요 필드, 쿼터 비용, 데이터 모델)
- `vling_style_internal_tool_design.md` — 채널 비교 분석 + 모니터링/알림 기능 설계안 (아키텍처, 로드맵)
- `youtube_channel_fetcher.py` — 실제로 채널 정보/영상 통계를 가져오는 검증된 프로토타입 스크립트
- `app.py` — `youtube_channel_fetcher.py`를 감싼 로컬 전용 Streamlit 웹앱 (배포용 아님)
- `requirements.txt` — 의존성 목록
- `tests/` — 순수 함수(네트워크 호출 없음) 단위 테스트

## 다음 단계 (Claude Code에서 이어서 할 일)

1. `pip install -r requirements.txt` 로 의존성 설치
2. `YOUTUBE_API_KEY` 환경변수 설정
3. `python youtube_channel_fetcher.py --handle 찹챠` 실행해서 정상 동작 확인
   - 테스트만 돌려보려면: `python -m unittest discover -s tests`
   - 웹 UI로 써보려면: `streamlit run app.py` (본인 컴퓨터에서만 열리는 로컬 전용 화면)
4. `youtube_channel_api_spec.md` 의 데이터 모델(channels/videos/channel_snapshots 테이블)을 기준으로 SQLite/Postgres DB 스키마 만들기
5. `vling_style_internal_tool_design.md` 의 로드맵 1~5단계를 순서대로 진행
   - 채널 등록(watchlist) + 매일 스냅샷 크론
   - compare_channels 비교 분석 기능
   - alert_rules + 알림 발송(Slack/이메일)
   - 정기 리포트 → Claude 프로젝트 지식 파일 업데이트 (MVP)
   - 필요시 MCP 서버로 전환해 Claude와 실시간 연동

Claude Code에게 "vling_style_internal_tool_design.md 읽고 2단계부터 시작해줘" 라고 요청하면 이어서 진행할 수 있습니다.
