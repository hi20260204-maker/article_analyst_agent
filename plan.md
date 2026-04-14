# Article Analyst Agent Implementation Plan (LangGraph)

본 문서는 `LangChain` 에코시스템과 **`LangGraph`** 프레임워크를 기반으로 한 실무형 기사 분석 에이전트 구축 계획서입니다. 기존의 선형적인 체인을 넘어, 상태 중심(State-centric)의 노드 구조를 통해 유연하고 고품질인 분석 리포트 생성을 목표로 합니다.

## 1. 프로젝트 범위 (Scope) 및 기술 스택

### 가. 기술 스택 (Tech Stack)
- **Orchestration**: `LangGraph` (에이전트 제어 흐름 및 상태 관리)
- **Core LLM**: `OpenAI gpt-4o-mini` (Temperature: 0.1)
- **Interface**: `Streamlit` (High-Contrast Light Mode UI)
- **Tools**: `Tavily Search` (뉴스 검색), `trafilatura` (본문 파싱)

### 나. 프로젝트 범위
- **MVP**: 단일/검색 기사 분석 및 Markdown 리포트 생성
- **확장**: 다중 에이전트 협업(수집, 품질 검증, 종합 분석) 워크플로우

## 2. 상세 활용 방안 및 상태 관리

- **상태 관리 (`graphs/state.py`)**: `TypedDict`와 `Annotated`를 활용해 기사 메타데이터, 검색 결과, 최종 리포트를 체계적으로 관리합니다.
- **노드 제어 (`graphs/workflow.py`)**: `StateGraph`를 통해 단순 라우팅을 넘어 순환적인 에러 수정(Self-correction) 흐름을 구축합니다.
- **개별 에이전트 파일화**: Phase 4 고도화 단계에 맞춰 각 노드(Supervisor, Collector, Validator, Analyst)를 독립적인 파일로 구조화합니다.

## 3. 프로젝트 아키텍처 (LangGraph Nodes)

LangChain의 단순 호출 방식을 **LangGraph의 상태 노드**로 대체하여 각 단계의 독립성과 품질을 확보합니다.

1. **Supervisor Node (구 Classifier)**: 사용자 의도 파악 및 다음 노드(Collector/Analyst) 결정.
2. **Collector Node (구 Search)**: Tavily 및 파서를 이용한 원문 데이터 수집 및 상태 업데이트.
3. **Validator Node**: 추출된 본문의 품질을 검증하고, 실패 시 재수집 요청 또는 종료 결정.
4. **Analyst Node**: 검증된 정보를 바탕으로 최종 심층 분석 수행.
5. **Reporter Tool Node**: 분석 결과를 Markdown 리포트로 파일 저장.

## 4. 분석 및 리포트 명세

- **심층 속성**: 논조(Tone), 사실과 주장 분리, 인사이트 및 전략적 후속 질문.
- **출력 규격**: `reports/` 폴더 내 `article_report_YYYYMMDD_HHMMSS.md` 저장.

## 5. 예외 처리 및 Fallback

- **OpenAI 기반 복구**: 파싱 에러 시 LLM의 추론 기능을 통해 원문을 최대한 복구하거나 요약 정보 제공.
- **UI 접근성 고도화**: 스트림릿 배경을 밝게 유지하여 텍스트 가독성 극대화.

## 6. 구현 단계별 전략

### Phase 1: 기반 구조 구축 [x]
- LangGraph 뼈대 및 OpenAI(gpt-4o-mini) 연동 환경 구축.

### Phase 2: 추출 및 분석 파이프라인 [x]
- `trafilatura` 기반 파서 및 `Analyst` 노드 최적화.

### Phase 3: 검색 및 고도화 [x]
- Tavily 연동 및 검색-분석 라우팅 안정화.

### Phase 4: 멀티 에이전트 확장 (LangGraph 고도화) [x]
- 기존 `nodes.py`를 각 에이전트별 독립 노드 파일(`graphs/agents/`)로 분리 및 구조화.
- 노드 간 독립적인 책임(Collection, Analysis, Validation) 부여.

---
최종 수정일: 2026-04-14 (OpenAI gpt-4o-mini / LangGraph 중심 구조 반영)

