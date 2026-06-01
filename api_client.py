"""
ComfyUI AI Image Generation - API 客户端
封装对 OpenAI 兼容 API 的调用（/v1/images/generations, /v1/images/edits）
"""
import base64
import requests
from . import config


def _build_url(base_url, path):
    """拼接 API URL，去除末尾多余斜杠"""
    return base_url.rstrip("/") + path


def call_text_to_image(settings, params):
    """
    文生图 / 多图合成
    对应原插件中的 generate 和 variation 流程
    POST /v1/images/generations
    """
    base_url = settings.get("baseUrl", config.DEFAULT_BASE_URL)
    api_key = settings.get("apiKey", "")
    model = params.get("model", settings.get("model", config.DEFAULT_MODEL))

    url = _build_url(base_url, "/v1/images/generations")

    body = {"model": model}

    # prompt
    if params.get("prompt"):
        body["prompt"] = params["prompt"]

    # n (生成数量)
    if params.get("n"):
        body["n"] = params["n"]

    # size
    if params.get("size"):
        body["size"] = params["size"]

    # output_format
    if params.get("output_format"):
        body["output_format"] = params["output_format"]

    # background
    if params.get("background"):
        body["background"] = params["background"]

    # quality
    if params.get("quality"):
        body["quality"] = params["quality"]

    # image (多图参考 - variation 模式)
    if params.get("images") and isinstance(params["images"], list):
        body["image"] = params["images"]

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }

    response = requests.post(url, json=body, headers=headers, timeout=120)
    data = response.json()

    if not response.ok:
        error_msg = "HTTP {} {}".format(response.status_code, response.reason)
        if data.get("error"):
            err = data["error"]
            error_msg = err.get("message") or err.get("code") or error_msg
        elif data.get("message"):
            error_msg = data["message"]
        raise RuntimeError(error_msg)

    return data


def call_image_to_image(settings, params):
    """
    图生图 / 图像编辑
    对应原插件中的 edit 流程
    POST /v1/images/edits (multipart/form-data)
    """
    base_url = settings.get("baseUrl", config.DEFAULT_BASE_URL)
    api_key = settings.get("apiKey", "")
    model = params.get("model", settings.get("model", config.DEFAULT_MODEL))

    url = _build_url(base_url, "/v1/images/edits")

    image_data = params.get("image")
    file_name = params.get("fileName", "source.png")

    form = {}
    form["image"] = (file_name, image_data, "image/png")
    form["model"] = (None, model)

    if params.get("prompt"):
        form["prompt"] = (None, params["prompt"])
    if params.get("n"):
        form["n"] = (None, str(params["n"]))
    if params.get("size"):
        form["size"] = (None, params["size"])
    if params.get("output_format"):
        form["output_format"] = (None, params["output_format"])
    if params.get("background"):
        form["background"] = (None, params["background"])
    if params.get("quality"):
        form["quality"] = (None, params["quality"])
    if params.get("input_fidelity"):
        form["input_fidelity"] = (None, params["input_fidelity"])

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }

    response = requests.post(url, files=form, headers=headers, timeout=120)
    data = response.json()

    if not response.ok:
        error_msg = "HTTP {} {}".format(response.status_code, response.reason)
        if data.get("error"):
            err = data["error"]
            error_msg = err.get("message") or err.get("code") or error_msg
        elif data.get("message"):
            error_msg = data["message"]
        raise RuntimeError(error_msg)

    return data


def download_image(url_or_b64):
    """
    下载生成的图像，返回 bytes
    支持 URL 和 base64 (data:image/...;base64,...)
    """
    if url_or_b64.startswith("data:"):
        # base64 内联图像
        header, b64 = url_or_b64.split(",", 1)
        return base64.b64decode(b64)
    else:
        # URL 下载
        resp = requests.get(url_or_b64, timeout=60)
        resp.raise_for_status()
        return resp.content
