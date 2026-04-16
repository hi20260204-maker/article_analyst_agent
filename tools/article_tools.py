# tools/article_tools.py
from langchain_core.tools import tool
import trafilatura
import requests
from typing import Optional

@tool
def article_parser_tool(url: str) -> dict[str, str]:
    """
    제공된 URL에서 기사의 본문과 제목을 추출합니다.
    한국어 인코딩 문제를 방지하기 위해 강제 인코딩 감지 로직을 포함합니다.
    """
    try:
        # 보안 및 필터링: 허용되지 않는 도메인이나 프로토콜 차단
        from urllib.parse import urlparse
        parsed_url = urlparse(url)
        if parsed_url.scheme not in ["http", "https"]:
            return {"error": "지원하지 않는 프로토콜입니다. (http, https만 가능)"}
        
        # 저품질 또는 차단된 도메인 리스트 (예시)
        blocked_domains = ["malicious.com", "example-leak.net"]
        if any(domain in parsed_url.netloc for domain in blocked_domains):
            return {"error": "신뢰할 수 없는 도메인입니다."}

        # requests를 사용하여 수동으로 다운로드 (인코딩 처리 강화를 위함)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # 인코딩 자동 감지 및 설정 (euc-kr, cp949 등 한국어 특화 처리)
        if response.encoding == 'ISO-8859-1':
            response.encoding = response.apparent_encoding
            
        try:
            html_content = response.content.decode(response.encoding or 'utf-8')
        except UnicodeDecodeError:
            # 인코딩 감지 실패 시 cp949(한국어 윈도우 표준)로 재시도
            try:
                html_content = response.content.decode('cp949')
            except UnicodeDecodeError:
                html_content = response.text # 최후의 수단
            
        # 본문 및 메타데이터 추출
        result = trafilatura.extract(html_content, output_format='txt', include_comments=False, include_tables=True)
        
        # 제목 추출
        metadata = trafilatura.extract_metadata(html_content)
        title = metadata.title if metadata else "제목 없음"
        
        if result:
            print(f"  [Parser] 추출 성공: {title[:20]}...")
            return {
                "title": title or "제목 없음",
                "content": result,
                "url": url
            }
        else:
            return {"error": "본문 내용을 추출하는 데 실패했습니다. 페이지 구조가 복잡할 수 있습니다."}
            
    except Exception as e:
        print(f"  [Parser] 에러 발생: {str(e)}")
        return {"error": f"기사 추출 중 오류 발생: {str(e)}"}
