import socket
import requests
import json
import os
# 时间相关
from datetime import datetime
# Bot 签名相关
import hashlib
import base64
import hmac
import time

print(f"url: {os.environ.get('WEBHOOK_URL')}, secret: {os.environ.get('FEISHU_SECRET')}, pwd: {os.environ.get('NOTE_PWD')}")

def get_ip(domain):
    try:
        return socket.gethostbyname(domain)
    except socket.gaierror:
        return None

def gen_sign(secret):
    # 获取当前时间戳
    timestamp = int(time.time())
    # 拼接timestamp和secret
    string_to_sign = '{}\n{}'.format(timestamp, secret)
    hmac_code = hmac.new(string_to_sign.encode("utf-8"), digestmod=hashlib.sha256).digest()
    # 对结果进行base64处理
    sign = base64.b64encode(hmac_code).decode('utf-8')
    return timestamp, sign

def send_rich_text_to_webhook(ip, port, timestamp, success, secret):
  github_repo = os.environ.get('GH_REPO')
  webhook_url = os.environ.get('WEBHOOK_URL')
  headers = {"Content-Type": "application/json"}
  _, sign = gen_sign(secret)
  data = {
    "timestamp": str(int(time.time())),
    "sign": sign,
    "msg_type": "post",
    "content": {
      "post": {
        "zh_cn": {
          "title": "剪贴板通知",
          "content": [
            [{"tag": "text", "text": f"触发仓库: {github_repo}"}],
            [{"tag": "text", "text": f"新的IP: {ip}"}],
            [{"tag": "text", "text": f"端口: {port}"}],
            [{"tag": "text", "text": f"时间: {timestamp}"}],
            [{"tag": "text", "text": f"是否成功: {'成功' if success else '失败'}"}]
          ]
        }
      }
    }
  }
  response = requests.post(webhook_url, headers=headers, data=json.dumps(data))
  if response.status_code == 200:
    print("消息发送成功！")
  else:
    print(f"消息发送失败，状态码：{response.status_code}")

def get_note():
  url = "https://api.txttool.cn/netcut/note/info/"
  data = {
    "note_name": "xmring_c3_ip_text",
    "note_pwd": os.environ.get('NOTE_PWD')
  }
  response = requests.post(url, data=data)
  if response.status_code == 200:
    json_data = response.json()
    if "data" in json_data and "note_content" in json_data["data"]:
      note_id = json_data["data"]["note_id"]
      note_token = json_data["data"]["note_token"]
      note_content = json_data["data"]["note_content"]
      return note_id, note_token, note_content
  return None, None, None

def set_note(new_content, note_id, note_token):
  set_url = "https://api.txttool.cn/netcut/note/save/"
  set_data = {
    "note_name": "xmring_c3_ip_text",
    "note_id": note_id,
    "note_content": new_content,
    "note_token": note_token,
    "expire_time": 94608000,
    "note_pwd": os.environ.get('NOTE_PWD')
  }
  response = requests.post(set_url, data=set_data)
  if response.status_code == 200:
    return True
  else:
    print(f"Error: Received status code {response.status_code}")
    return False

def main():
  note_id, note_token, note_content = get_note()
  fs_secret = os.environ.get('FEISHU_SECRETS')
  if note_id is not None and note_token is not None:
    ip = get_ip('auto.c3pool.org')
    if ip is not None:
      if note_content:
        new_content = f"{note_content}\n{ip}:19999"
      else:
        new_content = f"{ip}:19999"
      current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
      if set_note(new_content, note_id, note_token):
        print("内容更新成功！")
        send_rich_text_to_webhook(ip, "19999", current_time, True, fs_secret)
      else:
        print("内容更新失败！")
        send_rich_text_to_webhook(ip, "19999", current_time, False, fs_secret)
    else:
      print("无法获取IP地址")
  else:
    print("获取剪贴板内容失败！")

if __name__ == "__main__":
    main()
