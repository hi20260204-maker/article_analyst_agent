# graphs/agents/supervisor.py
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from ..state import AgentState

load_dotenv()
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)

def classifier_node(state: AgentState) -> dict[str, str]:
    """사용자의 입력을 분석하여 의도를 분류합니다."""
    print("\n--- [Nodes] Classifier 진입 ---")
    messages = state["messages"]
    
    # 도구 응답이 마지막 메시지일 경우 무시하고 이전 사용자 입력을 탐색
    last_message = ""
    for msg in reversed(messages):
        if msg.type == "human":
            last_message = msg.content
            break
            
    if not last_message:
        last_message = state.get("user_input", "")

    prompt = f"""
    당신은 입력 분류기입니다. 사용자의 다음 입력을 분석하여 'input_type'을 선택하세요.
    입력: "{last_message}"
    
    1. url_analysis: URL이 포함된 기사 분석 요청.
    2. search_and_analyze: 키워드 뉴스 검색 요청.
    3. followup_question: 이전 분석에 대한 추가 대화 (기사 내용 질문 등).
    4. general_chat: 인사 등 일반 대화.
    
    답변은 오직 영문 타입 키워드만 출력하세요. (예: url_analysis)
    """
    
    response = llm.invoke([HumanMessage(content=prompt)])
    input_type = response.content.strip().lower()
    
    valid_types = ["url_analysis", "search_and_analyze", "followup_question", "general_chat"]
    if not any(t in input_type for t in valid_types):
        for t in valid_types:
            if t in input_type:
                input_type = t
                break
        else:
            input_type = "general_chat"
                
    print(f"  [결과] 의도 분류: {input_type}")
    # retry_count 초기화 (새로운 요청 시)
    return {"input_type": input_type, "user_input": last_message, "retry_count": 0}
