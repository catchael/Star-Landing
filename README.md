# Star Landing｜Arduino UNO Q 手勢太空飛行

Star Landing 是一款第一人稱太空飛行遊戲。用雙手操控飛船穿越隕石帶，在能源耗盡前抵達空間站。也可以用 Android 手機當體感控制器，並在電腦上看遊戲畫面。

UNO Q 負責提供網頁及管理任務進度、能源與得分。電腦瀏覽器負責 3D 渲染和手勢辨識。攝影機接在電腦上，影像在瀏覽器內處理，遊戲只把方向與按鍵事件送到 UNO Q。

## 準備設備

- **Arduino UNO Q** 和一條可以傳輸資料的 USB-C 線。
- **電腦**，已安裝 Arduino App Lab，並有能跑 WebGL 的瀏覽器。手勢版建議使用電腦上的 Chrome。
- **手勢操作**需要電腦內建或外接的攝影機。**手機體感操作**需要一支有方向感測器的 Android 手機。
- **可讓裝置互相連線的區域網路**。用 Wi‑Fi 時，讓 UNO Q、電腦和要使用的手機加入同一個網路。若是訪客網路或校園網路，請確認裝置之間可以互通。

第一次設定板子可參考 [Arduino UNO Q 使用手冊](https://docs.arduino.cc/tutorials/uno-q/user-manual/)。

## 1. 把專案放到自己的 UNO Q

先下載這個儲存庫並解壓縮，或用 Git 複製。找到含有 `app.yaml` 的專案資料夾。復刻本版需要下列檔案和目錄結構：

```text
app.yaml
python/
└── main.py
assets/
├── index.html                    # Android 控制頁和網站首頁
├── display.html                  # 3D 遊戲和攝影機手勢控制
├── gesture_recognizer.task        # 手勢辨識模型
└── vendor/
    ├── three.module.js
    ├── three.core.js
    └── package/
        ├── vision_bundle.mjs
        └── wasm/                 # 保留整個資料夾
```

1. 用 USB-C 連接 UNO Q，在 Arduino App Lab 選取自己的板子。
2. 在 **Apps** 建立一個新 App。在 **Bricks** 加入 **WebUI - HTML**（`arduino:web_ui`）。
3. 將專案的 `python/main.py` 放入 App 的 `python/`。再將上面列出的網頁、模型和整個 `vendor/` 放入 App 的 `assets/`。保留檔名、大小寫和子資料夾結構。模型與 WASM 是二進位檔，請以原檔匯入。
4. 按 **Run**，等 Python 主控台顯示 `App started`，記下 WebUI 顯示的 **Network URL**。

如果下載的專案沒有 `gesture_recognizer.task`，請先下載 [Google 的 Gesture Recognizer 模型（float16 v1）](https://storage.googleapis.com/mediapipe-models/gesture_recognizer/gesture_recognizer/float16/1/gesture_recognizer.task)，放進專案的 `assets/`，再以原檔匯入 App Lab。

如果有從 App Lab 匯出的完整 App ZIP，也可以在 **Apps → ＋ → Import or install App** 匯入。從 GitHub 按 **Download ZIP** 取得的是原始檔壓縮包，請先解壓並按照上方步驟安裝。[Arduino App Lab 匯入與匯出說明](https://docs.arduino.cc/software/app-lab/apps/manage-apps)

## 2. 用自己的 IP 開啟遊戲

以下的 `<UNO_Q_IP>` 請換成 **Network URL** 裡的板子 IP。WebUI 預設使用 `7000`。電腦瀏覽器請使用板子的網址。主控台的 `localhost` 指的是服務所在的裝置。[Arduino WebUI Brick 說明](https://github.com/arduino/app-bricks-py/blob/main/src/arduino/app_bricks/web_ui/README.md)

| 用途 | 網址 |
| --- | --- |
| 電腦遊戲畫面與手勢校正 | `http://<UNO_Q_IP>:7000/display.html` |
| Android 手機體感控制 | `http://<UNO_Q_IP>:7000/` |
| 確認遊戲服務可連線 | `http://<UNO_Q_IP>:7000/state`，應顯示 JSON |

一場遊戲選一種控制方式。用攝影機時，在電腦的遊戲頁啟動手勢。用手機時，電腦保留遊戲畫面，手機開控制頁。

### 允許攝影機或手機感測器

Chrome 將攝影機和方向感測器限制在安全來源。若區網 HTTP 網頁能開啟，但瀏覽器擋住攝影機或方向感測器，可在可信任的區網開發環境中，為這台 UNO Q 加入 Chrome 測試例外。[Chromium 安全來源說明](https://www.chromium.org/Home/chromium-security/deprecating-powerful-features-on-insecure-origins/)

1. 在要使用攝影機或感測器的裝置上，用 Chrome 開啟 `chrome://flags/#unsafely-treat-insecure-origin-as-secure`。
2. 找到 **Insecure origins treated as secure**，選 **Enabled**。
3. 填入自己的來源網址 `http://<UNO_Q_IP>:7000`，只填到連接埠。
4. 按 **Relaunch**，重新開遊戲或控制頁。瀏覽器詢問權限時選 **允許**。

如果瀏覽器沒有這個選項、裝置政策禁止使用，或需要長期部署，請使用有受信任憑證的 HTTPS 網址。

## 3. 用攝影機手勢遊玩

1. 在電腦開啟 `/display.html`，按右側螢幕的 **啟動攝影機並開始校正**。
2. 校正會依序進行 **持平、向右、向左、上升、下降、射擊、衝刺**。每一步準備好後比 OK，接著有 5 秒讓你換成畫面指定的姿勢。持平及四個方向各記錄約 5 秒有效姿勢。射擊和衝刺各保持約 1 秒。
3. 持平和方向校正時，拇指自然搭在拳頭外側，雙手分開並維持在鏡像預覽的各自一側。畫面會顯示動作圖示與錄製進度。
4. 校正完成後，攝影機畫面會縮回右側小螢幕。倒數 5 秒並收到 UNO Q 確認後，自動起飛。

| 操作 | 手勢 |
| --- | --- |
| 向左 | 像轉方向盤一樣，左拳降低、右拳抬高 |
| 向右 | 右拳降低、左拳抬高 |
| 上升／下降 | 兩拳一起舉高／降低，以兩拳中點的高度控制 |
| 斜向移動 | 一起升降雙拳，同時向左或向右轉動 |
| 射擊 | 翹起右手拇指 |
| 衝刺 | 翹起左手拇指 |

比讚時，其餘四指維持握拳，就能同時操控方向。拇指搭回拳頭後可以再觸發下一次射擊或衝刺。右側小螢幕會顯示手部追蹤狀態、方向力度和各手的觸發次數。

### 改用 Android 體感

電腦開 `/display.html`，Android 開 `/`。把手機放在舒適的持平位置，在手機頁按 **開始感測／校正**。校正後，左右傾斜控制橫移，前後傾斜控制升降。用手機畫面上的按鈕射擊或衝刺。若切回控制頁後顯示重新校正，先把手機放回持平位置。

## 遊戲規則

穿越隕石帶並抵達空間站時，需保留至少 **20% 能源**才能完成降落。每次衝刺消耗 **8%**，提供約 **1.2 秒**加速。每次射擊消耗 **3%**，可擊毀前方的隕石。碰撞會損失船體。能源或船體耗盡時，任務失敗。

## 換網路或 IP

換網路後，在 App Lab 等 App 啟動，重新讀取 **Network URL**。如果不確定目前的 IP，可在 **UNO Q 終端機**執行 `hostname -I`。有多個位址時，選擇電腦可連到的板子介面。若用 Wi‑Fi，優先使用 WebUI 主控台顯示的網址。

用新 IP 開啟遊戲頁。如果使用 Chrome 的 HTTP 測試例外，也要在相應裝置上更新來源網址並重啟 Chrome。換 IP 不需要修改程式或模型。

## 常見問題

| 現象 | 先檢查哪裡 |
| --- | --- |
| `ERR_CONNECTION_TIMED_OUT` | 確認用了最新 IP、電腦與板子可互通，以及所用的網路沒有隔離裝置。 |
| `ERR_CONNECTION_REFUSED` | 確認 App Lab 按鈕顯示 **Stop**、主控台有 `App started`。若 App 啟動後立刻關閉，查看 Python 主控台最後的錯誤。 |
| 網頁打得開，中心沒有 3D 場景 | 確認 `assets/vendor/` 裡的 `three.module.js` 和 `three.core.js` 在同一層。UNO Q 網址下的 `/vendor/three.core.js` 應能讀到。 |
| 能看到遊戲，攝影機無法開啟 | 檢查 Chrome 的安全來源及網站相機權限。也確認系統已允許 Chrome 使用相機。 |
| 攝影機已開，但手勢模型載入失敗 | 檢查 `assets/gesture_recognizer.task` 以及 `assets/vendor/package/wasm/`。放好後在 App Lab **Stop → Run**，再重新整理網頁。 |
| 手機顯示已連線，傾斜沒有反應 | 按 **開始感測／校正**，確認角度數字會隨手機傾斜改變。若感測器被瀏覽器封鎖，依上方安全來源步驟處理。 |
| 校正倒數停住 | 看底部提示，讓兩手完整入鏡並分開。左右校正也可用畫面上的預設靈敏度按鈕繼續。 |
| 手勢射擊或衝刺漏判 | 先讓拇指自然搭回拳頭，等小螢幕顯示「就緒」再翹起。讓拇指和拳面都看得清楚，並用右側計數確認是否觸發。 |

如果不確定是板子沒提供網頁，還是電腦沒連到板子，讓 App 持續執行，然後在 **UNO Q 終端機**試：

```bash
hostname -I
curl -i --max-time 3 http://127.0.0.1:7000/state
```

如果板子本機回傳 `200 OK`，優先查電腦到板子的網路。如果板子本機也連不上，優先查看 App Lab 的啟動紀錄。

## 使用的工具

- [Arduino App Lab WebUI](https://github.com/arduino/app-bricks-py/blob/main/src/arduino/app_bricks/web_ui/README.md) 提供網頁與遊戲 API。
- [Three.js](https://threejs.org/) 負責 3D 渲染。遊戲頁從 UNO Q 載入儲存庫內的套件。
- [MediaPipe Gesture Recognizer](https://developers.google.com/edge/mediapipe/solutions/vision/gesture_recognizer?tab=Web) 提供手部關節座標與手勢分類。瀏覽器會從 UNO Q 載入放在 `assets/` 的模型。

### 公開發佈

請保留上方的目錄結構。隨專案發佈第三方套件時，一併附上 [Three.js r180 的 MIT 授權](https://github.com/mrdoob/three.js/blob/r180/LICENSE) 和 [MediaPipe 的 Apache 2.0 授權](https://github.com/google-ai-edge/mediapipe/blob/master/LICENSE)，並保留原始的版權與授權聲明。若模型由使用者另行下載，請保留本 README 的官方下載連結與放置路徑。
