import requests
import hashlib
import random
import time
from bs4 import BeautifulSoup
import os
import json
from datetime import datetime

# 生成签名
def generate_sign(word, app_key, app_secret, salt):
    sign_str = app_key + word + salt + app_secret
    hash_algorithm = hashlib.md5()
    hash_algorithm.update(sign_str.encode('utf-8'))
    return hash_algorithm.hexdigest()

# 查询单词定义
def create_request(word, app_key, app_secret):
    url = "https://openapi.youdao.com/api"
    salt = str(random.randint(1, 65536))
    sign = generate_sign(word, app_key, app_secret, salt)
    
    params = {
        'q': word,
        'from': 'en',
        'to': 'zh-CHS',
        'appKey': app_key,
        'salt': salt,
        'sign': sign
    }
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('errorCode') == '0':
            return data
        else:
            print(f"Error Code: {data.get('errorCode')}")
    else:
        print(f"Failed to fetch definition for word: {word}")
    return {}

# 提取详细字典内容
def extract_detailed_content(data):
    details = []
    if 'translation' in data:
        details.append(f"**Translation:** {', '.join(data['translation'])}")
    if 'basic' in data:
        if 'explains' in data['basic']:
            details.append(f"**Explains:**\n- " + "\n- ".join(data['basic']['explains']))
        if 'phonetic' in data['basic']:
            details.append(f"**Phonetic:** {data['basic']['phonetic']}")
    if 'web' in data:
        web_translations = []
        for item in data['web']:
            web_translations.append(f"- {item['key']}: {', '.join(item['value'])}")
        details.append("**Web Translations:**\n" + "\n".join(web_translations))
    if 'webdict' in data and 'url' in data['webdict']:
        webdict_url = data['webdict']['url']
        webdict_content = fetch_webdict_content(webdict_url)
        details.append(f"**详细释义:**\n{webdict_content}")
    return "\n".join(details)

# 抓取网页内容
def fetch_webdict_content(url):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        ul_element = soup.select_one('body > div > div:nth-of-type(2) > div:nth-of-type(1) > div > ul')
        if ul_element:
            return ul_element.get_text(separator='\n- ').strip()
    return "No content found"

# 获取API密钥
def get_api_keys():
    config_file = 'config.json'
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config.get('app_key'), config.get('app_secret')
    else:
        app_key = input("请输入有道API appKey: ")
        app_secret = input("请输入你的有道API appSecret: ")
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump({'app_key': app_key, 'app_secret': app_secret}, f)
        return app_key, app_secret

# 主程序入口
def main():
    output_file = 'English/单词.md'  # 保存到相对路径
    app_key, app_secret = get_api_keys()

    while True:
        words = []
        print("请输入单词，按 Enter 键输入下一个单词，连续两次 Enter 键开始翻译，输入 'exit' 退出：")
        enter_count = 0
        while True:
            word = input().strip()
            if word.lower() == 'exit':
                print("退出程序")
                return
            if word:
                words.append(word)
                enter_count = 0  # 重置计数器
            else:
                enter_count += 1
                if enter_count == 1:
                    break

        with open(output_file, 'r', encoding='utf-8') as f:
            existing_content = f.read()

        new_content = ""
        count = 0
        for word in words:
            result = create_request(word, app_key, app_secret)
            if result:
                detailed_content = extract_detailed_content(result)
                print(f"Detailed content for {word}: {detailed_content}")  # 打印详细内容
                # 删除空行
                detailed_content = "\n".join([line for line in detailed_content.split("\n") if line.strip() != "-"])
                new_content += f"## {word.capitalize()}\n{detailed_content}\n"
            
            count += 1
            if count % 5 == 0:
                print("等待5秒...")
                time.sleep(5)

        # 添加单词个数和日期
        date_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        summary = f"\n\n**本次查询单词个数:** {len(words)}\n**查询日期:** {date_str}\n"

        with open(output_file, 'a', encoding='utf-8') as f:  # 使用 'a' 模式追加内容到文件末尾
            f.write(new_content + summary)

if __name__ == '__main__':
    main()