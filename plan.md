# Article Analyst Agent Implementation Plan

본 문서는 `LangChain/1.colab/6. Tools_Agents/article_analyst_agent` 프로젝트의 실무형 기사 분석 에이전트 구축을 위한 구조화된 계획서입니다. `LLM_study` 내의 기존 코드 자산과 패턴을 참조하여 확장 가능한 시스템을 설계합니다.

## 1. 프로젝트 범위 (Scope)

### 가. MVP 범위 (Phase 1-2)
- **입력**: 단일 기사 URL 1개
- **기능**: 본문 텍스트 추출, 구조화된 요약 및 심층 분석 리포트 생성
- **출력**: Markdown 형식의 리포트 파일 저장

### 나. 확장 범위 (Phase 3+)
- **검색 기반 분석**: 키워드 입력 시 관련 뉴스 탐색 및 분석 대상 선정
- **다중 기사 비교**: 여러 기사의 논조 비교 및 공통/차이점 도출
- **멀티 에이전트 워크플로우**: 주제별 수집, 품질 검증, 종합 분석 에이전트 협업

## 2. 상세 분석된 기존 파일 및 활용 방안
`LLM_study` 내의 검증된 패턴을 참조하여 개발 효율성을 높입니다.

- **환경 설정 (`.env`)**: `TAVILY_API_KEY` 설정을 공유하여 실시간 정보 검색 성능을 확보합니다.
- **상태 관리 패턴 (`graphs/state.py`)**: `Annotated`와 `add_messages`를 활용한 이력 관리 방식을 차용하고, 기사 메타데이터와 분석 결과를 담을 수 있도록 상태를 확장합니다.
- **워크플로우 설계 (`main.py`)**: `langgraph.graph.StateGraph` 기반의 노드 제어 흐름과 `MemorySaver`를 통한 세션 관리 기법을 재사용합니다.
- **분기 로직 (`4.LCEL/2.RunnableBranch`)**: 사용자 입력의 성격(URL, 검색어, 일반 질문, 비교 요청 등)에 따라 유연하게 라우팅하는 분기 패턴을 적용합니다.
- **도구 정의 기술 (`tools/web_tools.py`)**: Tavily API의 `score` 기반 필터링 로직을 참조하여 고품질 기사를 선별합니다.
- **시각화 코드 (`tools/python_tools.py`)**: Matplotlib을 활용한 `create_simple_plot` 구현 방식을 참고하여 키워드 빈도 및 엔티티 출현 비율 시각화를 검토합니다.

## 3. 프로젝트 아키텍처 및 역할 분담

구조적 안정성을 위해 노드, 도구, LLM의 책임을 명확히 분리합니다.

- **Node (흐름 제어)**: 상태를 읽고 다음 실행 단계(Next Step)를 결정하는 오케스트레이터 역할.
- **Tool (외부 작업)**: 검색, 본문 추출(trafilatura), 파일 I/O 등 부수 효과(Side Effect)가 발생하는 작업 담당.
- **LLM (추론 및 생성)**: 분류(Classification), 요약, 엔티티 추출, 인사이트 도출 등 판단 작업 담당.

### 가. 확장된 에이전트 상태 (Agent State)
```python
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    user_input: str             # 원본 사용자 입력
    input_type: str             # url_analysis / search_and_analyze / followup / compare
    current_article_url: str    # 분석 중인 기사 주소
    article_title: str          # 기사 제목
    article_body: str           # 추출된 순수 본문 텍스트
    search_results: list        # 검색 시 검색 결과 리스트 보관
    selected_article: dict      # 다수 중 선택된 기사 정보
    analysis_result: dict       # 요약, 엔티티, 톤 등 구조화된 분석 결과
    report_path: str            # 생성된 리포트 파일 경로
    error_message: str          # 단계별 에러 발생 시 로그 기록
```

### 나. 입력 분류 기준 (Routing Logic)
단순 분류를 넘어 사용자 의도를 구체적으로 파악합니다.
1. `url_analysis`: URL이 직접 입력된 경우의 분석 흐름.
2. `search_and_analyze`: 특정 주제에 대한 뉴스 탐색이 필요한 경우.
3. `followup_question`: 이전 분석 결과에 대한 추가 질문(예: "리스크만 다시 요약해줘").
4. `compare_articles`: 여러 기사 간의 차이점 비교 요청.
5. `general_chat`: 도구 호출이 필요 없는 일반적인 대화.

## 4. 분석 및 리포트 명세

