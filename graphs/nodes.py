# graphs/nodes.py
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode
from langchain_core.messages import SystemMessage, HumanMessage
from typing import Literal
import json

# 상태 및 도구
from .state import AgentState
from tools.article_tools import article_parser_tool
from tools.web_tools import web_search_tool
from tools.report_tools import analysis_reporter_tool

# LLM 초기화 (OpenAI gpt-4o-mini 전환)
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)

# 모든 도구 리스트
tools = [article_parser_tool, web_search_tool, analysis_reporter_tool]
llm_with_tools = llm.bind_tools(tools)

def classifier_node(state: AgentState) -> dict[str, str]:
    """사용자의 입력을 분석하여 의도를 분류합니다."""
    print("\n--- [Nodes] Classifier 진입 ---")
    last_message = state["messages"][-1].content
    
    prompt = f"""
    당신은 입력 분류기입니다. 사용자의 다음 입력을 분석하여 'input_type'을 선택하세요.
    입력: "{last_message}"
    
    1. url_analysis: URL이 포함된 기사 분석 요청.
    2. search_and_analyze: 키워드 뉴스 검색 요청.
    3. followup_question: 이전 분석에 대한 추가 대화.
    4. general_chat: 인사 등 일반 대화.
    
    답변은 오직 영문 타입 키워드만 출력하세요. (예: url_analysis)
    """
    
    response = llm.invoke([HumanMessage(content=prompt)])
    input_type = response.content.strip().lower()
    
    valid_types = ["url_analysis", "search_and_analyze", "followup_question", "general_chat"]
    if not any(t in input_type for t in valid_types):
        # AI가 부연설명을 붙인 경우를 대비해 키워드 검색
        for t in valid_types:
            if t in input_type:
                input_type = t
                break
        else:
            input_type = "general_chat"
                
    print(f"  [결과] 의도 분류: {input_type}")
    return {"input_type": input_type, "user_input": str(last_message)}

def state_sync_node(state: AgentState) -> dict:
    """도구 실행 결과를 상태 필드에 동기화합니다."""
    print("--- [Nodes] State Sync 진입 ---")
    messages = state["messages"]
    last_message = messages[-1]
    
    if last_message.type == "tool":
        content = last_message.content
        print(f"  [Sync] 도구 응답 수신: {content[:50]}...")
        
        # 0. 도구 실행 에러 감지 (에러 응답인 경우)
        if '"error":' in content or "내용을 다운로드할 수 없습니다" in content:
            try:
                data = json.loads(content)
                error_msg = data.get("error", "알 수 없는 도구 실행 오류")
                print(f"  [Sync] 도구 오류 감지: {error_msg}")
                return {"error_message": error_msg}
            except:
                print("  [Sync] 원문 에러 메시지 동기화")
                return {"error_message": content}

        # 1. article_parser_tool 결과 처리
        if '"content":' in content:
            try:
                data = json.loads(content)
                print("  [Sync] 기사 본문 동기화 완료")
                return {
                    "article_body": data.get("content", ""),
                    "article_title": data.get("title", "제목 없음"),
                    "current_article_url": data.get("url", "")
                }
            except: pass
            
        # 2. web_search_tool 결과 처리
        if content.startswith("["):
            print("  [Sync] 검색 결과 동기화 완료")
            try:
                search_data = json.loads(content)
                return {"search_results": search_data}
            except: pass

        # 3. analysis_reporter_tool 결과 처리
        if content.endswith(".md") or "reports\\" in content or "reports/" in content:
            print(f"  [Sync] 리포트 경로 동기화: {content}")
            return {"report_path": content, "analysis_result": {"status": "completed"}}
                
    return {}

def validator_node(state: AgentState) -> dict[str, str]:
    """본문 품질을 검증합니다."""
    print("--- [Nodes] Validator 진입 ---")
    article_body = state.get("article_body", "")
    
    if not article_body or len(article_body) < 100:
        print("  [결과] 본문 품질 미달 (FAIL)")
        return {"error_message": "유효한 기사 본문을 확보하지 못했습니다."}
        
    prompt = f"다음 본문이 뉴스 기사로서 분석 가능한 수준인지 PASS/FAIL로만 답하세요.\n본문: {article_body[:300]}..."
    response = llm.invoke([HumanMessage(content=prompt)])
    
    res = response.content.upper()
    print(f"  [결과] 품질 검증: {res}")
    return {"error_message": "" if "PASS" in res else "기사 품질이 낮아 분석을 중단합니다."}

def analyst_node(state: AgentState) -> dict[str, list]:
    """심층 분석을 수행하고 리포트 생성 도구를 호출합니다."""
    print("--- [Nodes] Analyst 진입 ---")
    article_body = state.get("article_body", "")
    article_title = state.get("article_title", "기사 분석")
    current_url = state.get("current_article_url", "")
    
    system_prompt = """
    당신은 '전문 기사 분석가'입니다. 제공된 본문을 분석하고 반드시 'analysis_reporter_tool'을 호출하여 리포트를 저장하세요.
    리포트 본문(report_body)에는 다음 항목이 Markdown 형식으로 상세히 포함되어야 합니다:
    1. 요약 (핵심 3~5문장)
    2. 주요 엔티티 (인물, 기관, 장소)
    3. 심층 분석 (논조, 사실과 주장, 편향성)
    4. 인사이트 (리스크/기회, 후속 질문)
    
    모든 분석은 한국어로 수행하세요.
    """
    
    print("  [Analyst] OpenAI 분석 및 도구 호출 생성 중...")
    response = llm_with_tools.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"기사: {article_title}\nURL: {current_url}\n본문: {article_body}")
    ])
    
    return {"messages": [response]}

def call_model(state: AgentState) -> dict[str, list]:
    """초기 도구 호출(추출/검색) 및 검색 결과 선택을 위한 노드입니다."""
    print("--- [Nodes] Agent(call_model) 진입 ---")
    messages = state["messages"]
    input_type = state.get("input_type", "general_chat")
    search_results = state.get("search_results", [])
    
    intent_guide = ""
    # 1. 일반적인 URL 분석 요청
    if input_type == "url_analysis":
        intent_guide = "사용자가 URL을 주었습니다. 'article_parser_tool'을 사용하여 본문을 추출하세요."
    
    # 2. 검색 요청 시
    elif input_type == "search_and_analyze":
        if not search_results:
            intent_guide = "사용자가 주제 검색을 요청했습니다. 'web_search_tool'을 사용하여 뉴스를 찾으세요."
        else:
            # 검색 결과가 이미 있는 경우 -> 선택 유도
            intent_guide = f"""
            현재 다음 뉴스 검색 결과가 확보되었습니다:
            {json.dumps(search_results, ensure_ascii=False, indent=2)}
            
            위 결과 중 가장 내용이 풍부하고 관련성 높은 기사 1개를 선택하세요.
            선택한 기사의 URL을 사용하여 'article_parser_tool'을 호출하세요.
            """
    
    if intent_guide:
        # 가이드를 시스템 메시지로 추가하여 도구 호출 성능 극대화
        messages = [SystemMessage(content=intent_guide)] + messages
        
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

execute_tools = ToolNode(tools)
