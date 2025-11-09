from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from contextlib import asynccontextmanager
from urllib.parse import unquote
import os
import sys
import pandas as pd
from pathlib import Path
import asyncio
from typing import Dict, Set
import json
import time

from models import (
    LoginRequest, LoginResponse, SubmitRequest, SubmitResponse,
    LeaderboardResponse, LeaderboardManager, ProgressUpdate,
    PromptHistoryResponse, PromptHistoryManager
)
from solar_api import SolarAPIClient
from evaluator import Evaluator

# Supabase Manager (선택적)
try:
    from supabase_config import init_supabase, is_supabase_available
    from supabase_manager import SupabaseLeaderboardManager, SupabasePromptHistoryManager
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("⚠️ Supabase 관련 패키지가 없습니다. 로컬 JSON 파일을 사용합니다.")

# 경로 설정
BASE_DIR = Path(__file__).parent.parent

# 데이터 디렉터리: 여러 경로 확인 (Railway 환경 고려)
# Railway에서는 작업 디렉토리가 /app이고, backend 폴더에서 실행됨
DATA_DIR_CANDIDATES = [
    BASE_DIR / "data",                      # repo_root/data (Railway에서 일반적)
    Path(__file__).parent / "data",         # backend/data
    Path("/app/data"),                      # Railway 절대 경로
    Path("/app/backend/data"),              # Railway backend 절대 경로
]

DATA_DIR = None
for _cand in DATA_DIR_CANDIDATES:
    if _cand.exists() and _cand.is_dir():
        DATA_DIR = _cand
        print(f"✅ DATA_DIR 발견: {DATA_DIR} (절대 경로: {DATA_DIR.resolve()})")
        break
    else:
        print(f"⚠️ DATA_DIR 후보 확인: {_cand} (존재: {_cand.exists()})")

if DATA_DIR is None:
    # 기본값 설정 (로컬 개발 환경)
    DATA_DIR = BASE_DIR / "data"
    print(f"⚠️ DATA_DIR을 찾을 수 없어 기본값 사용: {DATA_DIR}")
    print(f"   현재 작업 디렉토리: {Path.cwd()}")
    print(f"   __file__ 위치: {Path(__file__).resolve()}")
    print(f"   BASE_DIR: {BASE_DIR.resolve()}")

FRONTEND_DIR = BASE_DIR / "frontend"
PDF_DIR = BASE_DIR / "Solar_prompt_cookbook"

# 전역 변수
leaderboard_manager = None
history_manager = None
evaluator = None
solar_client = None
active_sessions: Set[str] = set()
active_connections: Dict[str, WebSocket] = {}
active_websockets: Dict[str, WebSocket] = {}  # 진행 상황 전송용 WebSocket 연결

