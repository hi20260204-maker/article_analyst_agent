# graphs/agents/validator.py
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from ..state import AgentState

load_dotenv()
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)

def validator_node(state: AgentState) -> dict:
    """본문 품질을 검증합니다."""
    print("--- [Nodes] Validator 진입 ---")
    article_body = state.get("article_body", "")
    
    if not article_body or len(article_body) < 100:
        return {"error_message": "유효한 기사 본문을 확보하지 못했습니다."}
        
    prompt = f"다음 본문이 뉴스 기사로서 분석 가능한 수준인지 PASS/FAIL로만 답하세요.\n본문: {article_body[:300]}..."
    response = llm.invoke([HumanMessage(content=prompt)])
    
    res = response.content.upper()
    print(f"  [결과] 품질 검증: {res}")
    
    if "PASS" in res:
        return {"error_message": ""}
    else:
        return {"error_message": "추출된 텍스트의 품질이 낮아 분석이 불가능합니다."}
