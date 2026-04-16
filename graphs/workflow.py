# graphs/workflow.py
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

# 노드 및 상태
from .state import AgentState
from .agents.supervisor import classifier_node
from .agents.collector import call_model, execute_tools, state_sync_node
from .agents.validator import validator_node
from .agents.analyst import analyst_node

def route_based_on_type(state: AgentState) -> str:
    """input_type 및 메시지 상태에 따라 다음 노드를 결정합니다."""
    input_type = state.get("input_type")
    
    if input_type in ["url_analysis", "search_and_analyze", "compare_articles", "general_chat"]:
        return "agent"
    elif input_type == "followup_question":
        return "analyst"
    return "agent"

def should_continue(state: AgentState) -> str:
    """도구 호출이 완료되었는지 확인하고 다음 단계를 결정합니다."""
    # 에러 메시지가 있으면 즉시 종료 (무한 루프 방지)
    if state.get("error_message"):
        return END

    messages = state["messages"]
    last_message = messages[-1]
    
    # 1. 도구 호출이 더 필요한 경우 (AIMessage에 tool_calls가 있음)
    if getattr(last_message, "tool_calls", None):
        return "tools"
    
    # 2. 검색 결과가 방금 들어온 경우 -> 에이전트가 기사를 선택하도록 다시 call_model
    if state.get("search_results") and not state.get("article_body"):
        return "agent"

    # 3. 본문이 확보되었고 아직 분석 전이라면 검증 기회 확보
    if state.get("article_body") and not state.get("analysis_result"):
        return "validator"
        
    return END

def check_validation(state: AgentState) -> str:
    """검증 결과에 따라 다음 노드를 결정합니다."""
    if state.get("error_message"):
        return END
    return "analyst"

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

# 1. Classifier -> Route
workflow.add_conditional_edges(
    "classifier",
    route_based_on_type,
    {
        "agent": "agent",
        "analyst": "analyst"
    }
)

# 2. Agent -> Tools or End
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",
        "validator": "validator",
        "agent": "agent",
        "__end__": END
    }
)

# 3. Tools -> Sync
workflow.add_edge("tools", "sync")

# 4. Sync -> Next Stage
workflow.add_conditional_edges(
    "sync",
    should_continue,
    {
        "tools": "tools",
        "validator": "validator",
        "agent": "agent",
        "__end__": END
    }
)

# 5. Validator -> Analyst or End
workflow.add_conditional_edges(
    "validator",
    check_validation,
    {
        "analyst": "analyst",
        "__end__": END
    }
)

# 6. Analyst -> Tools (for reporting) or End
workflow.add_conditional_edges(
    "analyst",
    should_continue,
    {
        "tools": "tools",
        "__end__": END
    }
)

# 체크포인트 설정
memory = MemorySaver()

# 컴파일
app = workflow.compile(checkpointer=memory)
