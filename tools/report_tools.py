# tools/report_tools.py
from langchain_core.tools import tool
import os
from datetime import datetime

@tool
def analysis_reporter_tool(title: str, url: str, report_body: str) -> str:
    """
    기사 분석 완료 리포트(Markdown)를 생성하여 저장합니다.
    - title: 기사 제목
    - url: 원본 주소
    - report_body: 분석 요약, 엔티티, 인사이트 등을 포함한 전체 본문 (Markdown 형식 권장)
    """
    try:
        # 폴더 생성 (없을 경우)
        report_dir = "reports"
        if not os.path.exists(report_dir):
            os.makedirs(report_dir)
            
        # 파일명 생성: article_report_YYYYMMDD_HHMMSS.md
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"article_report_{timestamp}.md"
        filepath = os.path.join(report_dir, filename)
        
        # Markdown 내용 구성
        md_content = f"""# 📰 기사 분석 리포트: {title}

- **분석 일시**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **원본 URL**: {url}

{report_body}

---
*본 리포트는 Article Analyst Agent에 의해 자동으로 생성되었습니다.*
"""
        
        # 파일 저장
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md_content)
            
        print(f"  [📁 파일 저장 완료]: {filepath}")
        return filepath
        
    except Exception as e:
        print(f"  [❌ 리포트 저장 실패]: {str(e)}")
        return f"리포트 생성 중 오류 발생: {str(e)}"
