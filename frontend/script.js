// PDF.js 설정
pdfjsLib.GlobalWorkerOptions.workerSrc =
  "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";

// 전역 변수
let currentUser = null;
let currentPDF = null;
let currentPage = 1;
let totalPages = 0;
let pdfScale = 1.2;
let pdfDoc = null;
let progressWebSocket = null; // 진행 상황 WebSocket 연결

// API 베이스 URL (config.js에서 설정됨, 없으면 빈 문자열)
const API_BASE = window.API_BASE || "";

// 초기화
document.addEventListener("DOMContentLoaded", () => {
  // 엔터키로 로그인
  document
    .getElementById("nickname-input")
    ?.addEventListener("keypress", (e) => {
      if (e.key === "Enter") handleLogin();
    });

  // 리더보드 자동 갱신 (10초마다)
  setInterval(loadLeaderboard, 10000);
});

// 로그인 처리
async function handleLogin() {
  const nicknameInput = document.getElementById("nickname-input");
  const nickname = nicknameInput.value.trim();

  if (!nickname) {
    alert("닉네임을 입력해주세요.");
    return;
  }

  try {
    const response = await fetch(`${API_BASE}/api/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ nickname }),
    });

    const data = await response.json();

    if (data.success) {
      currentUser = nickname;
      document.getElementById("current-user").textContent = nickname;

      // WebSocket 연결
      connectWebSocket(nickname);

      // 화면 전환
      document.getElementById("login-screen").classList.remove("active");
      document.getElementById("main-screen").classList.add("active");

      // 초기 데이터 로드
      await loadPDFList();
      await loadLeaderboard();
    } else {
      alert(data.message || "로그인에 실패했습니다.");
    }
  } catch (error) {
    console.error("로그인 오류:", error);
    alert("로그인 중 오류가 발생했습니다.");
  }
}

// WebSocket 연결 함수
function connectWebSocket(nickname) {
  // 기존 연결이 있으면 종료
  if (progressWebSocket) {
    progressWebSocket.close();
    progressWebSocket = null;
  }

  // WebSocket URL 설정 (config.js에서 설정됨)
  const backendWsBase =
    window.BACKEND_WS_URL ||
    (window.location.protocol === "https:" ? "wss:" : "ws:") +
      "//" +
      window.location.host;

  // URL 인코딩 사용 (한글 지원)
  const encodedNickname = encodeURIComponent(nickname);
  const wsUrl = `${backendWsBase}/api/ws/${encodedNickname}`;

  console.log("WebSocket 연결 시도:", wsUrl);

  progressWebSocket = new WebSocket(wsUrl);

  progressWebSocket.onopen = () => {
    console.log("WebSocket 연결됨:", nickname);
    // 연결 확인 메시지
    if (progressWebSocket && progressWebSocket.readyState === WebSocket.OPEN) {
      progressWebSocket.send("ping");
    }
  };

  progressWebSocket.onmessage = (event) => {
    try {
      // ping/pong 응답은 무시
      if (event.data === "pong") {
        return;
      }

      const data = JSON.parse(event.data);

      // 연결 확인 메시지
      if (data.type === "connected") {
        console.log("✅ WebSocket 연결 확인:", data.message);
        return;
      }

      handleProgressUpdate(data);
    } catch (e) {
      console.error("WebSocket 메시지 파싱 오류:", e, event.data);
    }
  };

  progressWebSocket.onerror = (error) => {
    console.error("WebSocket 오류:", error);
    console.error("WebSocket URL:", wsUrl);
    console.error("WebSocket 상태:", progressWebSocket?.readyState);
    // 에러 시 즉시 재연결 시도하지 않음 (onclose에서 처리)
  };

  progressWebSocket.onclose = (event) => {
    console.log("WebSocket 연결 종료", event.code, event.reason);
    progressWebSocket = null;

    // 정상 종료가 아닌 경우 재연결 시도 (1000 = 정상 종료)
    // 1006 = 비정상 종료, 1001 = 서버 종료 등
    if (event.code !== 1000 && currentUser) {
      console.log(
        `WebSocket 비정상 종료 (코드: ${event.code}), 2초 후 재연결 시도...`
      );
      setTimeout(() => {
        if (
          currentUser &&
          (!progressWebSocket ||
            progressWebSocket.readyState === WebSocket.CLOSED)
        ) {
          connectWebSocket(currentUser);
        }
      }, 2000);
    }
  };
}

// 진행 상황 업데이트 핸들러
function handleProgressUpdate(data) {
  const progressContainer = document.getElementById("progress-container");
  const progressFill = document.getElementById("progress-fill");
  const progressText = document.getElementById("progress-text");
  const submitBtn = document.getElementById("submit-button");

  if (data.type === "progress") {
    // 진행바 표시
    progressContainer.style.display = "block";
    submitBtn.disabled = true;
    submitBtn.textContent = "처리 중...";

    // 진행률 업데이트
    progressFill.style.width = `${data.progress}%`;
    progressText.textContent = data.message;

    // 단계별 색상 업데이트 (선택사항)
    progressFill.setAttribute("data-stage", data.stage);

    console.log(`진행률: ${data.progress}% - ${data.message}`);
  } else if (data.type === "complete") {
    // 완료 처리
    progressFill.style.width = "100%";
    progressText.textContent = "✅ 완료!";

    setTimeout(() => {
      progressContainer.style.display = "none";

      // 결과 표시
      const resultMessage = document.getElementById("result-message");
      const resultContainer = document.getElementById("result-container");

      resultMessage.className = "result-message success";
      let htmlContent = `
        <h4>✅ 평가 완료!</h4>
        <p><strong>점수:</strong> ${data.score}점</p>
        <p><strong>처리된 문장:</strong> ${data.total_processed}개</p>
      `;

      // 평가 상세 정보가 있으면 추가
      if (data.total_tp !== undefined) {
        htmlContent += `
          <hr style="margin: 1rem 0; border: none; border-top: 1px solid #ddd;">
          <div class="eval-details">
            <p><strong>평가 상세:</strong></p>
            <p>✅ TP (올바른 교정): ${data.total_tp}</p>
            <p>❌ FP (잘못된 교정): ${data.total_fp}</p>
            <p>⚠️ FM (놓친 교정): ${data.total_fm}</p>
          </div>
        `;
      }

      resultMessage.innerHTML = htmlContent;
      resultContainer.style.display = "block";

      // 리더보드 갱신
      loadLeaderboard();

      // 버튼 상태 복원
      submitBtn.disabled = false;
      submitBtn.textContent = "제출하기";
    }, 500);
  } else if (data.type === "error") {
    // 오류 처리
    progressContainer.style.display = "none";

    const resultMessage = document.getElementById("result-message");
    const resultContainer = document.getElementById("result-container");

    resultMessage.className = "result-message error";
    resultMessage.innerHTML = `
      <h4>❌ 오류 발생</h4>
      <p>${data.message}</p>
    `;
    resultContainer.style.display = "block";

    // 버튼 상태 복원
    submitBtn.disabled = false;
    submitBtn.textContent = "제출하기";
  }
}

// 로그아웃 처리
function handleLogout() {
  if (confirm("로그아웃하시겠습니까?")) {
    // WebSocket 연결 종료
    if (progressWebSocket) {
      progressWebSocket.close();
      progressWebSocket = null;
    }

    currentUser = null;
    document.getElementById("nickname-input").value = "";
    document.getElementById("prompt-input").value = "";

    // 화면 전환
    document.getElementById("main-screen").classList.remove("active");
    document.getElementById("login-screen").classList.add("active");
  }
}

// PDF 목록 로드
async function loadPDFList() {
  try {
    const response = await fetch(`${API_BASE}/api/pdfs`);
    const data = await response.json();

    const selector = document.getElementById("pdf-selector");
    selector.innerHTML = '<option value="">PDF 선택...</option>';

    data.pdfs.forEach((pdf) => {
      const option = document.createElement("option");
      option.value = pdf;
      option.textContent = pdf
        .replace(".pdf", "")
        .replace(/^vertopal\.com_|^chapter-|^hapter-/g, "");
      selector.appendChild(option);
    });
  } catch (error) {
    console.error("PDF 목록 로드 오류:", error);
  }
}

// 선택된 PDF 로드
async function loadSelectedPDF() {
  const selector = document.getElementById("pdf-selector");
  const pdfFile = selector.value;

  if (!pdfFile) return;

  const loadingDiv = document.getElementById("pdf-loading");
  loadingDiv.textContent = "PDF 로딩 중...";
  loadingDiv.style.display = "flex";

  try {
    const url = `${API_BASE}/api/pdfs/${encodeURIComponent(pdfFile)}`;
    const loadingTask = pdfjsLib.getDocument(url);
    pdfDoc = await loadingTask.promise;

    totalPages = pdfDoc.numPages;
    currentPage = 1;

    await renderPage(currentPage);

    loadingDiv.style.display = "none";
    updatePageInfo();
  } catch (error) {
    console.error("PDF 로드 오류:", error);
    loadingDiv.textContent = "PDF 로드 실패";
  }
}

// PDF 페이지 렌더링
async function renderPage(pageNum) {
  if (!pdfDoc) return;

  try {
    const page = await pdfDoc.getPage(pageNum);
    const canvas = document.getElementById("pdf-canvas");
    const context = canvas.getContext("2d");

    const viewport = page.getViewport({ scale: pdfScale });

    canvas.height = viewport.height;
    canvas.width = viewport.width;

    const renderContext = {
      canvasContext: context,
      viewport: viewport,
    };

    await page.render(renderContext).promise;
  } catch (error) {
    console.error("페이지 렌더링 오류:", error);
  }
}

// 페이지 정보 업데이트
function updatePageInfo() {
  document.getElementById(
    "page-info"
  ).textContent = `${currentPage} / ${totalPages}`;

  document.getElementById("prev-page").disabled = currentPage <= 1;
  document.getElementById("next-page").disabled = currentPage >= totalPages;
}

// PDF 네비게이션
async function previousPage() {
  if (currentPage > 1) {
    currentPage--;
    await renderPage(currentPage);
    updatePageInfo();
  }
}

async function nextPage() {
  if (currentPage < totalPages) {
    currentPage++;
    await renderPage(currentPage);
    updatePageInfo();
  }
}

async function zoomIn() {
  pdfScale += 0.2;
  await renderPage(currentPage);
}

async function zoomOut() {
  if (pdfScale > 0.4) {
    pdfScale -= 0.2;
    await renderPage(currentPage);
  }
}

// 프롬프트 제출
async function handleSubmit() {
  const promptInput = document.getElementById("prompt-input");
  const prompt = promptInput.value.trim();

  if (!prompt) {
    alert("프롬프트를 입력해주세요.");
    return;
  }

  if (!currentUser) {
    alert("로그인이 필요합니다.");
    return;
  }

  // WebSocket 연결 확인 및 재연결 시도
  if (!progressWebSocket || progressWebSocket.readyState !== WebSocket.OPEN) {
    console.warn("WebSocket 연결이 없습니다. 재연결 시도...");
    connectWebSocket(currentUser);

    // 재연결 대기 (최대 2초)
    let reconnectAttempts = 0;
    while (
      (!progressWebSocket || progressWebSocket.readyState !== WebSocket.OPEN) &&
      reconnectAttempts < 20
    ) {
      await new Promise((resolve) => setTimeout(resolve, 100));
      reconnectAttempts++;
    }

    if (!progressWebSocket || progressWebSocket.readyState !== WebSocket.OPEN) {
      alert(
        "WebSocket 연결에 실패했습니다. 페이지를 새로고침하고 다시 시도해주세요."
      );
      return;
    }
  }

  // UI 초기화
  const submitBtn = document.getElementById("submit-button");
  const progressContainer = document.getElementById("progress-container");
  const resultContainer = document.getElementById("result-container");
  const progressFill = document.getElementById("progress-fill");
  const progressText = document.getElementById("progress-text");

  submitBtn.disabled = true;
  submitBtn.textContent = "처리 중...";
  progressContainer.style.display = "block";
  resultContainer.style.display = "none";

  // 초기 진행 상태 표시
  progressFill.style.width = "0%";
  progressText.textContent = "시작 중...";

  try {
    // API 호출 (백그라운드 작업 시작)
    const response = await fetch(`${API_BASE}/api/submit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        nickname: currentUser,
        prompt: prompt,
      }),
    });

    const data = await response.json();

    if (!data.success) {
      throw new Error(data.message || "제출에 실패했습니다.");
    }

    // WebSocket을 통해 진행 상황을 실시간으로 받음
    // handleProgressUpdate가 자동으로 호출됨
  } catch (error) {
    console.error("제출 오류:", error);

    progressContainer.style.display = "none";

    const resultMessage = document.getElementById("result-message");
    resultMessage.className = "result-message error";
    resultMessage.innerHTML = `
      <h4>❌ 오류 발생</h4>
      <p>${error.message}</p>
    `;
    resultContainer.style.display = "block";

    submitBtn.disabled = false;
    submitBtn.textContent = "제출하기";
  }
}

