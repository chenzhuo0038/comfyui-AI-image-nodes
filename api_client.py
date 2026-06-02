"""
ComfyUI AI Image Generation - API 客户端
封装对 OpenAI 兼容 API 的调用（/v1/images/generations, /v1/images/edits）
"""
import base64
import time
import requests
from . import config

# 生成请求的超时（秒）— 高清图生成可能数分钟
_GEN_TIMEOUT = 600
# 下载图片的超时（秒）
_DL_TIMEOUT = 120
# 最大重试次数，仅对可重试的异常（连接超时、可读超时、5xx）
_MAX_RETRIES = 2
# 跳过系统代理（避免代理干扰）
_NO_PROXY = {"http": "", "https": ""}


def _request_with_retry(method, url, max_retries=_MAX_RETRIES, **kwargs):
    """
    带指数退避重试的请求封装
    仅对 connection / read / 5xx 错误重试
    """
    # 强制绕过系统代理
    kwargs.setdefault("proxies", _NO_PROXY)

    last_exc = None
    for attempt in range(max_retries + 1):
        try:
            resp = requests.request(method, url, **kwargs)
            # 检查 5xx 服务器错误是否需要重试
            if resp.status_code >= 500 and attempt < max_retries:
                wait = 5 * (2 ** attempt)
                print(f"[AI 图像] 服务器错误 {resp.status_code}，{wait}秒后重试 "
                      f"({attempt + 1}/{max_retries})...")
                time.sleep(wait)
                continue
            return resp
        except (requests.exceptions.ConnectionError,
                requests.exceptions.Timeout) as e:
            last_exc = e
            if attempt < max_retries:
                wait = 5 * (2 ** attempt)
                print(f"[AI 图像] 请求超时/连接失败，{wait}秒后重试 "
                      f"({attempt + 1}/{max_retries})...")
                time.sleep(wait)
            else:
                break
        except requests.exceptions.RequestException as e:
            last_exc = e
            break
    raise last_exc


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

    response = _request_with_retry(
        "POST", url, json=body, headers=headers, timeout=_GEN_TIMEOUT
    )
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

    response = _request_with_retry(
        "POST", url, files=form, headers=headers, timeout=_GEN_TIMEOUT
    )
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
        # URL 下载，跳过系统代理
        resp = requests.get(url_or_b64, timeout=_DL_TIMEOUT, proxies=_NO_PROXY)
        resp.raise_for_status()
        return resp.content
