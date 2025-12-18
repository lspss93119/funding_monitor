# AWS EC2 部署指南 ☁️

本指南將協助您在 EC2 實例上設定 Funding Monitor，讓它能夠 24/7 全天候運行。

## 事前準備
- 一個執行中的 AWS EC2 實例 (建議使用 Ubuntu 22.04 或 24.04)。
- 擁有伺服器的 SSH 存取權限 (Key .pem 檔案)。
- **安全群組 (Security Group)**：確保您的安全群組 "Inbound Rules" 已開啟 **Port 8080** (Custom TCP)，這樣您才能從瀏覽器看到儀表板。

## 1. 連線到您的 EC2
1. **設定金鑰權限** (重要！否則會報錯 `Permissions 0644 too open`)：
   ```bash
   chmod 400 "your-key.pem"
   ```

2. **連線伺服器**：
   打開終端機 (Terminal)，使用 SSH 連入您的伺服器：
   ```bash
   ssh -i "your-key.pem" ubuntu@your-ec2-ip-address
   ```

## 2. 安裝系統套件
更新系統並安裝 Python 相關工具：
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv git -y
```

## 3. 下載專案代碼
Clone 您的專案 (請替換為您的 Github 網址)：
```bash
git clone https://github.com/lspss93119/funding_monitor.git
cd funding_monitor
```

## 4. 設定 Python 環境
建立虛擬環境並安裝依賴套件，以免影響系統 Python：
```bash
# 建立虛擬環境 (venv)
python3 -m venv venv

# 啟動並安裝
source venv/bin/activate
pip install -r requirements.txt
```

## 5. 設定 Systemd 背景服務
這能確保程式在背景執行，且當伺服器重開機或程式崩潰時會自動重啟。

1. **檢查設定檔 (可選)**：
   如果是使用預設的 `ubuntu` 使用者，通常不需要修改。若您的使用者名稱不同，請編輯設定檔：
   ```bash
   nano funding_monitor.service
   ```

2. **複製到系統目錄**：
   ```bash
   sudo cp funding_monitor.service /etc/systemd/system/
   ```

3. **啟動服務**：
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable funding_monitor
   sudo systemctl start funding_monitor
   ```

4. **檢查狀態**：
   ```bash
   sudo systemctl status funding_monitor
   ```
   如果看到綠色的 `Active: active (running)` 就代表成功了！

## 6. 開啟儀表板
現在打開您的瀏覽器，網址輸入：
`http://<您的-EC2-IP>:8080`

🎉 **大功告成！** 您的監控程式現在已經在雲端 24 小時不間斷運行了。

---
### 常用維護指令

- **查看即時 Log**：
  ```bash
  journalctl -u funding_monitor -f
  ```
- **更新程式碼並重啟** (當您有新功能上傳到 Github 時)：
  ```bash
  cd ~/funding_monitor
  git pull
  sudo systemctl restart funding_monitor
  ```