// 리더보드 로드
async function loadLeaderboard() {
  try {
    const response = await fetch(`${API_BASE}/api/leaderboard`);
    const data = await response.json();

    const tbody = document.getElementById("leaderboard-body");

    if (data.leaderboard.length === 0) {
      tbody.innerHTML =
        '<tr><td colspan="4" class="no-data">데이터가 없습니다</td></tr>';
      return;
    }

    tbody.innerHTML = data.leaderboard
      .map((entry, index) => {
        const rank = index + 1;
        const medal =
          rank === 1 ? "🥇" : rank === 2 ? "🥈" : rank === 3 ? "🥉" : rank;
        const isCurrentUser = entry.nickname === currentUser;

        return `
                <tr class="${isCurrentUser ? "current-user" : ""}">
                    <td>${medal}</td>
                    <td>${entry.nickname}</td>
                    <td><strong>${entry.score.toFixed(2)}</strong></td>
                    <td>${entry.submission_count}</td>
                </tr>
            `;
      })
      .join("");
  } catch (error) {
    console.error("리더보드 로드 오류:", error);
  }
}

// 히스토리 모달 열기
async function showHistory() {
  if (!currentUser) {
    alert("로그인이 필요합니다.");
    return;
  }

  const modal = document.getElementById("history-modal");
  modal.style.display = "block";

  // 히스토리 로드
  await loadHistory();
}

