# Deployment Guide for AWS EC2 ☁️

This guide will help you set up the Funding Monitor to run 24/7 on your EC2 instance.

## Prerequisites
- An active AWS EC2 instance (Ubuntu 22.04 or 24.04 recommended).
- SSH Access to your instance.
- **Security Group**: Ensure **Port 8080** (Custom TCP) is open in your Security Group inbound rules so you can access the dashboard.

## 1. Connect to your EC2
Open your terminal and SSH into your server:
```bash
ssh -i "your-key.pem" ubuntu@your-ec2-ip-address
```

## 2. Install System Dependencies
Update the package list and install Python tools:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv git -y
```

## 3. Clone the Repository
Clone your project (replace with your repo URL):
```bash
git clone https://github.com/lspss93119/funding_monitor.git
cd funding_monitor
```

## 4. Setup Python Environment
Create a virtual environment and install requirements:
```bash
# Create venv
python3 -m venv venv

# Activate and install
source venv/bin/activate
pip install -r requirements.txt
```

## 5. Configure Systemd Service
This ensures the app runs in the background and restarts automatically if it crashes or the server reboots.

1. **Edit the Service File (Optional)**:
   If your username is NOT `ubuntu` or your path is different, edit `funding_monitor.service` now using `nano funding_monitor.service`.

2. **Copy to System Directory**:
   ```bash
   sudo cp funding_monitor.service /etc/systemd/system/
   ```

3. **Reload and Start**:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable funding_monitor
   sudo systemctl start funding_monitor
   ```

4. **Check Status**:
   ```bash
   sudo systemctl status funding_monitor
   ```
   You should see `Active: active (running)`.

## 6. Access the Dashboard
Open your browser and go to:
`http://<your-ec2-ip>:8080`

🎉 **Done!** Your monitor is now recording data 24/7.

---
### Maintenance Commands

- **View Logs**:
  ```bash
  journalctl -u funding_monitor -f
  ```
- **Restart App** (after code update):
  ```bash
  cd ~/funding_monitor
  git pull
  sudo systemctl restart funding_monitor
  ```
