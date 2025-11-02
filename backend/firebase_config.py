"""Firebase Admin SDK 초기화"""
import os
import firebase_admin
from firebase_admin import credentials, firestore
from pathlib import Path

# Firebase 초기화 여부 확인
_firebase_app = None
_db = None

def init_firebase():
    """Firebase Admin SDK 초기화"""
    global _firebase_app, _db
    
    if _firebase_app is not None:
        return _firebase_app
    
    try:
        # 방법 1: 환경변수로 Firebase 설정 JSON 사용
        firebase_config = os.getenv("FIREBASE_CONFIG_JSON")
        if firebase_config:
            import json
            cred = credentials.Certificate(json.loads(firebase_config))
            _firebase_app = firebase_admin.initialize_app(cred)
        else:
            # 방법 2: Firebase 서비스 계정 키 파일 사용
            key_file = os.getenv("FIREBASE_KEY_FILE")
            if key_file and Path(key_file).exists():
                cred = credentials.Certificate(key_file)
                _firebase_app = firebase_admin.initialize_app(cred)
            else:
                # 방법 3: 프로젝트 루트의 firebase-key.json 파일 사용
                base_dir = Path(__file__).parent.parent
                key_file = base_dir / "firebase-key.json"
                if key_file.exists():
                    cred = credentials.Certificate(str(key_file))
                    _firebase_app = firebase_admin.initialize_app(cred)
                else:
                    # 방법 4: Application Default Credentials 사용 (Google Cloud 환경)
                    try:
                        _firebase_app = firebase_admin.initialize_app()
                        print("✅ Firebase 초기화 완료 (Application Default Credentials)")
                    except Exception as e:
                        print(f"⚠️ Firebase 초기화 실패: {e}")
                        print("Firebase를 사용하려면 다음 중 하나를 설정하세요:")
                        print("  1. FIREBASE_CONFIG_JSON 환경변수 (JSON 문자열)")
                        print("  2. FIREBASE_KEY_FILE 환경변수 (파일 경로)")
                        print("  3. firebase-key.json 파일 (프로젝트 루트)")
                        print("  4. Application Default Credentials (Google Cloud 환경)")
                        raise ValueError("Firebase 설정이 없습니다.")
        
        _db = firestore.client()
        print("✅ Firebase Firestore 초기화 완료")
        return _firebase_app
    
    except Exception as e:
        print(f"❌ Firebase 초기화 오류: {e}")
        raise

def get_db():
    """Firestore 데이터베이스 인스턴스 반환"""
    global _db
    if _db is None:
        init_firebase()
    return _db

def is_firebase_available():
    """Firebase가 사용 가능한지 확인"""
    try:
        init_firebase()
        return True
    except:
        return False

