import streamlit as st
import uuid
import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage
from graphs.workflow import app
import time

# 환경 변수 로드
load_dotenv()

# 디자인 설정
st.set_page_config(
    page_title="Article Analyst Agent",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS (High-Contrast Premium Light Design)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@300;400;600;700&display=swap');
    
    /* 기본 배경 및 폰트 설정 */
    html, body, [class*="css"] {
        font-family: 'Pretendard', sans-serif;
        color: #1E293B !important;
    }
    
    .stApp {
        background-color: #F8FAFC;
    }
    
    /* 헤더 디자인 (Light Mode) */
    .main-header {
        background: #FFFFFF;
        padding: 2.5rem;
        border-radius: 15px;
        border-bottom: 5px solid #2563EB;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    }
    
    .main-header h1 {
        color: #0F172A !important;
        font-weight: 800;
        font-size: 2.8rem;
        margin-bottom: 0.5rem;
        letter-spacing: -0.05rem;
    }
    
    .main-header p {
        color: #64748B !important;
        font-size: 1.1rem;
    }
    
    /* 사이드바 가독성 강화 (Light Mode) */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #E2E8F0;
    }
    
    section[data-testid="stSidebar"] .stMarkdown p {
        color: #334155 !important;
    }
    
    /* 채팅 메시지 버블 가독성 (Light Mode) */
    .stChatMessage {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        margin-bottom: 1rem;
        border-radius: 12px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.02);
    }
    
    .stChatMessage p {
        color: #1E293B !important;
    }
    
    /* 리포트 컨테이너 (Premium Document Style) */
    .report-container {
        background-color: #FFFFFF;
        color: #1E293B !important;
        padding: 3rem;
        border-radius: 10px;
        line-height: 1.7;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        margin-top: 1.5rem;
        border: 1px solid #CBD5E1;
    }
    
    .report-container h1, .report-container h2, .report-container h3 {
        color: #0F172A !important;
        border-left: 5px solid #2563EB;
        padding-left: 1rem;
        margin-top: 2rem;
    }
    
    .report-container p, .report-container li {
        color: #334155 !important;
        font-size: 1.05rem;
    }

    /* 상태바 텍스트 가독성 */
    .stStatusWidget {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        color: #1E293B !important;
    }
</style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False
if "report_path" not in st.session_state:
    st.session_state.report_path = None

# 사이드바 구성
with st.sidebar:
    st.markdown("## ⚙️ 설정 & 상태")
    st.info(f"**세션 ID**: \n`{st.session_state.thread_id}`")
    
    st.markdown("---")
    st.markdown("### 🤖 모델 정보")
    st.code("Ollama Area\nModel: llama3.2:3b")
    
    st.markdown("### 🛠️ 도구 상태")
    st.success("Tavily Search: Online")
    st.success("Trafilatura Parser: Ready")
    
    if st.button("🔄 대화 초기화", use_container_width=True):
        st.session_state.messages = []
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.analysis_done = False
        st.session_state.report_path = None
        st.rerun()

# 메인 헤더
st.markdown('<div class="main-header"><h1>📰 Article Analyst Agent</h1><p>심층 기사 분석 및 리포트 자동 생성 시스템</p></div>', unsafe_allow_html=True)

# 채팅 내역 표시
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 사용자 입력
if prompt := st.chat_input("기사 URL 또는 검색 키워드를 입력하세요..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 에이전트 실행
    with st.chat_message("assistant"):
        config = {"configurable": {"thread_id": st.session_state.thread_id}}
        inputs = {"messages": [HumanMessage(content=prompt)]}
        
        status_placeholder = st.empty()
        
        # 스트리밍 실행
        full_response = ""
        report_found = False
        
        with st.status("🧐 에이전트가 분석을 수행하고 있습니다...", expanded=True) as status:
            for chunk in app.stream(inputs, config, stream_mode="updates"):
                for node_name, output in chunk.items():
                    st.write(f"✅ **{node_name.upper()}** 단계 완료")
                    
                    # 에러 처리
                    if "error_message" in output and output["error_message"]:
                        st.error(f"⚠️ {output['error_message']}")
            
            status.update(label="✅ 분석 완료!", state="complete", expanded=False)

        # 최종 상태 확인
        final_state = app.get_state(config)
        if final_state.values:
            # 1. 메시지 추출
            messages = final_state.values.get("messages")
            if messages:
                full_response = messages[-1].content
                st.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            
            # 2. 리포트 파일 확인
            report_path = final_state.values.get("report_path")
            if report_path and os.path.exists(report_path):
                st.session_state.report_path = report_path
                st.session_state.analysis_done = True
                
                with st.expander("📄 생성된 리포트 상세 보기", expanded=True):
                    with open(report_path, "r", encoding="utf-8") as f:
                        report_content = f.read()
                    st.markdown(f'<div class="report-container">{report_content}</div>', unsafe_allow_html=True)
                    
                    # 다운로드 버튼
                    st.download_button(
                        label="📥 리포트 다운로드 (.md)",
                        data=report_content,
                        file_name=os.path.basename(report_path),
                        mime="text/markdown",
                        use_container_width=True
                    )
