import requests
import json

# --- 1. 配置基础信息 ---
# 警告：直接在代码中写入API密钥存在安全风险，建议在生产环境中使用环境变量等更安全的方式。
api_key = "sk-izdctsmxyxdsypxradjlyvbnrrtyjglaiqfkfsvvognfzbkg"
api_base_url = "https://api.siliconflow.cn/v1"
endpoint = f"{api_base_url}/chat/completions"

# --- 2. 构造请求头 ---
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

def generate_comment(article_title, article_summary):
    """
    调用SiliconFlow API为指定文章生成一条高质量评论。

    Args:
        article_title (str): 文章的标题。
        article_summary (str): 文章的摘要或核心观点。

    Returns:
        str: AI生成的评论文本，如果失败则返回错误信息。
    """
    if "izdctsmxyxdsypxradjlyvbnrrtyjglaiqfkfsvvognfzbkg" not in api_key:
        return "错误：请确认API Key是否正确填写。"

    # --- 3. 构造请求体 (Payload) ---
    # 已更新为您提供的最新版提示词
    system_prompt = """
# 角色
你是一位热爱在知识社区分享见解的深度读者。你的评论风格真诚、有洞察力，从不进行空洞的赞美。你善于捕捉文章中的亮点，并乐于结合自身的经历和思考，提出有价值的观点或疑问。

# 任务
请你阅读以下文章信息，并为这篇文章撰写一条大约100-150字的精选评论。

# 评论要求
1. 避免套话：禁止使用"写得真好"、"学到了"、"感谢分享"等过于宽泛、没有信息量的词语开头或结尾。
2. 具体引用：必须引用或转述文章中的一个具体观点、案例、数据或触动你的句子，作为评论的起点。
3. 表达真情实感：分享由引用的内容所触发的个人联想、真实经历、感悟，或者是一个深入的疑问。
4. 自然流畅：语言风格像是在和朋友聊天，可以适当使用一些生活化的词语和标点来增强语气。
"""

    # 用户提供的具体文章信息
    user_prompt = f"文章标题：《{article_title}》\n核心内容：{article_summary}"

    payload = {
        "model": "Qwen/Qwen3-8B",
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        "stream": False,
        "max_tokens": 512,
        "temperature": 0.8,
        "top_p": 0.8
    }

    # --- 4. 发送HTTP POST请求 ---
    try:
        response = requests.post(endpoint, headers=headers, data=json.dumps(payload), timeout=60)
        response.raise_for_status()

        # --- 5. 处理并返回结果 ---
        response_data = response.json()
        comment = response_data["choices"][0]["message"]["content"]
        return comment.strip()

    except requests.exceptions.HTTPError as http_err:
        return f"API请求失败，HTTP错误: {http_err}\n返回内容: {response.text}"
    except requests.exceptions.RequestException as e:
        return f"网络或请求配置错误: {e}"
    except KeyError:
        return f"解析API返回数据失败，可能返回了错误信息: {response.text}"
    except Exception as e:
        return f"发生未知错误: {e}"

# --- 如何使用这个模块的示例 ---
#
# 1. 将此文件保存为 "comment_generator.py"。
# 2. 在另一个Python文件中，你可以像下面这样导入和使用它：
#
# from comment_generator import generate_comment
#
# title = "我的文章标题"
# summary = "我的文章摘要..."
# my_comment = generate_comment(title, summary)
# print(my_comment)
#