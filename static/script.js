document.addEventListener("DOMContentLoaded", () => {
  const resultDiv = document.getElementById("result");
  const previewDiv = document.getElementById("preview");
  const startButton = document.getElementById("start-scan");
  const stopButton = document.getElementById("stop-scan");
  const cameraControls = document.getElementById("camera-controls");
  const manualInput = document.getElementById("manual-id");
  const apiUrl = document.body.dataset.apiUrl;
  const entryButton = document.getElementById("entry-button");
  const exitButton = document.getElementById("exit-button");
  const stopAfterScan = false;

  let scanner = null;
  let messageTimer = null;

  function showMessage(text, keep = false) {
    resultDiv.innerText = text;
    if (messageTimer) clearTimeout(messageTimer);
    if (!keep) {
      messageTimer = setTimeout(() => {
        resultDiv.innerText = "ユーザIDを入力してください";
      }, 10000);
    }
  }

  function handleQrCode(decodedText) {
    console.log("読み取った内容:", decodedText);
    sendQrEntry(decodedText);
  }

  if (startButton) {
    startButton.addEventListener("click", () => {
      showMessage("カメラを起動中...", true);
      previewDiv.style.display = "block";
      cameraControls.style.display = "block";
      startButton.disabled = true;

      scanner = new Html5Qrcode("preview");
      let scanned = false;

      scanner.start(
        { facingMode: "environment" },
        {
          fps: 10,
          qrbox: { width: 300, height: 300 },
          aspectRatio: 1.0
        },
        (decodedText) => {
          if (scanned) return;
          scanned = true;

          handleQrCode(decodedText); // 入退室処理を呼ぶ

          showMessage("読み取り完了！次の読み取りを待っています...", true);

          // 一定時間後に再び読み取りを許可
          setTimeout(() => {
            scanned = false;
          }, 3000); // 3秒後に再読み取り可能
        },
        (errorMessage) => {
          console.warn("読み取りエラー:", errorMessage);
        }

      ).catch(err => {
        showMessage("カメラの起動に失敗しました", false);
        console.error("カメラ起動エラー:", err);
        alert("カメラの起動に失敗しました。\n" + err.message);
        previewDiv.style.display = "none";
        cameraControls.style.display = "none";
        startButton.disabled = false;
      });
    });
  }

  if (stopButton) {
    stopButton.addEventListener("click", () => {
      if (scanner) {
        scanner.stop().then(() => {
          previewDiv.style.display = "none";
          cameraControls.style.display = "none";
          startButton.disabled = false;
          showMessage("カメラを停止しました");
          scanner.clear();
          scanner = null;
        }).catch(err => {
          console.error("カメラ停止エラー:", err);
        });
      }
    });
  }
  
  if (entryButton) {
    entryButton.addEventListener("click", () => {
      submitManual("in");
    });
  }

  if (exitButton) {
    exitButton.addEventListener("click", () => {
      submitManual("out");
    });
  }

  function sendQrEntry(userId) {
    fetch("/qr-entry", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ id: userId })
    })
    .then(response => response.json())
    .then(data => {
      if (data.message) {
        showMessage(data.message, true);  // 成功メッセージ表示
      } else if (data.error) {
        showMessage(data.error, false);   // エラーメッセージ表示
      }
    })
    .catch(error => {
      console.error("通信エラー:", error);
      showMessage("通信エラーが発生しました", false);
    });
  }
  
  function submitManual(action) {
  const input = document.getElementById("manual-id");
  const userId = input.value.trim();

    if (!userId) {
      showMessage("IDを入力してください", false);
      return;
    }

    fetch("/manual-entry", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ id: userId, action: action })
    })
    .then(response => response.json())
    .then(data => {
      if (data.message) {
        showMessage(data.message, true);
      } else if (data.error) {
        showMessage(data.error, false);
      }
    })
    .catch(error => {
      console.error("通信エラー:", error);
      showMessage("通信エラーが発生しました", false);
    });
  }

});

