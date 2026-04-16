# 프로젝트 메모리

## 1. 개요

LangGraph 프레임워크를 기반으로 한 **기사 심층 분석 에이전트** 시스템입니다. 실시간 웹 기사 추출, 다중 에이전트 협업을 통한 품질 검증, 그리고 최종적인 마크다운 리포트 생성을 자동화하는 것을 목표로 합니다.

---

## 2. 분석 (프로젝트 구조 및 상태)

### 가. 프로젝트 구조
- **`graphs/`**: 시스템의 핵심 로직 및 에이전트 워크플로우 정의.
    - `agents/`: 독립적인 책임을 갖는 노드 파일 (Supervisor, Collector, Analyst, Validator).
    - `state.py`: `AgentState` (TypedDict)를 활용한 상태 중심 관리.
    - `workflow.py`: `StateGraph`를 통한 에이전트 간 제어 흐름 구성.
- **`tools/`**: 에이전트가 사용하는 기능적 도구 모음.
    - `web_tools.py`: Tavily 기반 검색 기능.
    - `article_tools.py`: trafilatura 기반 본문 파싱 및 인코딩 처리.
    - `report_tools.py`: 분석 결과를 Markdown 파일로 저장.
- **인터페이스**:
    - `streamlit_app.py`: 스트림릿 기반 웹 UI (사용자 친화적인 대화형 환경).
    - `main.py`: 터미널 기반 CLI 환경.
- **`reports/`**: 생성된 기사 분석 리포트 저장소.

### 나. 현재 상태
- **Phase 4 완료**: 멀티 에이전트(Multi-Agent) 체계가 구축되어 분업화된 분석 수행 중.
- **기술 스택**: LangGraph, OpenAI (gpt-4o-mini), Tavily, Streamlit.

---

## 3. 옵션 (기존 설계 의사결정)

### [옵션 A] 단순 선형 체인 (Linear Chain)
- 설명: 이전 단계 결과가 다음 단계로 전달되는 단순 구조. 빠르지만 에러 발생 시 복구(Self-correction)가 어려움.

### [옵션 B] 상태 중심 그래프 (LangGraph) - 선택됨
- 설명: 노드 간 순환(Loopy)이 가능하며, 상태(State)를 공유하여 중단된 지점부터 재개하거나 품질 미달 시 재시도(Validator 노드 등)가 가능함.


---

## 4. 선택 (확정된 결정)

### [확정] 아키텍처 및 구현 방향
- **선택된 옵션**: [옵션 B] 상태 중심 그래프 (LangGraph) 및 Supervisor-Worker 패턴
- **이유**: 복잡한 다중 에이전트 협업 환경에서 상태 보존과 에러 복구가 필수적이며, Supervisor를 통한 유연한 라우팅이 프로젝트의 확장성에 가장 적합함.

### [제약 사항/강제 규칙]
1. **LangGraph 기반**: 모든 핵심 워크플로우는 `LangGraph`의 `StateGraph`를 사용하여 구현하며, 단순 선형 체인 방식은 지양한다.
2. **Supervisor 패턴 준수**: 사용자 입력의 의도 파악 및 작업 배정은 반드시 `Supervisor` 노드를 거쳐야 한다.
3. **엄격한 상태 관리**: `graphs/state.py`에 정의된 `input_type` (Literal 5종)을 엄격히 준수하여 로직 분기를 관리한다.
4. **실시간성 우선**: 정보의 최신성을 보장하기 위해 고정된 지식 베이스(RAG)보다 실시간 웹 검색 및 추출 데이터를 우선적으로 활용한다.

---


## 5. 반영 (구현 특징)

- **자가 수정 로직**: `Validator` 에이전트가 본문 추출 품질을 확인하고, 실패 시 `retry_count`를 체크하며 재수집을 시도함.
- **대화 맥락 유지**: `Analyst` 노드에서 전체 `messages` 이력을 참조하여 분석 결과에 대한 후속 질문 처리가 가능하도록 구현함.
- **모듈화**: 기존 `nodes.py`를 각 에이전트별로 분리하여 유지보수성 향상.

---

## 7. 브레인스토밍 및 설계 (서비스 고도화: 다각도 합성 강화)

