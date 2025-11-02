// 환경별 설정
// Netlify 환경변수에서 백엔드 URL을 읽어옴
(function() {
  // Netlify 환경변수 확인
  const netlifyEnv = typeof process !== 'undefined' && process.env ? process.env.NETLIFY_ENV : null;
  const backendUrl = typeof process !== 'undefined' && process.env ? process.env.BACKEND_URL : null;
  
  // 환경변수가 없으면 빈 문자열 (상대 경로 사용)
  window.API_BASE = backendUrl || '';
  window.BACKEND_WS_URL = backendUrl ? 
    backendUrl.replace(/^http/, 'ws') : 
    (window.location.protocol === 'https:' ? 'wss:' : 'ws:') + '//' + window.location.host;
})();