// 히스토리 모달 닫기
function closeHistory() {
  const modal = document.getElementById("history-modal");
  modal.style.display = "none";
}

// 모달 외부 클릭 시 닫기
window.onclick = function (event) {
  const modal = document.getElementById("history-modal");
  if (event.target === modal) {
    closeHistory();
  }
};

// 히스토리 로드
async function loadHistory() {
  if (!currentUser) return;

  const historyList = document.getElementById("history-list");
  const historyStats = document.getElementById("history-stats");

  historyList.innerHTML = '<p class="no-data">히스토리를 불러오는 중...</p>';

  try {
    const response = await fetch(
      `${API_BASE}/api/history/${encodeURIComponent(currentUser)}`
    );
    const data = await response.json();

    if (data.history.length === 0) {
      historyList.innerHTML =
        '<p class="no-data">아직 제출한 프롬프트가 없습니다.</p>';
      historyStats.innerHTML = "";
      return;
    }

    // 통계 정보 표시
    const bestScore = Math.max(...data.history.map((h) => h.score));
    const avgScore = (
      data.history.reduce((sum, h) => sum + h.score, 0) / data.history.length
    ).toFixed(2);

    historyStats.innerHTML = `
            <div class="stats-item">
                <span class="stats-label">총 제출 횟수:</span>
                <span class="stats-value">${data.total_submissions}회</span>
            </div>
            <div class="stats-item">
                <span class="stats-label">최고 점수:</span>
                <span class="stats-value best-score">${bestScore.toFixed(
                  2
                )}점</span>
            </div>
            <div class="stats-item">
                <span class="stats-label">평균 점수:</span>
                <span class="stats-value">${avgScore}점</span>
            </div>
        `;

    // 히스토리 목록 표시
    historyList.innerHTML = data.history
      .map((entry, index) => {
        const date = new Date(entry.timestamp);
        const formattedDate = date.toLocaleString("ko-KR", {
          year: "numeric",
          month: "2-digit",
          day: "2-digit",
          hour: "2-digit",
          minute: "2-digit",
        });

        const isBestScore = entry.score === bestScore;

        return `
                <div class="history-item ${
                  isBestScore ? "best-score-item" : ""
                }">
                    <div class="history-header">
                        <span class="history-number">#${
                          entry.submission_number
                        }</span>
                        <span class="history-score ${
                          isBestScore ? "best" : ""
                        }">${entry.score.toFixed(2)}점 ${
          isBestScore ? "🏆" : ""
        }</span>
                    </div>
                    <div class="history-date">${formattedDate}</div>
                    <div class="history-prompt">${escapeHtml(
                      entry.prompt
                    )}</div>
                    <div class="history-actions">
                        <button onclick="reusePrompt(${index})" class="reuse-btn">다시 사용</button>
                    </div>
                </div>
            `;
      })
      .join("");
  } catch (error) {
    console.error("히스토리 로드 오류:", error);
    historyList.innerHTML =
      '<p class="no-data error">히스토리를 불러오는데 실패했습니다.</p>';
  }
}

// 프롬프트 재사용
async function reusePrompt(index) {
  if (!currentUser) return;

  try {
    const response = await fetch(
      `${API_BASE}/api/history/${encodeURIComponent(currentUser)}`
    );
    const data = await response.json();

    if (data.history[index]) {
      document.getElementById("prompt-input").value =
        data.history[index].prompt;
      closeHistory();
      alert("프롬프트가 입력창에 복사되었습니다.");
    }
  } catch (error) {
    console.error("프롬프트 재사용 오류:", error);
  }
}

// HTML 이스케이프
function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}
