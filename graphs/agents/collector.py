# graphs/agents/collector.py
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode
from langchain_core.messages import SystemMessage, HumanMessage
from ..state import AgentState
from tools.article_tools import article_parser_tool
from tools.web_tools import web_search_tool
from tools.report_tools import analysis_reporter_tool

load_dotenv()
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
tools = [article_parser_tool, web_search_tool, analysis_reporter_tool]
llm_with_tools = llm.bind_tools(tools)

def call_model(state: AgentState) -> dict:
    """초기 도구 호출(추출/검색) 및 다중 기사 선택을 위한 노드입니다."""
    print("--- [Nodes] Agent(call_model) 진입 ---")
    messages = state["messages"]
    input_type = state.get("input_type", "general_chat")
    search_results = state.get("search_results", [])
    retry_count = state.get("retry_count", 0)
    analysis_objective = state.get("analysis_objective", "")
    
    # 무한 루프 방지 로직
    if retry_count >= 3:
        return {"error_message": "최대 재시도 횟수를 초과했습니다. URL을 확인하거나 검색어를 변경해주세요."}

    intent_guide = ""
    if input_type == "url_analysis":
        intent_guide = f"사용자가 URL을 주었습니다. 'article_parser_tool'을 사용하여 본문을 추출하세요. 분석 목표: {analysis_objective}"
    elif input_type == "search_and_analyze":
        if not search_results:
            intent_guide = f"""
            사용자가 뉴스 검색 및 분석을 요청했습니다. 
            분석 목표: {analysis_objective}
            
            위 목표를 달성하기 위해 가장 적합한 최신 뉴스를 찾을 수 있는 **핵심 키워드 2~3개**를 생성하여 'web_search_tool'을 호출하세요.
            (예: "삼성전자 HBM 양산 계획", "반도체 시장 점유율 전망" 등)
            """
        else:
            intent_guide = f"""
            [강제 지시]
            당신은 현재 뉴스 검색 결과를 분석 목표({analysis_objective})에 맞춰 선별하는 단계에 있습니다.
            
            1. 아래 검색 결과 중 분석 가치가 높은 **서로 다른 기사 3~5개**를 선택하세요.
            2. 선택한 각 기사의 URL에 대해 **반드시 'article_parser_tool'을 각각 호출**하세요.
            3. 사용자에게 검색 결과를 설명하거나 텍스트로 답변하지 마세요. 
            4. 오직 도구 호출(tool_calls)만 생성하세요. 텍스트 응답은 금지됩니다.

            검색 결과:
            {json.dumps(search_results, ensure_ascii=False, indent=2)}
            """
    
    if intent_guide:
        messages = [SystemMessage(content=intent_guide)] + messages
        
    response = llm_with_tools.invoke(messages)
    return {"messages": [response], "retry_count": retry_count + 1}

def state_sync_node(state: AgentState) -> dict:
    """도구 실행 결과를 상태 필드에 동기화하며, 다중 기사를 article_list에 누적합니다."""
    print("--- [Nodes] State Sync 진입 ---")
    messages = state["messages"]
    
    # 마지막 AI 메시지 이후의 모든 도구 응답을 찾아 처리
    new_updates = {
        "article_list": state.get("article_list", []) or [],
        "search_results": state.get("search_results", []),
        "error_message": ""
    }
    
    # 마지막 AI 메시지 인덱스 찾기
    last_ai_idx = -1
    for i in range(len(messages) - 1, -1, -1):
        if messages[i].type == "ai":
            last_ai_idx = i
            break
            
    # AI 메시지 이후의 도구 메시지들을 처리
    tool_messages = messages[last_ai_idx + 1:]
    for msg in tool_messages:
        if msg.type != "tool":
            continue
            
        content = msg.content
        # 도구 실행 에러 감지 (일부 실패는 허용할 수 있으므로 에러 메시지만 기록하고 중단하지 않음)
        if '"error":' in content or "실패했습니다" in content or "오류" in content:
            print(f"  [Warning] 도구 호출 중 일부 오류 발생: {content[:50]}...")
            continue

        # 1. article_parser_tool 결과 처리
        if '"content":' in content:
            try:
                data = json.loads(content)
                new_article = {
                    "title": data.get("title", "제목 없음"),
                    "content": data.get("content", ""),
                    "url": data.get("url", "")
                }
                if not any(a['url'] == new_article['url'] for a in new_updates["article_list"]):
                    new_updates["article_list"].append(new_article)
                    # 하위 호환성용 필드 업데이트
                    new_updates["article_body"] = new_article["content"]
                    new_updates["article_title"] = new_article["title"]
                    new_updates["current_article_url"] = new_article["url"]
            except: pass
            
        # 2. web_search_tool 결과 처리
        elif content.startswith("["):
            try:
                search_data = json.loads(content)
                new_updates["search_results"] = search_data
            except: pass

        # 3. analysis_reporter_tool 결과 처리
        elif ".md" in content:
            new_updates["report_path"] = content
            new_updates["analysis_result"] = {"status": "completed"}
                
    return new_updates

execute_tools = ToolNode(tools)
