# graphs/state.py
from typing import TypedDict, Annotated, Literal, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages

class AgentState(TypedDict):
    """기사 분석 에이전트의 상태를 관리하는 클래스"""
    
    # 대화 이력 (add_messages를 통해 순차적으로 병합됨)
    messages: Annotated[Sequence[BaseMessage], add_messages]
    
    # 사용자 입력 원본
    user_input: str
    
    # 입력 타입 분류: 5가지 케이스에 대한 엄격한 정의
    input_type: Literal["url_analysis", "search_and_analyze", "followup_question", "compare_articles", "general_chat"]
    
    # 현재 분석 중인 기사 URL
    current_article_url: str
    
    # 기사 제목 (추출 결과)
    article_title: str
    
    # 기사 본문 텍스트 (추출 결과)
    article_body: str
    
    # 재시도 횟수 관리 (무한 루프 방지)
    retry_count: int
    
    # 검색 수행 시 반환된 결과 리스트
    search_results: list[dict[str, str]]
    
    # 다수 기사 중 분석 대상으로 선택된 단일 기사 정보
    selected_article: dict[str, str]
    
    # 구조화된 분석 결과 (요약, 인물, 기관, 장소, 논조, 인사이트 등)
    # dict 내부는 실제 분석 항목에 맞춰 상세화 가능하나, 일단 dict[str, str | list[str]] 수준으로 정의
    analysis_result: dict[str, str | list[str]]
    
    # 저장된 리포트 파일 경로
    report_path: str
    
    # 단계별 에러 발생 시 기록되는 메시지
    error_message: str
