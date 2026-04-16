# graphs/agents/analyst.py
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from ..state import AgentState
from .collector import llm_with_tools

load_dotenv()

def analyst_node(state: AgentState) -> dict:
    """다중 기사를 종합 비교 및 분석하여 심층 인사이트를 도출합니다."""
    print("--- [Nodes] Analyst 진입 ---")
    messages = state["messages"]
    article_list = state.get("article_list", [])
    analysis_objective = state.get("analysis_objective", "기사 분석")
    input_type = state.get("input_type", "followup_question")
    
    if not article_list:
        # 단일 기사 호환성 체크
        article_body = state.get("article_body", "")
        if not article_body:
            return {"error_message": "분석할 본문 데이터가 없습니다."}
        article_list = [{
            "title": state.get("article_title", "제목 없음"),
            "content": article_body,
            "url": state.get("current_article_url", "")
        }]

    # 분석 대상 기사 목록 문자열 생성
    articles_context = ""
    for i, art in enumerate(article_list):
        articles_context += f"\n[기사 {i+1}]\n- 제목: {art['title']}\n- URL: {art['url']}\n- 본문: {art['content'][:2000]}...\n"

    system_prompt = f"""
    당신은 '전문 뉴스 인사이트 분석가'입니다. 
    사용자의 분석 목표: **{analysis_objective}**
    
    [제공된 기사 컨텍스트]
    {articles_context}

    [분석 가이드라인]
    1. **합의점(Consensus)**: 모든 기사에서 공통적으로 사실로 인정하거나 강조하는 지점 도출.
    2. **상충점(Divergence)**: 기사별로 관점이 다르거나 수치, 전망이 엇갈리는 부분을 예리하게 대조.
    3. **사용자 맞춤형 인사이트**: 사용자의 '분석 목표'에 가장 직결되는 핵심 시사점 도출.
    4. 분석 완료 후 최초 분석 시에는 반드시 'analysis_reporter_tool'을 호출하여 Markdown 리포트를 저장하세요.
    
    [답변 가이드라인]
    - 모든 답변은 한국어로 수행하세요.
    - 논리적이고 전문적인 톤을 유지하세요.
    - 본문에 없는 내용을 지어내지 마세요.
    """
    
    print(f"  [Analyst] 다중 기사 분석 중 (Target: {analysis_objective[:30]}...)...")
    
    # 전체 대화 이력을 포함하여 LLM 호출
    response = llm_with_tools.invoke([
        SystemMessage(content=system_prompt)
    ] + messages)
    
    return {"messages": [response]}
