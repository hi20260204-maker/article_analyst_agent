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
    """초기 도구 호출(추출/검색) 및 검색 결과 선택을 위한 노드입니다."""
    print("--- [Nodes] Agent(call_model) 진입 ---")
    messages = state["messages"]
    input_type = state.get("input_type", "general_chat")
    search_results = state.get("search_results", [])
    retry_count = state.get("retry_count", 0)
    
    # 무한 루프 방지 로직
    if retry_count >= 3:
        return {"error_message": "최대 재시도 횟수를 초과했습니다. URL을 확인하거나 검색어를 변경해주세요."}

    intent_guide = ""
    if input_type == "url_analysis":
        intent_guide = "사용자가 URL을 주었습니다. 'article_parser_tool'을 사용하여 본문을 추출하세요."
    elif input_type == "search_and_analyze":
        if not search_results:
            intent_guide = "사용자가 주제 검색을 요청했습니다. 'web_search_tool'을 사용하여 관련 뉴스를 찾으세요."
        else:
            intent_guide = f"""
            현재 다음 뉴스 검색 결과가 확보되었습니다:
            {json.dumps(search_results, ensure_ascii=False, indent=2)}
            
            위 검색 결과 중 사용자의 의도에 가장 부합하고 내용이 풍부한 기사 1개를 선택하세요.
            그 후, 선택한 기사의 URL을 사용하여 **반드시 'article_parser_tool'을 호출**하여 본문을 추출하세요.
            사용자에게 검색 결과 목록을 단순히 나열하지 말고, 즉시 분석 단계로 진행해야 합니다. 
            """
    
    if intent_guide:
        messages = [SystemMessage(content=intent_guide)] + messages
        
    response = llm_with_tools.invoke(messages)
    return {"messages": [response], "retry_count": retry_count + 1}

def state_sync_node(state: AgentState) -> dict:
    """도구 실행 결과를 상태 필드에 동기화합니다."""
    print("--- [Nodes] State Sync 진입 ---")
    messages = state["messages"]
    last_message = messages[-1]
    
    if last_message.type == "tool":
        content = last_message.content
        
        # 도구 실행 에러 감지
        if '"error":' in content or "실패했습니다" in content or "오류" in content:
            return {"error_message": content}

        # 1. article_parser_tool 결과 처리
        if '"content":' in content:
            try:
                data = json.loads(content)
                return {
                    "article_body": data.get("content", ""),
                    "article_title": data.get("title", "제목 없음"),
                    "current_article_url": data.get("url", ""),
                    "error_message": "" # 에러 초기화
                }
            except: pass
            
        # 2. web_search_tool 결과 처리
        if content.startswith("["):
            try:
                search_data = json.loads(content)
                return {"search_results": search_data, "error_message": ""}
            except: pass

        # 3. analysis_reporter_tool 결과 처리
        if ".md" in content:
            return {"report_path": content, "analysis_result": {"status": "completed"}}
                
    return {}

execute_tools = ToolNode(tools)
