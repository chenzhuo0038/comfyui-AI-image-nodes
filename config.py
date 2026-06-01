"""
ComfyUI AI Image Generation - 配置管理
对应原PS插件中的 localStorage 设置存储
"""
import os
import json

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "settings.json")

DEFAULT_BASE_URL = "https://checct.site"
DEFAULT_MODEL = "gpt-image-2-all"

# 所有下拉选项均为纯字符串列表（ComfyUI 元组格式有序列化兼容问题）
MODEL_OPTIONS = ["gpt-image-2-all"]

SIZE_OPTIONS = ["1024x1024", "1536x1024", "1024x1536"]

# key=模型, value=支持的尺寸列表
SIZE_MAP = {
    "gpt-image-2-all": ["1024x1024", "1536x1024", "1024x1536"],
}

QUALITY_OPTIONS = ["", "auto", "low", "medium", "high"]

FORMAT_OPTIONS = ["png", "jpeg", "webp"]

BACKGROUND_OPTIONS = ["auto", "transparent", "opaque"]

INPUT_FIDELITY_OPTIONS = ["", "low", "high"]


def load_settings():
    """加载设置，对应原插件的 d() 函数"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {
                "baseUrl": data.get("baseUrl", DEFAULT_BASE_URL),
                "model": data.get("model", DEFAULT_MODEL),
                "apiKey": data.get("apiKey", ""),
            }
    except Exception:
        pass
    return {"baseUrl": DEFAULT_BASE_URL, "model": DEFAULT_MODEL, "apiKey": ""}


def save_settings(model, apiKey):
    """保存设置，服务器地址已写死，仅保存模型和 API 密钥"""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({"model": model, "apiKey": apiKey}, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def get_available_sizes(model):
    """根据模型返回支持的尺寸"""
    return SIZE_MAP.get(model, ["1024x1024"])
