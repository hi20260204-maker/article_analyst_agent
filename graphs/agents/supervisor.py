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
    당신은 입력 분류기이자 의도 파악 전문가입니다. 사용자의 입력을 분석하여 'input_type'과 구체적인 'analysis_objective'를 JSON 형식으로 반환하세요.
    입력: "{last_message}"
    
    [input_type 분류 기준]
    1. url_analysis: URL이 포함된 기사 분석 요청.
    2. search_and_analyze: 키워드 뉴스 검색 요청.
    3. followup_question: 이전 분석에 대한 추가 대화 (기사 내용 질문 등).
    4. general_chat: 인사 등 일반 대화.
    
    [analysis_objective 추출 기준]
    - 사용자가 알고 싶어하는 구체적인 '분석의 맥락'이나 '관점'을 한 문장으로 정의하세요.
    - 예: "삼성전자 실적" -> "삼성전자의 분기 실적 추이와 시장 지배력 변화 분석"
    - 예: "AI 윤리" -> "AI 기술 발전에 따른 윤리적 쟁점과 규제 현황 비교 분석"
    - 특별한 의도가 없으면 "일반적인 정보 요약 및 분석"으로 설정하세요.
    
    답변은 오직 JSON 형식으로만 출력하세요.
    형식: {{"input_type": "...", "analysis_objective": "..."}}
    """
    
    response = llm.invoke([HumanMessage(content=prompt)])
    try:
        # JSON 파싱 시도 (간혹 정규화 안 된 경우 대비)
        import json
        content = response.content.strip()
        if "```json" in content:
            content = content.split("```json")[-1].split("```")[0].strip()
        elif "{" in content:
            content = content[content.find("{"):content.rfind("}")+1]
        
        result = json.loads(content)
        input_type = result.get("input_type", "general_chat").lower()
        analysis_objective = result.get("analysis_objective", "일반적인 정보 요약 및 분석")
    except Exception as e:
        print(f"  [Error] JSON 파싱 실패: {e}")
        input_type = "general_chat"
        analysis_objective = "일반적인 정보 요약 및 분석"
    
    valid_types = ["url_analysis", "search_and_analyze", "followup_question", "general_chat"]
    if input_type not in valid_types:
        input_type = "general_chat"
                
    print(f"  [결과] 의도 분류: {input_type}")
    print(f"  [결과] 분석 목표: {analysis_objective}")
    
    return {
        "input_type": input_type, 
        "analysis_objective": analysis_objective,
        "user_input": last_message, 
        "retry_count": 0,
        "article_list": [] # 상태 초기화
    }
