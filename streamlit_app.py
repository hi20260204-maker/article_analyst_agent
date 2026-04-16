
import streamlit as st
import uuid
import os
from dotenv import load_dotenv

# 환경 변수 먼저 로드 (런타임 에러 방지)
load_dotenv()

from langchain_core.messages import HumanMessage, AIMessage
from graphs.workflow import app
import time

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
    /* 위 리포트 컨테이너 하단에 아티클 카드 디자인 추가 */
    .article-card {
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(226, 232, 240, 0.8);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.2rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    .article-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        border-color: #2563EB;
    }

    .article-title {
        color: #1E293B !important;
        font-weight: 700 !important;
        font-size: 1.25rem !important;
        text-decoration: none !important;
        margin-bottom: 0.5rem;
        display: block;
    }

    .article-source {
        display: inline-block;
        background: #E0E7FF;
        color: #4338CA !important;
        padding: 0.2rem 0.6rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-bottom: 0.8rem;
    }

    .article-snippet {
        color: #475569 !important;
        font-size: 0.95rem;
        line-height: 1.6;
    }

    /* 탭 스타일 조정 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: #F1F5F9;
        padding: 0.5rem;
        border-radius: 12px;
    }

    .stTabs [data-baseweb="tab"] {
        height: 45px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 8px;
        color: #64748B !important;
        font-weight: 600;
    }

    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF !important;
        color: #2563EB !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
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
# 신규: 탭 전환 시 데이터 보존을 위한 리스트
if "article_list" not in st.session_state:
    st.session_state.article_list = []
if "search_results" not in st.session_state:
    st.session_state.search_results = []

# 사이드바 구성
with st.sidebar:
    st.markdown("## ⚙️ 설정 & 상태")
    st.info(f"**세션 ID**: \n`{st.session_state.thread_id}`")
    
    st.markdown("---")
    st.markdown("### 🤖 모델 정보")
    st.info("**Model**: OpenAI gpt-4o-mini\n\n**Framework**: LangGraph (Multi-Agent)")
    
    st.markdown("### 🛠️ 도구 상태")
    st.success("Tavily Search: Online")
    st.success("Trafilatura Parser: Ready")
    st.success("Report Generator: Ready")
    
    if st.button("🔄 대화 초기화", use_container_width=True):
        st.session_state.messages = []
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.analysis_done = False
        st.session_state.report_path = None
        st.session_state.article_list = []
        st.session_state.search_results = []
        st.rerun()

# 메인 헤더
st.markdown('<div class="main-header"><h1>📰 Article Analyst Agent</h1><p>심층 기사 분석 및 리포트 자동 생성 시스템</p></div>', unsafe_allow_html=True)

# 메인 탭 구성
chat_tab, source_tab, report_tab = st.tabs(["💬 AI 대화", "🔍 수집된 소스", "📊 심층 리포트"])

with chat_tab:
    # 채팅 내역 표시
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

with source_tab:
    st.markdown("### 🔍 수집된 뉴스 소스")
    if not st.session_state.search_results:
        st.info("아직 수집된 소스가 없습니다. 대화를 시작해 보세요.")
    else:
        # 분석에 포함된 URL 추출
        analyzed_urls = [art.get("url") for art in st.session_state.article_list]
        
        for idx, res in enumerate(st.session_state.search_results):
            url = res.get("url", "#")
            title = res.get("title", "제목 없음")
            snippet = res.get("content", "내용 요약 없음")
            domain = url.split("//")[-1].split("/")[0]
            is_analyzed = url in analyzed_urls
            badge_html = f'<span class="article-source">{"분석 포함됨" if is_analyzed else "검색 결과"}</span>'
            
            st.markdown(f"""
            <div class="article-card">
                {badge_html}
                <a href="{url}" target="_blank" class="article-title">{title}</a>
                <div style="color: #64748B; font-size: 0.85rem; margin-bottom: 0.5rem;">출처: {domain}</div>
                <p class="article-snippet">{snippet[:300]}...</p>
            </div>
            """, unsafe_allow_html=True)

with report_tab:
    st.markdown("### 📊 심층 인사이트 리포트")
    if not st.session_state.report_path or not os.path.exists(st.session_state.report_path):
        st.info("아직 생성된 리포트가 없습니다. 분석이 완료되면 이곳에 표시됩니다.")
    else:
        with open(st.session_state.report_path, "r", encoding="utf-8") as f:
            report_content = f.read()
        
        # 상단 다운로드 섹션
        col1, col2 = st.columns([4, 1])
        with col1:
            st.success("✅ 파일이 성공적으로 생성되었습니다.")
        with col2:
            st.download_button(
                label="📥 다운로드",
                data=report_content,
                file_name=os.path.basename(st.session_state.report_path),
                mime="text/markdown",
                use_container_width=True
            )
        
        # 전문 뷰어
        st.markdown(f'<div class="report-container">{report_content}</div>', unsafe_allow_html=True)

# 사용자 입력 (탭 외부에 위치하여 상시 접근 가능)
if prompt := st.chat_input("기사 URL 또는 검색 키워드를 입력하세요..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with chat_tab:
        with st.chat_message("user"):
            st.markdown(prompt)

    # 에이전트 실행
    with chat_tab:
        with st.chat_message("assistant"):
            config = {"configurable": {"thread_id": st.session_state.thread_id}}
            inputs = {"messages": [HumanMessage(content=prompt)]}
            
            # 스트리밍 실행
            full_response = ""
            
            with st.status("🧐 에이전트가 분석을 수행하고 있습니다...", expanded=True) as status:
                for chunk in app.stream(inputs, config, stream_mode="updates"):
                    for node_name, output in chunk.items():
                        st.write(f"✅ **{node_name.upper()}** 단계 완료")
                        
                        # 에러 처리
                        if isinstance(output, dict) and "error_message" in output and output["error_message"]:
                            st.error(f"⚠️ {output['error_message']}")
                
                status.update(label="✅ 분석 완료!", state="complete", expanded=False)

            # 최종 상태 확인 및 데이터 동기화
            final_state = app.get_state(config)
            if final_state.values:
                # 1. 메시지 추출 및 세션 저장
                messages = final_state.values.get("messages")
                if messages:
                    full_response = messages[-1].content
                    st.markdown(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                
                # 2. 검색 결과 및 아티클 목록 동기화
                st.session_state.search_results = final_state.values.get("search_results", [])
                st.session_state.article_list = final_state.values.get("article_list", [])
                
                # 3. 리포트 파일 확인
                report_path = final_state.values.get("report_path")
                if report_path and os.path.exists(report_path):
                    st.session_state.report_path = report_path
                    st.session_state.analysis_done = True
                    st.rerun() # 전역 탭 업데이트를 위해 리런
