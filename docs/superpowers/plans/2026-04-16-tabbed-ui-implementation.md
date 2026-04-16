# Premium Tabbed UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Streamlit UI를 3가지 핵심 탭(대화, 소스, 리포트)으로 분리하고 프리미엄 디자인(CSS)을 적용하여 가독성과 심미성을 고도화합니다.

**Architecture:** `st.tabs`를 메인 컨테이너로 사용하며, 분석 진행 상태와 소스 수집 현황을 각 탭에 실시간으로 반영합니다. `article_list`와 `search_results`를 세션 메시지와 동기화하여 탭 전환 중에도 데이터가 유실되지 않도록 설계합니다.

**Tech Stack:** Streamlit, Custom CSS, LangGraph (State management)

---

### Task 1: 고도화된 CSS 시스템 및 세션 초기화 확장

**Files:**
- Modify: `streamlit_app.py:22-146`

- [ ] **Step 1: 프리미엄 카드 디자인 및 탭 스타일링 CSS 추가**
    - `Article Card`용 Glassmorphism 효과 추가
    - 탭 바(`stTabs`)의 선택 상태 가독성 강화
    - 리포트 컨테이너의 타이포그래피(Line-height, Font-size) 미세 조정

- [ ] **Step 2: 세션 상태(st.session_state) 필드 확장**
    - `article_list`, `search_results`를 세션 상태에 추가하여 탭 전환 시 데이터 유지 보장

- [ ] **Step 3: 초기화 버튼 로직 업데이트**
    - 새롭게 추가된 세션 필드들도 초기화되도록 `st.button("🔄 대화 초기화")` 로직 수정

---

### Task 2: 메인 탭(st.tabs) 구조 및 실시간 상태바 구현

**Files:**
- Modify: `streamlit_app.py:151-182`

- [ ] **Step 1: 메인 레이아웃에 st.tabs 도입**
    - `chat_tab, source_tab, report_tab = st.tabs(["💬 AI 대화", "🔍 수집된 소스", "📊 심층 리포트"])` 선언

- [ ] **Step 2: 대화 탭(Chat Tab) 구성**
    - 기존 채팅 내역 및 채팅 입력창을 `chat_tab` 내부로 이동

- [ ] **Step 3: 진행 상태 표시(st.status) 최적화**
    - 에이전트 실행 중 나타나는 상태 메시지를 `chat_tab` 상단 또는 내부에 깔끔하게 배치

---

### Task 3: '수집된 소스(Sources)' 탭 카드형 인터페이스 구현

**Files:**
- Modify: `streamlit_app.py:184-213` (신규 로직 삽입)

- [ ] **Step 1: 데이터 추출 및 세션 동기화 로직 추가**
    - `app.stream` 도중 또는 완료 후 `search_results`와 `article_list`를 세션 상태에 저장

- [ ] **Step 2: Article Card 렌더링 함수 작성**
    - `source_tab` 내에서 `search_results`를 순회하며 카드 UI 생성
    - 제목, 출처(Domain), 스니펫, 수집 배지(Badge) 표시

- [ ] **Step 3: 인터랙티브 링크 추가**
    - 각 카드 상단에 원문으로 연결되는 하이퍼링크 적용

---

### Task 4: '심층 리포트(Analysis)' 탭 전문 뷰어 구현

**Files:**
- Modify: `streamlit_app.py:200-213` (위치 이동)

- [ ] **Step 1: 리포트 탭 내 문서 렌더링**
    - `report_tab` 내에서 `report_path` 존재 여부 확인 후 `report-container` 스타일로 출력

- [ ] **Step 2: 다운로드 버튼 고도화**
    - 리포트 상단에 강조된 다운로드 섹션 배치

- [ ] **Step 3: 빈 상태(Empty State) 처리**
    - 분석 전에는 "아직 생성된 리포트가 없습니다."라는 안내 메시지 표시

---

### Task 5: 전체 워크플로우 통합 테스트 및 최종 폴리싱

**Files:**
- Test: `streamlit_app.py` 실행 및 다중 기사 분석 시뮬레이션

- [ ] **Step 1: end-to-end 테스트**
    - 검색 -> 3~5개 기사 수집 -> 탭별 데이터 실시간 업데이트 확인
- [ ] **Step 2: 탭 전환 내구성 테스트**
    - 분석 도중 탭을 옮겨 다녀도 에이전트 작업이 중단되거나 화면이 깨지지 않는지 확인
- [ ] **Step 3: 디자인 최종 검토**
    - 텍스트 정렬, 카드 여백, 색상 대비 등 프리미엄 감성 최종 점교
