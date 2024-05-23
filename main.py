import socket
import requests
import json
import os
from datetime import datetime
import time
import hashlib
import base64
import hmac

note_name = os.environ.get('NOTE_NAME')


def get_ip(domain):
    try:
        return socket.gethostbyname(domain)
    except socket.gaierror as e:
        error_message = f"获取IP地址失败, 错误信息: {e}"
        print(error_message)
        send_rich_text_to_webhook(None, None, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), None, None, note_name,False, os.environ.get('FEISHU_SECRETS'), error_message)
        return None

def gen_sign(timestamp, secret):
    string_to_sign = '{}\n{}'.format(timestamp, secret)
    hmac_code = hmac.new(string_to_sign.encode("utf-8"), digestmod=hashlib.sha256).digest()
    sign = base64.b64encode(hmac_code).decode('utf-8')
    return sign

def send_rich_text_to_webhook(ip, port, readable_time, last_read_time, id, name, success, secret, error_message=None):
    github_repo = os.environ.get('GH_REPO')
    webhook_url = os.environ.get('WEBHOOK_URL')
    headers = {"Content-Type": "application/json"}
    timestamp = str(int(time.time()))
    sign = gen_sign(timestamp, secret)
    readable_time = readable_time if readable_time else "N/A"
    last_read_time = last_read_time if last_read_time else "N/A"
    content = [
        [{"tag": "text", "text": f"触发仓库: {github_repo}"}],
        [{"tag": "text", "text": f"剪贴板: {name if name else 'N/A'}"}],
        [{"tag": "text", "text": f"剪贴板ID: {id if id else 'N/A'}"}],
        [{"tag": "text", "text": f"新IP: {ip if ip else 'N/A'}"}],
        [{"tag": "text", "text": f"端口: {port if port else 'N/A'}"}],
        [{"tag": "text", "text": f"完成时间: {readable_time}"}],
        [{"tag": "text", "text": f"上次阅读时间: {last_read_time}"}],
        [{"tag": "text", "text": f"是否成功: {'成功' if success else '失败'}"}]
    ]
    if error_message:
        content.append([{"tag": "text", "text": f"错误信息: {error_message}"}])
    data = {
        "timestamp": timestamp,
        "sign": sign,
        "msg_type": "post",
        "content": {
            "post": {
                "zh_cn": {
                    "title": "剪贴板通知",
                    "content": content
                }
            }
        }
    }
    response = requests.post(webhook_url, headers=headers, data=json.dumps(data))
    if response.status_code == 200:
        print("消息发送成功！")
    else:
        print(f"消息发送失败，状态码：{response.status_code}")

def get_note(note_name):
    url = "https://api.txttool.cn/netcut/note/info/"
    data = {
        "note_name": note_name,
        "note_pwd": os.environ.get('NOTE_PWD')
    }
    try:
        response = requests.post(url, data=data)
        if response.status_code == 200:
            json_data = response.json()
            if "data" in json_data and "note_content" in json_data["data"]:
                note_id = json_data["data"]["note_id"]
                note_token = json_data["data"]["note_token"]
                last_read_time = json_data["data"]["last_read_time"]
                note_content = json_data["data"]["note_content"]
                return note_id, note_token, last_read_time, note_content, note_id
            else:
                error_message = "获取剪贴板内容失败，响应数据不完整。"
                send_rich_text_to_webhook(None, None, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), None, False, note_name, os.environ.get('FEISHU_SECRETS'), error_message)
                exit(-1)
        else:
            error_message = f"获取剪贴板内容失败, 状态码: {response.status_code}"
            send_rich_text_to_webhook(None, None, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), None, False, note_name, os.environ.get('FEISHU_SECRETS'), error_message)
            exit(-1)
    except Exception as e:
        error_message = f"获取剪贴板内容失败, 错误信息: {e}"
        send_rich_text_to_webhook(None, None, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), None, False, note_name, os.environ.get('FEISHU_SECRETS'), error_message)
        exit(-1)
    return None, None, None, None, None

def set_note(new_content, note_name, note_id, note_token):
    set_url = "https://api.txttool.cn/netcut/note/save/"
    set_data = {
        "note_name": note_name,
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
    note_id, note_token, last_read_time, note_content, note_id = get_note(note_name)
    fs_secret = os.environ.get('FEISHU_SECRETS')
    note_content_lines = note_content.split('\n')
    note_content_last = note_content_lines[-1] if note_content_lines else None
    if note_id is not None and note_token is not None:
        ip = get_ip('auto.c3pool.org')
        if ip is not None:
            new_content = f"{ip}:19999"
            if note_content_last == new_content:
                print("内容无需更新！")
                return 0
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if set_note(new_content, note_name, note_id, note_token):
                print("内容更新成功！")
                send_rich_text_to_webhook(ip, "19999", current_time, last_read_time, note_id, note_name, True, fs_secret)
            else:
                error_message = "内容更新失败！"
                print(error_message)
                send_rich_text_to_webhook(ip, "19999", current_time, last_read_time, note_id, note_name, False, fs_secret, error_message)
        else:
            error_message = "无法获取IP地址"
            print(error_message)
            send_rich_text_to_webhook(None, None, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), None, note_id, note_name, False, fs_secret, error_message)
    else:
        error_message = "获取剪贴板内容失败！"
        print(error_message)
        send_rich_text_to_webhook(None, None, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), None, note_id, note_name, False, fs_secret, error_message)

if __name__ == "__main__":
    main()