## 7. 예외 처리 정책 (Error Handling)

안정적인 에이전트 작동을 위해 단계별 실패 대응 시나리오를 구성합니다.

- **본문 추출 실패**: `trafilatura` 파싱 불가 시 원문 메타데이터 및 LLM의 기본 지식을 기반으로 제한적 분석 수행 후 경고 메시지 출력.
- **검색 품질 저하**: 관련성 점수가 낮을 경우 에이전트가 단독 결정하지 않고 상위 후보군을 사용자에게 제시하여 선택 유도.
- **출력 파싱 에러**: LLM의 응답이 JSON 형식을 벗어날 경우 Raw Text를 보존하는 Fallback 로직 적용.
- **리포트 저장 실패**: 파일 시스템 에러 시 터미널/화면 출력을 우선적으로 보장.

## 8. RAG(Retrieval-Augmented Generation) 제외 사유 [x]
본 프로젝트는 **실시간 웹 기사 추출 및 즉각적 분석 파이프라인**의 안정성 확보를 제 1목표로 합니다. 따라서 초기 단계에서는 인덱싱 기반의 Vector DB 시스템(RAG)보다는 실시간 추출 및 컨텍스트 기반 분석에 집중하여 정보의 최신성과 정확도를 확보합니다.

## 9. 테스트 시나리오 (Scenario-based Testing) [x]
- **URL 직접 입력**: 국내/외 주요 언론사 URL을 통한 본문 추출 및 분석 정확도 검증.
- **검색어 입력**: 주제어(예: "삼성전자 반도체 전망") 입력 시 검색 결과 선별 및 종합 분석 테스트.
- **후속 질문**: 분석된 리포트 내용에 대해 구체적인 세부 사항 질문 시 메모리 유지 여부 확인.
- **실패 대응**: 유료 기사나 렌더링이 복잡한 페이지 입력 시 에러 메시지 및 Fallback 작동 여부 확인.

---

## 10. [완료] 멀티 에이전트 확장 (Phase 4) [x]
MVP 단계 완료 후, 분석 완성도를 높이기 위해 다음과 같은 멀티 에이전트 협업 체계를 고려합니다.
- **주제별 수집 에이전트**: 다양한 소스에서 뉴스 데이터를 대량 수집. [x]
- **Quality Validator 에이전트**: 수집된 뉴스의 중복성, 출처 신뢰도, 본문 확보 가능성 검증. [x]
- **종합 분석 에이전트**: 검증된 정보를 바탕으로 최종 리포트 통합 및 인사이트 도출. [x]
- **Supervisor 에이전트**: 사용자 입력을 바탕으로 위 에이전트들의 작업 순서를 조율. [x]

## 11. 수정 및 개선 필요 사항 (Current Issues & Improvements) [x]
- **인코딩 안정화**: `article_tools.py` 내 인코딩 감지 및 수동 디코딩 로직 보완.
- **무한 루프 방지**: `retry_count` 도입 및 워크플로우 제어 로직 강화.
- **UI 정보 정합성**: Streamlit 사이드바 모델 정보 수정 (Ollama -> OpenAI).

## 12. 최신 버그 수정 및 최적화 (Scenario 2 & 3 대응) [x]
검증 과정에서 발견된 핵심 로직 결함을 다음과 같이 해결하였습니다.

### 가. 검색-분석 전환 자동화 (Scenario 2)
- **문제**: 검색 결과 확보 후 상세 분석 단계로 넘어가지 않고 단순 중단되는 현상.
- **해결**: `collector.py`의 `call_model` 프롬프트를 강화하여 검색 결과 중 최적의 기사를 자동으로 선택하고 `article_parser_tool`을 즉시 호출하도록 강제함.

### 나. 대화 맥락 유지 및 후속 질문 처리 (Scenario 3)
- **문제**: 분석 리포트 생성 후 추가 질문 시 이전 기사 내용이나 대화 맥락을 기억하지 못함.
- **해결**: `Analyst` 노드에 전체 대화 이력(`messages`)을 전달하고, 시스템 프롬프트를 컨텍스트 기반 대화가 가능하도록 수정함.