### 가. 분석 결과 (취약점 및 개선 방향)
- **취약점**: 토큰 비용 폭주, 정보 상충 시 환각 위험, 검색 API 병목, 보안(SSRF) 취약성.
- **보완 방향**: **'다중 기사 비교 분석(Multi-source Synthesis)'** 및 **'인텐트 디스커버리(Intent Discovery)'** 도입.

### 나. 확정된 디자인 (Approved Design)

#### 1. 인텐트 디스커버리 (Supervisor 강화)
- 사용자의 단순 요청에서 '구체적인 분석 목표(Analysis Objective)'를 추출.
- 예: "경제적 파급 효과", "기술적 타당성" 등 분석 관점을 미리 설정하여 하위 에이전트에 전달.

#### 2. 다중 수집 및 병렬 처리 (Collector & Tools)
- 단일 기사가 아닌 상위 N개(3~5개) 기사를 비동기(`asyncio`)로 동시 수집.
- 정보의 다양성(Source Diversity)을 확보하여 편향성 제거.

#### 3. 비교 분석 및 교차 검증 (Analyst)
- 기사 간 **합의점(Consensus)**과 **상충점(Divergence)**을 대조하여 리포트 생성.
- 사용자 맞춤형 인사이트 도출을 위한 '의도 기반 분석' 프롬프트 적용.

#### 4. 상태 관리 최적화 (`AgentState`)
- `article_list`: 수집된 기사 정보를 담는 리스트 구조 추가.
- `analysis_objective`: 추출된 사용자 의도를 공유하기 위한 필드 추가.

### 다. 적용 예정 기술
- **비동기 처리**: `httpx` 또는 `asyncio` 기반 파싱 로직.
- **프롬프트 기법**: Chain-of-Thought (CoT) 및 Cross-Reference Reasoning.
- **보안**: URL 도메인 및 리스폰스 사이즈 검증 로직 추가.

---

## 8. 최종 반영 (다중 기사 합성 및 의도 파악 구현 완료 - 2026-04-16)

배포된 상세 설계서([Specs](file:///c:/dev/Project/article_analyst_agent/docs/superpowers/specs/2026-04-16-multi-article-synthesis-design.md))에 따라 다음 기능을 최종 구현 및 반영하였습니다.

### 🔹 상태 관리 고도화
- `AgentState` 내 `article_list` 및 `analysis_objective` 필드를 추가하여 다중 뉴스 소스와 구체적인 분석 의도를 전역적으로 추적할 수 있도록 개선하였습니다.

### 🔹 인텐트 디스커버리 시스템
- `Supervisor` 노드(`classifier_node`)가 사용자 입력에서 단순히 유형을 분류하는 것을 넘어, "무엇을 분석해야 하는가"에 대한 구체적인 문장(Analysis Goal)을 생성하도록 프롬프트를 고도화하였습니다.
- JSON 기반의 응답 체계를 도입하여 데이터 흐름의 안정성을 확보하였습니다.

### 🔹 다중 기사 수집 및 동기화 로직
- `Collector` 노드(`call_model`)가 검색 결과 중 상위 3~5개의 핵심 기사를 선택하여 도구를 동시 호출할 수 있도록 지침을 강화하였습니다.
- `state_sync_node`가 AI 메시지 이후의 모든 도구 응답을 순회하며 `article_list`에 중복 없이 누적하도록 로직을 개편하였습니다.

### 🔹 비교 및 합성 분석 (Synthesis)
- `Analyst` 노드의 시스템 프롬프트를 전면 개편하여, 여러 기사 간의 **합의점(Consensus)**과 **상충점(Divergence)**을 대조 분석하도록 하였습니다.
- 추출된 `analysis_objective`를 최우선 가이드라인으로 설정하여 사용자 맞춤형 인사이트 도출을 유도하였습니다.

### 🔹 보안 및 안정성
- `article_parser_tool`에 URL 스키마 검증 및 도메인 필터링 로직을 추가하여 외부 소스 연결 시의 보안성을 강화하였습니다.

**현재 상태**: 설계 및 구현 완료. 시스템은 이제 단일 기사 분석을 넘어 다각도 인사이트 합성 엔진으로 작동합니다.
