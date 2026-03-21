<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>GraphTools API Tester</title>
  <script defer src="./api_tester.js"></script>
  <style>
    :root {
      --bg: #f2f4f7;
      --panel: #ffffff;
      --line: #d8dee7;
      --text: #243447;
      --muted: #667788;
      --ok: #146c43;
      --ng: #b42318;
      --accent: #0b66c3;
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      font-family: "Noto Sans JP", sans-serif;
      color: var(--text);
      background: radial-gradient(circle at right top, #e5eef8, var(--bg) 48%);
      min-height: 100vh;
      padding: 20px;
    }

    .wrap {
      max-width: 1080px;
      margin: 0 auto;
      display: grid;
      gap: 14px;
    }

    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 14px;
    }

    h1 {
      margin: 0;
      font-size: 22px;
    }

    .sub {
      margin-top: 6px;
      color: var(--muted);
      font-size: 13px;
    }

    .row {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
    }

    input[type="text"] {
      width: 100%;
      max-width: 460px;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 8px 10px;
      font-size: 14px;
    }

    button {
      border: 1px solid #98bde7;
      background: #edf5ff;
      color: #134273;
      border-radius: 8px;
      padding: 8px 12px;
      font-size: 13px;
      cursor: pointer;
    }

    button.primary {
      border-color: #2d7dd2;
      background: #0b66c3;
      color: #fff;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }

    th, td {
      border: 1px solid var(--line);
      padding: 8px;
    }

    .ok { color: var(--ok); font-weight: 700; }
    .ng { color: var(--ng); font-weight: 700; }

    #log {
      width: 100%;
      height: 260px;
      background: #101720;
      color: #90f2a4;
      border: 1px solid #2c3642;
      border-radius: 8px;
      padding: 10px;
      overflow: auto;
      white-space: pre-wrap;
      font-family: monospace;
      font-size: 12px;
    }
  </style>
</head>

<body>
  <div class="wrap">
    <div class="panel">
      <h1>GraphTools API簡易テスター</h1>
      <div class="sub">指定4テストをブラウザで実行し、結果とログを確認できます。</div>
    </div>

    <div class="panel">
      <div class="row">
        <label for="apiBase">API Base</label>
        <input id="apiBase" type="text" />
        <button id="btnDetect">自動検出</button>
        <button id="btnHealth">接続確認</button>
      </div>
      <div id="status" class="status"></div>
      <div class="row">
        <button id="btnT1">Test 1</button>
        <button id="btnT2">Test 2</button>
        <button id="btnT3">Test 3</button>
        <button id="btnT4">Test 4</button>
        <button id="btnAll" class="primary">Run All</button>
        <button id="btnClear">結果クリア</button>
      </div>
    </div>

    <div class="panel">
      <table>
        <thead>
          <tr>
            <th>Test</th>
            <th>Result</th>
            <th>Duration(ms)</th>
            <th>Detail</th>
          </tr>
        </thead>
        <tbody id="resultBody"></tbody>
      </table>
    </div>

    <div class="panel">
      <div class="row">
        <button id="btnSaveJson">ログ保存(JSON)</button>
        <button id="btnSaveTxt">ログ保存(TXT)</button>
      </div>
      <pre id="log"></pre>
    </div>
  </div>
</body>
</html>
