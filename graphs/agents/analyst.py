# graphs/agents/analyst.py
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from ..state import AgentState
from .collector import llm_with_tools

load_dotenv()

def analyst_node(state: AgentState) -> dict:
    """심층 분석을 수행하고 리포트 생성 도구를 호출하거나 추가 질문에 답변합니다."""
    print("--- [Nodes] Analyst 진입 ---")
    messages = state["messages"]
    article_body = state.get("article_body", "")
    article_title = state.get("article_title", "기사 분석")
    current_url = state.get("current_article_url", "")
    input_type = state.get("input_type", "followup_question")
    
    if not article_body:
        return {"error_message": "분석할 본문 데이터가 없습니다."}

    system_prompt = f"""
    당신은 '전문 기사 분석가'입니다. 제공된 본문 컨텍스트를 바탕으로 사용자와 대화하세요. 
    
    [기사 정보]
    - 제목: {article_title}
    - URL: {current_url}
    - 본문: {article_body}

    [임무]
    1. 만약 현재 요청이 기사에 대한 최초 분석({input_type} == 'url_analysis' 또는 'search_and_analyze')이라면, 
       반드시 'analysis_reporter_tool'을 호출하여 Markdown 리포트를 저장하세요.
    2. 만약 현재 요청이 기사 내용에 대한 후속 질문({input_type} == 'followup_question')이라면, 
       리포트 도구를 호출할 필요 없이 대이터 이력과 본문 내용을 바탕으로 사용자에게 친절하고 상세하게 답변하세요.
    
    [답변 가이드라인]
    - 모든 답변은 한국어로 수행하세요.
    - 논리적이고 전문적인 톤을 유지하되, 가독성을 위해 이모지와 구분선을 활용하세요.
    - 본문에 없는 내용을 지어내지 마세요.
    """
    
    print(f"  [Analyst] 처리 중 (Input Type: {input_type})...")
    
    # 전체 대화 이력을 포함하여 LLM 호출 (Context Awareness)
    response = llm_with_tools.invoke([
        SystemMessage(content=system_prompt)
    ] + messages)
    
    return {"messages": [response]}