### 가. 주요 분석 항목 (Deep Analysis)
단순 요약을 넘어 기사의 구조와 의도를 파악합니다.
- **요약**: 1회성 한 줄 요약 및 3~5문장 핵심 요약.
- **엔티티**: 핵심 인물, 기관, 장소, 날짜 추출.
- **심층 속성**: 기사의 논조(Tone), 주장과 사실의 분리, 잠재적 편향성(Bias) 분석.
- **전략적 인사이트**: 핵심 리스크 및 기회 요인 도출, 연관 후속 질문 추천.

### 나. 리포트 출력 규격 (`analysis_reporter_tool`)
- **파일명 규칙**: `article_report_YYYYMMDD_HHMMSS.md`
- **파일명 구조**: `reports/` 폴더 내에 저장.
- **섹션 구성**: 기사 정보(제목, URL, 추출일시), 요약, 핵심 포인트, 인사이트, 주의사항 및 한계점.

## 5. 예외 처리 정책 (Error Handling)

안정적인 에이전트 작동을 위해 단계별 실패 대응 시나리오를 구성합니다.

- **본문 추출 실패**: `trafilatura` 파싱 불가 시 원문 메타데이터 및 LLM의 기본 지식을 기반으로 제한적 분석 수행 후 경고 메시지 출력.
- **검색 품질 저하**: 관련성 점수가 낮을 경우 에이전트가 단독 결정하지 않고 상위 후보군을 사용자에게 제시하여 선택 유도.
- **출력 파싱 에러**: LLM의 응답이 JSON 형식을 벗어날 경우 Raw Text를 보존하는 Fallback 로직 적용.
- **리포트 저장 실패**: 파일 시스템 에러 시 터미널/화면 출력을 우선적으로 보장.

## 6. 구현 단계별 전략

### Phase 1: 기반 구조 구축 [x]
- `investment_analyst_agent` 패턴을 참조한 그래프 뼈대 및 확장 상태 설계.
- `Classifier` 노드의 프롬프트 엔지니어링 및 기본 라우팅 구현.

### Phase 2: 추출 및 분석 파이프라인 (MVP) [x]
- `trafilatura` 라이브러리를 활용한 `article_parser_tool` 구현.
- 심층 분석 항목이 포함된 `Analyst` 노드의 System Message 최적화.
- Markdown 리포트 자동 생성 도구 구현.

### Phase 3: 검색 및 고도화 [x]
- Tavily 기반의 `search_and_analyze` 흐름 추가.
- 다중 기사 비교 분석 및 후속 질문 처리 로직 연동.

## 7. RAG(Retrieval-Augmented Generation) 제외 사유 [x]
본 프로젝트는 **실시간 웹 기사 추출 및 즉각적 분석 파이프라인**의 안정성 확보를 제 1목표로 합니다. 따라서 초기 단계에서는 인덱싱 기반의 Vector DB 시스템(RAG)보다는 실시간 추출 및 컨텍스트 기반 분석에 집중하여 정보의 최신성과 정확도를 확보합니다.

## 8. 테스트 시나리오 (Scenario-based Testing) [x]
- **URL 직접 입력**: 국내/외 주요 언론사 URL을 통한 본문 추출 및 분석 정확도 검증.
- **검색어 입력**: 주제어(예: "삼성전자 반도체 전망") 입력 시 검색 결과 선별 및 종합 분석 테스트.
- **후속 질문**: 분석된 리포트 내용에 대해 구체적인 세부 사항 질문 시 메모리 유지 여부 확인.
- **실패 대응**: 유료 기사나 렌더링이 복잡한 페이지 입력 시 에러 메시지 및 Fallback 작동 여부 확인.

---

## [완료] 멀티 에이전트 확장 (Phase 4) [x]
MVP 단계 완료 후, 분석 완성도를 높이기 위해 다음과 같은 멀티 에이전트 협업 체계를 고려합니다.
- **주제별 수집 에이전트**: 다양한 소스에서 뉴스 데이터를 대량 수집. [x]
- **Quality Validator 에이전트**: 수집된 뉴스의 중복성, 출처 신뢰도, 본문 확보 가능성 검증. [x]
- **종합 분석 에이전트**: 검증된 정보를 바탕으로 최종 리포트 통합 및 인사이트 도출. [x]
- **Supervisor 에이전트**: 사용자 입력을 바탕으로 위 에이전트들의 작업 순서를 조율. [x]

## 추가
- 모델에 대한 정확성이 떨어지는 것으로 파악 -> openai 키 사용하는걸로 모델을 변경
- 스트림릿 ui가 너무 어두워서 글이 안보임 글이 잘 보이도록 배경을 밝게 변경
- .env에 OPENAI_API_KEY 이미 이거 있어 따로 확인하지말고 바꿔줘 그리고  모델은 temperature 0.1로 설정(gpt-4o-mini 정확한 모델로 진행)