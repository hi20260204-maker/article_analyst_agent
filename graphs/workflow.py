# graphs/workflow.py
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

# 노드 및 상태
from .state import AgentState
from .nodes import classifier_node, analyst_node, validator_node, state_sync_node, call_model, execute_tools

def route_based_on_type(state: AgentState) -> str:
    """input_type 및 메시지 상태에 따라 다음 노드를 결정합니다."""
    input_type = state.get("input_type")
    
    if input_type == "url_analysis":
        # 모델이 도구 호출(article_parser_tool)을 결정하도록 agent 노드로 전송
        return "agent"
    elif input_type == "search_and_analyze":
        # 모델이 도구 호출(web_search_tool)을 결정하도록 agent 노드로 전송
        return "agent"
    elif input_type == "followup_question":
        # 분석가 노드로 직접 이동하여 대화 기반 분석
        return "analyst"
    else:
        # 일반 대화
        return "agent"

def should_continue(state: AgentState) -> str:
    """도구 호출이 완료되었는지 확인하고 다음 단계를 결정합니다."""
    messages = state["messages"]
    last_message = messages[-1]
    
    # 1. 도구 호출이 더 필요한 경우 (AIMessage에 tool_calls가 있음)
    if getattr(last_message, "tool_calls", None):
        return "tools"
    
    # 2. 검색 결과가 방금 들어온 경우 -> 에이전트가 기사를 선택하도록 가이드
    if state.get("search_results") and not state.get("article_body") and not state.get("error_message"):
        return "agent"

    # 3. 본문이 확보되었고 아직 분석 전이라면 분석 노드로 이동
    if state.get("article_body") and not state.get("analysis_result") and not state.get("error_message"):
        return "analyst"
        
    return END


# 그래프 구성
workflow = StateGraph(AgentState)

# 노드 추가
workflow.add_node("classifier", classifier_node)
workflow.add_node("agent", call_model)
workflow.add_node("tools", execute_tools)
workflow.add_node("sync", state_sync_node)
workflow.add_node("validator", validator_node)
workflow.add_node("analyst", analyst_node)

# 엣지 연결
workflow.add_edge(START, "classifier")

# 조건부 라우팅: Classifier -> ?
workflow.add_conditional_edges(
    "classifier",
    route_based_on_type,
    {
        "tools": "tools",
        "agent": "agent",
        "analyst": "analyst"
    }
)

# 도구 노드 이후에는 상태 동기화 진행
workflow.add_edge("tools", "sync")

# 상태 동기화 이후 검증 또는 분석으로 진행
workflow.add_conditional_edges(
    "sync",
    should_continue,
    {
        "tools": "tools",
        "analyst": "validator", # 분석 전 검증 단계 추가
        "agent": "agent",
        "__end__": END
    }
)

# 검증 통과 여부에 따른 흐름
def check_validation(state: AgentState) -> str:
    """검증 결과에 따라 다음 노드를 결정합니다."""
    # 무한 루프 방지: 이미 에러가 있다면 다시 에이전트(Retry)로 보내지 않고 종료
    if state.get("error_message"):
        print(f"  [Workflow] 품질 검증 실패로 인한 종료: {state.get('error_message')}")
        return "end" 
    return "analyst"

workflow.add_conditional_edges(
    "validator",
    check_validation,
    {
        "analyst": "analyst",
        "end": END
    }
)

# 분석 완료 후에는 리포트 저장(tools) 또는 종료
workflow.add_edge("analyst", "tools")

# 에이전트 노드 이후의 흐름 결정 (도구 실행 또는 종료)
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",
        "analyst": "validator",
        "agent": "agent",
        "__end__": END
    }
)

# 체크포인트 설정
memory = MemorySaver()

# 컴파일
app = workflow.compile(checkpointer=memory)
