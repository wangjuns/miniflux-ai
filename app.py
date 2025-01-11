import requests
import openai
from openai import OpenAI
import os
import logging

# 设置日志记录器
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_unread_entries(
    miniflux_url: str, miniflux_api_key: str, category_id: int
) -> list:
    headers = {"X-Auth-Token": miniflux_api_key}
    response = requests.get(
        f"{miniflux_url}/v1/entries",
        headers=headers,
        params={
            "status": "unread",
            "category_id": category_id,
        },
        timeout=10,
    )
    response.raise_for_status()
    return response.json().get("entries", [])


def generate_summary(client: OpenAI, openai_model: str, content: str) -> str:
    try:
        response = client.chat.completions.create(
            model=openai_model,
            messages=[
                {"role": "system", "content": "你是一个优秀的摘要生成助手。"},
                {"role": "user", "content": f"请为以下内容生成中文摘要：\n{content}"},
            ],
            max_tokens=300,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error("Error generating summary: %s", e)
        return None


def translate_content(client: OpenAI, openai_model: str, content: str) -> str:
    try:
        response = client.chat.completions.create(
            model=openai_model,
            messages=[
                {
                    "role": "system",
                    "content": "你是一个优秀的翻译助手，可以将文本翻译成中文并保留原文格式。",
                },
                {"role": "user", "content": f"请将以下内容翻译成中文：\n{content}"},
            ],
            max_tokens=30000,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error("Error translating content: %s", e)
        return None


def update_entry_content(
    miniflux_url: str,
    miniflux_api_key: str,
    entry_id: int,
    content: str,
    summary: str,
    translation: str,
) -> bool:
    headers = {"X-Auth-Token": miniflux_api_key}

    # 使用entry_id作为div的id
    summary_template = f"""
<div id='summary-{entry_id}' style='border: 1px solid #ccc; padding: 10px; margin-bottom: 10px; background-color: #f9f9f9;'>
    <strong>摘要：</strong>
    <p>{summary}</p>
</div>
"""
    translation_template = f"""
<div id='translation-{entry_id}' style='border: 1px solid #ccc; padding: 10px; margin-bottom: 10px; background-color: #eef9f9;'>
    <strong>翻译：</strong>
    <p>{translation}</p>
</div>
"""

    # 增加原文开始标识
    original_content_marker = (
        f"<div id='original-{entry_id}'><strong>原文开始：</strong></div>"
    )

    # 检查现有内容中是否已经包含这些div
    if (
        f"id='summary-{entry_id}'" in content
        and f"id='translation-{entry_id}'" in content
    ):
        logger.info("Entry ID %d already contains summary and translation.", entry_id)
        return True  # 已经存在，不需要更新

    updated_content = (
        summary_template + translation_template + original_content_marker + content
    )
    payload = {"content": updated_content}
    response = requests.put(
        f"{miniflux_url}/v1/entries/{entry_id}",
        headers=headers,
        json=payload,
        timeout=10,
    )

    # 新增日志记录响应内容
    if response.status_code not in {204, 200, 201}:
        logger.error(
            "Failed to update entry ID %d. Status code: %d, Response: %s",
            entry_id,
            response.status_code,
            response.text,
        )

    response.raise_for_status()
    return response.status_code in {204, 200, 201}


def process_entry(
    client: OpenAI,
    openai_model: str,
    miniflux_url: str,
    miniflux_api_key: str,
    entry: dict,
) -> None:
    entry_id = entry["id"]
    title = entry["title"]
    content = entry["content"]

    logger.info("Processing entry: %s (ID: %d)", title, entry_id)

    # 调用OpenAI API生成摘要和翻译
    summary = generate_summary(client, openai_model, content)
    translation = translate_content(client, openai_model, content)

    if summary and translation:
        logger.info("Generated summary: %s", summary)
        logger.info("Generated translation.")

        # 更新文章内容
        success = update_entry_content(
            miniflux_url,
            miniflux_api_key,
            entry_id,
            content,
            summary,
            translation,
        )
        if success:
            logger.info("Updated entry ID %d with new content.", entry_id)
        else:
            logger.error("Failed to update entry ID %d.", entry_id)
    else:
        logger.error("Failed to process entry ID %d.", entry_id)


def setup_client() -> OpenAI:
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_base_url = os.getenv("OPENAI_BASE_URL")
    return openai.OpenAI(api_key=openai_api_key, base_url=openai_base_url)


def main() -> None:
    # 从环境变量获取配置
    miniflux_url = os.getenv("MINIFLUX_URL")
    miniflux_api_key = os.getenv("MINIFLUX_API_KEY")
    openai_model = os.getenv("OPENAI_MODEL")
    category_id = int(os.getenv("CATEGORY_ID", "4"))  # 默认值为4

    if not all(
        [
            miniflux_url,
            miniflux_api_key,
            openai_model,
        ]
    ):
        logger.error("Error: Missing required environment variables.")
        return

    client = setup_client()

    # 获取未读文章
    unread_entries = get_unread_entries(miniflux_url, miniflux_api_key, category_id)

    max_entries_to_process = 1  # 设置单次最多处理的entry数量
    for entry in unread_entries[:max_entries_to_process]:
        process_entry(client, openai_model, miniflux_url, miniflux_api_key, entry)


if __name__ == "__main__":
    main()
