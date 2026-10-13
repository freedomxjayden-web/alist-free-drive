# AList · Render 免費私人網盤

AList v3.65.0 跑在 Render Free Web Service，檔案存 Google Drive。使用 Render 自帶的 HTTPS 網址，Mac 可以關機。已查核 Render 官方文件仍提供 Free Web Service，未綁付款方式時，超出免費配額會停用服務。帳戶若另外要求信用卡驗證，請停止，這個方案不符合免卡要求。

## 部署

將本目錄推送至自己的 GitHub 儲存庫，在 Render 建立 Web Service 並連接此儲存庫。Runtime 選 Docker，Instance Type 選 Free，Health Check Path 設為 `/api/public/settings`。不要加入付費磁碟或付費資料庫。

在 Render Environment 設定 `ALIST_ADMIN_PASSWORD`，自選至少 16 字元密碼。不要把它寫進程式、README 或 Git。啟動後使用 `admin` 登入，密碼是 Environment 設定的值。預設訪客停用。

若要公開只讀瀏覽，在 Environment 設定 `ALIST_PUBLIC_READ=true`。任何取得網址的人都能瀏覽及下載掛載目錄內的檔案；訪客禁止上傳、建立資料夾、改名、移動和刪除。頁面右下角「編輯 🔒」通往管理員密碼登入頁。請只掛載準備公開的資料夾。改回 `false` 並重新部署即可關閉公開瀏覽。

`render.yaml` 也可供 Blueprint 使用，已固定 `plan: free`；部署前仍要核對帳戶頁面的實際價格。

## 快速上傳

登入 `admin` 後，在檔案瀏覽頁左下角的快速上傳區拖入文件，或聚焦該區後按 ⌘V 貼上圖片／截圖，即開始上傳。也可按「選擇文件」，支援多檔。目的地為操作開始時正在瀏覽的掛載資料夾；根首頁沒有可寫入掛載時會提示選擇資料夾。

同名文件會逐一詢問是否覆蓋，選擇跳過會保留原檔；失敗項目可按「重試」。成功後更新列表。訪客只能瀏覽，不能上傳。暫不支援整個資料夾、下載連結或保證 Finder 複製文件後直接貼上。

介面透過 AList 的 `customize_body` 設定載入，與本部署綁定；不要另外覆寫該設定。

## 掛載 Google Drive

Google 免費 15 GB 空間由 Drive、Gmail 和 Google Photos 共用。按照 [AList 官方 Google Drive 文件](https://alistgo.com/guide/drivers/googledrive.html) 用自己的 OAuth Client ID、Client Secret、Refresh Token 掛載。Google Cloud 專案只啟用 Drive API，不啟用計費。帳戶登入及 Google 授權由本人完成。

在 AList 管理頁新增 GoogleDrive 儲存，掛載路徑可設 `/GoogleDrive`，根資料夾 ID 可用 `root` 或指定資料夾 ID。Testing 模式的 OAuth refresh token 可能在 7 天後到期，長期使用需按 Google OAuth 規則調整應用狀態。先用小檔案驗證實際上傳與下載。

## 休眠後自動還原

Render 免費服務閒置 15 分鐘後休眠，喚醒約需一分鐘。休眠、重啟和重新部署會丟失本機檔案。因此必須保存掛載設定：

```sh
python3 export-storages.py https://你的實際網址.onrender.com
```

程式隱藏輸入管理員密碼，將掛載匯出到 `storages.secret.json`。檔案包含雲盤憑證，只將其內容保存到 Render Environment 的 `ALIST_STORAGES_JSON`，不要提交至 Git，也不要傳到聊天。

更新變數後重啟，確認掛載能還原。每次修改掛載或重新授權後，重新匯出並更新該變數。只還原管理員與掛載，額外使用者、索引、分享設定及任務歷史不會自動還原。Google Drive 的檔案由 Google 保存。

## 免費限制

- 每個 workspace 每月 750 個免費運行小時，與同一 workspace 的其他免費服務共用。
- 不綁付款方式。免費流量或 build 額度超標時，服務或新建置可能被停用至下一個計費週期。
- Render 可能暫停大量主動連接外部儲存的免費服務。本方案只適合個人輕量使用，不能保證大檔案或大量傳輸可長期免費。
- 不做防休眠輪詢，不將臨時磁碟作永久儲存。

## 驗證範圍

啟動腳本已在官方 macOS AList 原生版本上驗證登入、訪客保護及掛載還原。Render Docker Linux 建置與啟動已成功，實際網址為 https://alist-free-drive.onrender.com，登入頁已確認可開啟。公開模式已在本機通過 8 項權限檢查及瀏覽器驗證：訪客可列出檔案，寫入和管理 API 被拒絕，編輯按鈕通往登入頁。快速上傳已通過 13 項模擬介面行為檢查、7 項本機 AList API 驗證及瀏覽器多檔選取上傳驗證；拖入與剪貼簿圖片事件使用模擬測試，實際 Google Drive 上傳仍待掛載後驗證。公開模式已部署到 https://alist-free-drive.onrender.com，正式站已驗證首頁无需登入，編輯按鈕通往密碼登入頁。Google Drive 尚未掛載，實際雲端上傳、下載及重啟還原仍待驗證。

參考：<https://render.com/docs/free>、<https://render.com/docs/faq>、<https://alistgo.com/guide/drivers/googledrive.html>
