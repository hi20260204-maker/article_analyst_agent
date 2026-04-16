import sys
import io

# Windows 터미널 한글/이모지 인코딩 문제 해결
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from dotenv import load_dotenv
load_dotenv()

from langchain_core.messages import HumanMessage
from graphs.workflow import app
import uuid

def run_article_analyst():
    print("\n" + "="*50)
    print(" 시사/뉴스 기사 분석 에이전트 가동")
    print("="*50)
    print("사용법:")
    print("1. 기사 URL을 입력하여 분석 (예: https://news.v.daum.net/...)")
    print("2. 특정 주제를 키워드로 검색 (예: 삼성전자 반도체 전망)")
    print("3. 분석된 결과에 대해 추가 질문 (예: 주요 리스크만 요약해줘)")
    print("4. 'exit' 입력 시 종료")
    print("="*50)

    # 세션 관리를 위한 thread_id 생성
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    while True:
        try:
            user_input = input("\n[ 사용자]: ").strip()
            
            if user_input.lower() in ["exit", "quit", "종료"]:
                print("시스템을 종료합니다.")
                break
                
            if not user_input:
                continue

            inputs = {"messages": [HumanMessage(content=user_input)]}
            
            print("에이전트가 처리 중입니다... (잠시만 기다려 주세요)")
            
            # 스트리밍 실행으로 노드 진행 과정 출력
            for chunk in app.stream(inputs, config, stream_mode="updates"):
                for node_name, output in chunk.items():
                    print(f"  [ {node_name.upper()} 완료]")
                    
                    # 에러 메시지가 상태에 기록된 경우 출력
                    if "error_message" in output and output["error_message"]:
                        print(f"  [경고]: {output['error_message']}")

            # 최종 상태 확인 및 결과 출력
            final_state = app.get_state(config)
            if final_state.values:
                # 1. 분석 결과(analysis_result)가 있으면 출력
                analysis = final_state.values.get("analysis_result")
                if analysis and "error" not in analysis:
                    print("\n" + "-"*50)
                    print("[ 분석 결과]")
                    print(analysis.get("summary", "분석 결과가 없습니다."))
                    print("-"*50)
                    
                    if final_state.values.get("report_path"):
                        print(f" 리포트 저장 완료: {final_state.values.get('report_path')}")
                
                # 2. 일반 답변(messages) 출력
                else:
                    messages = final_state.values.get("messages")
                    if messages:
                        print(f"\n[ 에이전트]: {messages[-1].content}")

        except KeyboardInterrupt:
            print("\n작업이 중단되었습니다.")
            break
        except Exception as e:
            print(f"\n[ 오류 발생]: {str(e)}")

if __name__ == "__main__":
    run_article_analyst()