@asynccontextmanager
async def lifespan(app: FastAPI):
    """서버 시작/종료 시 초기화"""
    global evaluator, solar_client, leaderboard_manager, history_manager
    
    # Supabase 초기화 시도
    use_supabase = os.getenv("USE_SUPABASE", "false").lower() == "true"
    if use_supabase and SUPABASE_AVAILABLE:
        try:
            init_supabase()
            if is_supabase_available():
                leaderboard_manager = SupabaseLeaderboardManager()
                history_manager = SupabasePromptHistoryManager()
                print("✅ Supabase를 사용합니다.")
            else:
                raise Exception("Supabase 초기화 실패")
        except Exception as e:
            print(f"⚠️ Supabase 초기화 실패, 로컬 JSON 파일을 사용합니다: {e}")
            leaderboard_manager = LeaderboardManager(filepath=str(BASE_DIR / "leaderboard.json"))
            history_manager = PromptHistoryManager(filepath=str(BASE_DIR / "prompt_history.json"))
    else:
        # 로컬 JSON 파일 사용
        leaderboard_manager = LeaderboardManager(filepath=str(BASE_DIR / "leaderboard.json"))
        history_manager = PromptHistoryManager(filepath=str(BASE_DIR / "prompt_history.json"))
        print("📁 로컬 JSON 파일을 사용합니다.")
    
    try:
        # Evaluator 초기화
        test_csv_path = DATA_DIR / "test_from_train.csv"
        answer_csv_path = DATA_DIR / "answer_from_train.csv"
        
        if not test_csv_path.exists():
            print(f"❌ 경고: test_from_train.csv를 찾을 수 없습니다: {test_csv_path}")
            print(f"   현재 DATA_DIR: {DATA_DIR}")
            print(f"   DATA_DIR 존재 여부: {DATA_DIR.exists()}")
        elif not answer_csv_path.exists():
            print(f"❌ 경고: answer_from_train.csv를 찾을 수 없습니다: {answer_csv_path}")
            print(f"   현재 DATA_DIR: {DATA_DIR}")
            print(f"   DATA_DIR 존재 여부: {DATA_DIR.exists()}")
        else:
            try:
                evaluator = Evaluator(str(test_csv_path), str(answer_csv_path))
                print("✅ Evaluator 초기화 완료")
            except Exception as e:
                print(f"❌ Evaluator 초기화 실패: {e}")
                import traceback
                traceback.print_exc()
        
        # Solar API 클라이언트 초기화
        try:
            solar_client = SolarAPIClient()
            print("✅ Solar API 클라이언트 초기화 완료")
        except Exception as e:
            print(f"❌ Solar API 클라이언트 초기화 실패: {e}")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        print(f"❌ 초기화 중 예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc()
    
    # 초기화 상태 확인 및 로깅
    print("\n" + "="*50)
    print("초기화 상태 확인:")
    print(f"  - leaderboard_manager: {'✅' if leaderboard_manager else '❌'}")
    print(f"  - history_manager: {'✅' if history_manager else '❌'}")
    print(f"  - evaluator: {'✅' if evaluator else '❌'}")
    print(f"  - solar_client: {'✅' if solar_client else '❌'}")
    print("="*50 + "\n")
    
    yield  # 서버 실행 중
    
    # 종료 시 정리
    print("서버 종료 중...")

# FastAPI 앱 초기화
app = FastAPI(title="프롬프톤 플랫폼", lifespan=lifespan)

# CORS 설정
# Netlify URL을 환경변수에서 읽어오기
netlify_url = os.getenv("NETLIFY_URL", "")
allowed_origins = ["*"]  # 기본값: 모든 출처 허용

# Netlify URL이 설정되어 있으면 추가
if netlify_url:
    allowed_origins = [
        netlify_url,
        netlify_url.replace("https://", "http://"),  # HTTP 버전도 허용
    ]
    # 로컬 개발용
    allowed_origins.extend([
        "http://localhost:8888",
        "http://localhost:3000",
        "http://localhost:8000",
    ])
    print(f"✅ CORS 허용 출처: {allowed_origins}")
else:
    print("⚠️ NETLIFY_URL이 설정되지 않았습니다. 모든 출처를 허용합니다.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket 엔드포인트는 정적 파일 마운트 전에 정의해야 함
@app.websocket("/api/ws/{nickname}")
async def websocket_endpoint(websocket: WebSocket, nickname: str):
    """WebSocket 연결 - 진행 상황 실시간 전송"""
    # URL 디코딩 (한글 닉네임 처리)
    try:
        decoded_nickname = unquote(nickname)
    except Exception as e:
        print(f"URL 디코딩 오류: {e}, 원본: {nickname}")
        decoded_nickname = nickname
    
    try:
        print(f"WebSocket 연결 시도: {decoded_nickname} (원본: {nickname})")
        await websocket.accept()
        active_websockets[decoded_nickname] = websocket
        print(f"✅ WebSocket 연결 성공: {decoded_nickname}")
        
        # 연결 확인 메시지 전송
        await websocket.send_json({
            "type": "connected",
            "message": "WebSocket 연결이 성공했습니다."
        })
        
        # 연결 유지 (클라이언트가 닫을 때까지 대기)
        while True:
            try:
                data = await websocket.receive_text()
                # ping/pong 처리 (선택사항)
                if data == "ping":
                    await websocket.send_text("pong")
            except WebSocketDisconnect:
                break
    except Exception as e:
        print(f"❌ WebSocket 처리 중 오류 ({decoded_nickname}): {e}")
        import traceback
        traceback.print_exc()
        try:
            await websocket.close()
        except:
            pass
    finally:
        print(f"WebSocket 연결 종료: {decoded_nickname}")
        active_websockets.pop(decoded_nickname, None)

# 정적 파일 서빙 (프론트엔드) - WebSocket 이후에 마운트
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

@app.get("/")
async def read_root():
    """메인 페이지"""
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "프롬프톤 플랫폼 API 서버"}

@app.post("/api/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """로그인 (닉네임 기반)"""
    nickname = request.nickname.strip()
    
    if not nickname:
        raise HTTPException(status_code=400, detail="닉네임을 입력해주세요.")
    
    if len(nickname) > 20:
        raise HTTPException(status_code=400, detail="닉네임은 20자 이하로 입력해주세요.")
    
    # 세션에 추가
    active_sessions.add(nickname)
    
    return LoginResponse(
        success=True,
        nickname=nickname,
        message=f"{nickname}님, 환영합니다!"
    )

@app.post("/api/submit", response_model=SubmitResponse)
async def submit_prompt(request: SubmitRequest):
    """프롬프트 제출 및 평가 (비동기 백그라운드 작업)"""
    global evaluator, solar_client, leaderboard_manager, history_manager
    
    try:
        print(f"📥 제출 요청 수신: nickname={request.nickname}, prompt_length={len(request.prompt) if request.prompt else 0}")
        
        # 초기화 상태 확인
        if not solar_client:
            print("❌ Solar API 클라이언트가 초기화되지 않았습니다.")
            raise HTTPException(status_code=500, detail="Solar API 클라이언트가 초기화되지 않았습니다.")
        
        if not evaluator:
            print("❌ 평가 시스템이 초기화되지 않았습니다.")
            raise HTTPException(status_code=500, detail="평가 시스템이 초기화되지 않았습니다.")
        
        if not leaderboard_manager:
            print("❌ 리더보드 관리자가 초기화되지 않았습니다.")
            raise HTTPException(status_code=500, detail="리더보드 관리자가 초기화되지 않았습니다.")
        
        if not history_manager:
            print("❌ 히스토리 관리자가 초기화되지 않았습니다.")
            raise HTTPException(status_code=500, detail="히스토리 관리자가 초기화되지 않았습니다.")
        
        nickname = request.nickname.strip()
        prompt = request.prompt.strip()
        
        if not nickname:
            raise HTTPException(status_code=400, detail="닉네임을 입력해주세요.")
        
        if not prompt:
            raise HTTPException(status_code=400, detail="프롬프트를 입력해주세요.")
        
        print(f"✅ 제출 요청 검증 완료: {nickname}")
        
        # 비동기 작업을 백그라운드에서 실행
        task = asyncio.create_task(
            process_submission(
                nickname,
                prompt,
                evaluator,
                solar_client,
                leaderboard_manager,
                history_manager
            )
        )
        print(f"✅ 백그라운드 작업 시작: {nickname} (task={task})")
        
        # 즉시 응답 반환 (작업은 백그라운드에서 진행)
        return SubmitResponse(
            success=True,
            message="처리를 시작했습니다. 진행 상황은 실시간으로 업데이트됩니다.",
            score=0.0,
            total_processed=0
        )
    except HTTPException as he:
        # HTTPException은 그대로 전달
        print(f"❌ HTTPException 발생: {he.status_code} - {he.detail}")
        raise
    except Exception as e:
        # 예상치 못한 오류 로깅
        print(f"❌ 제출 요청 처리 중 예상치 못한 오류: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"서버 오류가 발생했습니다: {str(e)}")

@app.get("/api/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard():
    """리더보드 조회"""
    if not leaderboard_manager:
        raise HTTPException(status_code=500, detail="리더보드 관리자가 초기화되지 않았습니다.")
    leaderboard = leaderboard_manager.get_leaderboard()
    return LeaderboardResponse(leaderboard=leaderboard)

@app.get("/api/history/{nickname}", response_model=PromptHistoryResponse)
async def get_prompt_history(nickname: str):
    """사용자의 프롬프트 히스토리 조회"""
    if not history_manager:
        raise HTTPException(status_code=500, detail="히스토리 관리자가 초기화되지 않았습니다.")
    history = history_manager.get_history(nickname)
    return PromptHistoryResponse(
        history=history,
        total_submissions=len(history)
    )

@app.get("/api/pdfs")
async def get_pdf_list():
    """PDF 파일 목록 반환"""
    if not PDF_DIR.exists():
        return {"pdfs": []}
    
    pdf_files = sorted([
        f.name for f in PDF_DIR.iterdir() 
        if f.suffix.lower() == '.pdf'
    ])
    
    return {"pdfs": pdf_files}

@app.get("/api/pdfs/{filename}")
async def get_pdf(filename: str):
    """PDF 파일 서빙"""
    pdf_path = PDF_DIR / filename
    
    if not pdf_path.exists() or not pdf_path.is_file():
        raise HTTPException(status_code=404, detail="PDF 파일을 찾을 수 없습니다.")
    
    return FileResponse(
        str(pdf_path),
        media_type="application/pdf",
        filename=filename
    )

@app.get("/api/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "evaluator_ready": evaluator is not None,
        "solar_client_ready": solar_client is not None
    }

async def send_progress(nickname: str, stage: str, progress: int, message: str):
    """특정 닉네임의 WebSocket으로 진행 상황 전송"""
    if nickname in active_websockets:
        try:
            await active_websockets[nickname].send_json({
                "type": "progress",
                "stage": stage,  # "data_prep", "ai_correction", "evaluation", "saving"
                "progress": progress,  # 0-100
                "message": message,
                "timestamp": time.time()
            })
        except Exception as e:
            print(f"WebSocket 전송 실패 ({nickname}): {e}")
            active_websockets.pop(nickname, None)  # 연결 제거

async def process_submission(
    nickname: str, 
    prompt: str, 
    evaluator: Evaluator,
    solar_client: SolarAPIClient,
    leaderboard_manager: LeaderboardManager,
    history_manager: PromptHistoryManager
):
    """실제 제출 처리 작업 (백그라운드 실행)"""
    try:
        # 1. 데이터 준비 단계
        await send_progress(nickname, "data_prep", 5, "📁 데이터 준비 중...")
        
        test_csv_path = DATA_DIR / "test_from_train.csv"
        if not test_csv_path.exists():
            raise Exception("test_from_train.csv를 찾을 수 없습니다.")
        
        await send_progress(nickname, "data_prep", 10, "📁 CSV 파일 읽는 중...")
        
        df_test = pd.read_csv(test_csv_path)
        test_ids = evaluator.get_test_ids()
        df_filtered = df_test[df_test['id'].isin(test_ids)]
        
        if len(df_filtered) == 0:
            raise Exception("평가할 데이터가 없습니다.")
        
        sentences = [
            (row['id'], row['err_sentence']) 
            for _, row in df_filtered.iterrows()
        ]
        
        await send_progress(nickname, "data_prep", 100, 
                          f"✅ 데이터 준비 완료 ({len(sentences)}개 문장)")
        
        # 2. AI 교정 단계 (진행 상황 콜백 포함)
        await send_progress(nickname, "ai_correction", 15, "🤖 AI 교정 시작...")
        
        # 진행 상황 추적을 위한 콜백 함수
        async def correction_callback(current: int, total: int, id_val: str = ""):
            progress = 15 + int((current / total) * 65)  # 15~80%
            progress = min(progress, 80)  # 최대 80%로 제한
            percentage = int((current / total) * 100)
            await send_progress(
                nickname, 
                "ai_correction", 
                progress,
                f"✨ AI 교정 진행 중... {current}/{total} ({percentage}%)"
            )
        
        corrected_results = await solar_client.correct_batch(
            prompt=prompt,
            sentences=sentences,
            callback=correction_callback
        )
        
        await send_progress(nickname, "ai_correction", 100, 
                          f"✅ AI 교정 완료! ({len(corrected_results)}개 문장)")
        
        # 3. 평가 단계
        await send_progress(nickname, "evaluation", 85, "📊 결과 평가 중...")
        
        evaluation_result = evaluator.evaluate_submission(corrected_results)
        
        if "error" in evaluation_result:
            raise Exception(evaluation_result["error"])
        
        score = evaluation_result["score"]
        
        await send_progress(nickname, "evaluation", 95, "✅ 평가 완료!")
        
        # 4. 저장 단계
        await send_progress(nickname, "saving", 96, "💾 리더보드 저장 중...")
        
        leaderboard_manager.update_score(nickname, score)
        
        await send_progress(nickname, "saving", 97, "💾 히스토리 저장 중...")
        
        history_manager.add_submission(nickname, prompt, score)
        
        await send_progress(nickname, "saving", 98, "💾 제출 파일 저장 중...")
        
        # Submission 파일 저장
        submission_dir = BASE_DIR / "submissions"
        submission_dir.mkdir(exist_ok=True)
        submission_df = pd.DataFrame(corrected_results, columns=['id', 'cor_sentence'])
        submission_path = submission_dir / f"{nickname}_submission.csv"
        submission_df.to_csv(submission_path, index=False, encoding='utf-8-sig')
        
        await send_progress(nickname, "saving", 100, "✅ 저장 완료!")
        
        # 5. 최종 결과 전송
        if nickname in active_websockets:
            result_data = {
                "type": "complete",
                "success": True,
                "score": score,
                "total_processed": len(corrected_results),
                "message": f"평가 완료! 점수: {score}점"
            }
            
            # 평가 상세 정보가 있으면 추가
            if "total_tp" in evaluation_result:
                result_data["total_tp"] = evaluation_result["total_tp"]
                result_data["total_fp"] = evaluation_result["total_fp"]
                result_data["total_fm"] = evaluation_result["total_fm"]
            
            await active_websockets[nickname].send_json(result_data)
            
    except Exception as e:
        print(f"제출 처리 중 오류 ({nickname}): {e}")
        import traceback
        traceback.print_exc()
        
        # 오류 발생 시 클라이언트에 알림
        if nickname in active_websockets:
            await active_websockets[nickname].send_json({
                "type": "error",
                "message": str(e)
            })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

