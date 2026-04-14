# tools/web_tools.py
from langchain_core.tools import tool
from langchain_community.utilities.tavily_search import TavilySearchAPIWrapper
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

tavily_api_key = os.getenv("TAVILY_API_KEY")

@tool
def web_search_tool(query: str) -> list[dict[str, str]]:
    """
    특정 주제에 관한 최신 뉴스나 관련 기사를 웹에서 검색합니다.
    검색 결과 중 연관성 점수가 0.7 이상인 신뢰할 수 있는 정보만 반환합니다.
    """
    if not tavily_api_key:
        # 에러 메시지를 list[dict] 형태로 반환하여 타입 일관성 유지
        return [{"error": "TAVILY_API_KEY가 설정되지 않았습니다."}]
        
    try:
        search = TavilySearchAPIWrapper(tavily_api_key=tavily_api_key)
        
        # 검색 수행 (최대 5개 결과)
        results = search.results(query=query, max_results=5)
        
        # 필터링 임계값 설정
        THRESHOLD = 0.7
        filtered_results = [res for res in results if res.get("score", 0) >= THRESHOLD]
        
        # 결과 포맷팅 (title, url, content, score 포함)
        final_results: list[dict[str, str]] = []
        for res in filtered_results:
            final_results.append({
                "title": str(res.get("title", "N/A")),
                "url": str(res.get("url", "N/A")),
                "content": str(res.get("content", "N/A")),
                "score": str(res.get("score", 0))
            })
            
        return final_results
        
    except Exception as e:
        return [{"error": f"Tavily 검색 중 오류 발생: {str(e)}"}]
