"""
ComfyUI AI Image Generation Nodes - 中文界面
四个节点：
1. AIImageSettings   - API 设置（服务器地址写死，可配置模型和 API 密钥）
2. AIImageGenerate   - 文生图
3. AIImageEdit       - 图像编辑
4. AIImageVariation  - 多图合成
"""
import io
import json
import base64
import torch
import numpy as np
from PIL import Image
import requests
from . import config
from . import api_client


# ============================================================
# 工具函数
# ============================================================

def pil_to_tensor(image: Image.Image) -> torch.Tensor:
    img = image.convert("RGB")
    arr = np.array(img).astype(np.float32) / 255.0
    return torch.from_numpy(arr).unsqueeze(0)


def tensor_to_pil(tensor: torch.Tensor) -> Image.Image:
    arr = (tensor.squeeze(0).cpu().numpy() * 255).clip(0, 255).astype(np.uint8)
    return Image.fromarray(arr)


def image_to_bytes(image: Image.Image, fmt="PNG") -> bytes:
    buf = io.BytesIO()
    image.save(buf, format=fmt)
    buf.seek(0)
    return buf.read()


def tensor_to_b64(tensor: torch.Tensor) -> str:
    img = tensor_to_pil(tensor)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode("utf-8")
    return f"data:image/png;base64,{b64}"


def bytes_to_tensor(data: bytes) -> torch.Tensor:
    img = Image.open(io.BytesIO(data))
    return pil_to_tensor(img)


# ============================================================
# 共用下拉列表
# ============================================================

def _model_list():
    return list(config.MODEL_OPTIONS)


def _size_list():
    settings = config.load_settings()
    model = settings.get("model", config.DEFAULT_MODEL)
    available = set(config.get_available_sizes(model))
    return [s for s in config.SIZE_OPTIONS if s in available]


def _quality_list():
    return list(config.QUALITY_OPTIONS)


def _format_list():
    return list(config.FORMAT_OPTIONS)


def _bg_list():
    return list(config.BACKGROUND_OPTIONS)


def _input_fidelity_list():
    return list(config.INPUT_FIDELITY_OPTIONS)


# ============================================================
# 节点 0：AIImageSettings - API 设置节点
# ============================================================

class AIImageSettings:
    """
    API 设置节点
    服务器地址已写死，只需配置模型和 API 密钥即可使用

    输出 settings_json（STRING），可连线到其他节点以显式传递配置；
    不连线时其他节点自动从 settings.json 读取。
    """

    @classmethod
    def INPUT_TYPES(cls):
        saved = config.load_settings()
        models = _model_list()
        return {
            "required": {
                "模型": (models, {"default": saved.get("model", config.DEFAULT_MODEL)}),
                "API 密钥": ("STRING", {
                    "default": saved.get("apiKey", ""),
                }),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("配置",)
    FUNCTION = "save"
    CATEGORY = "AI 图像"
    OUTPUT_NODE = True

    def save(self, **kwargs):
        model = kwargs.get("模型", config.DEFAULT_MODEL)
        api_key = kwargs.get("API 密钥", "")
        config.save_settings(model, api_key)
        settings_json = json.dumps({
            "baseUrl": config.DEFAULT_BASE_URL,
            "model": model,
            "apiKey": api_key,
        }, ensure_ascii=False)
        print(f"[AI 图像] 设置已保存 → 模型={model}  服务器={config.DEFAULT_BASE_URL}")
        return (settings_json,)


# ============================================================
# 节点 1：AIImageGenerate - 文生图
# ============================================================

class AIImageGenerate:
    """
    文生图节点
    根据文字描述生成图像
    """

    @classmethod
    def INPUT_TYPES(cls):
        models = _model_list()
        sizes = _size_list()
        return {
            "required": {
                "提示词": ("STRING", {
                    "multiline": True, "default": "",
                }),
                "图像尺寸": (sizes, {"default": sizes[0] if sizes else "1024x1024"}),
                "生成数量": ("INT", {"default": 1, "min": 1, "max": 10, "step": 1}),
                "图像质量": (_quality_list(), {"default": ""}),
                "输出格式": (_format_list(), {"default": "png"}),
                "背景处理": (_bg_list(), {"default": "auto"}),
            },
            "optional": {
                "模型": (models, {"default": models[0] if models else "gpt-image-2-all"}),
                "配置": ("STRING", {
                    "default": "", "forceInput": True, "multiline": True,
                }),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("图像",)
    FUNCTION = "generate"
    CATEGORY = "AI 图像"

    def generate(self, **kwargs):
        prompt = kwargs.get("提示词", "")
        size = kwargs.get("图像尺寸", "1024x1024")
        n = kwargs.get("生成数量", 1)
        quality = kwargs.get("图像质量", "")
        output_format = kwargs.get("输出格式", "png")
        background = kwargs.get("背景处理", "auto")
        model = kwargs.get("模型")
        settings_json = kwargs.get("配置", "")

        settings = _resolve_settings(settings_json)

        if not settings.get("apiKey"):
            raise RuntimeError("请先添加「AI 图像 - API 设置」节点，填入 API 密钥后执行")

        if not prompt.strip():
            raise RuntimeError("请输入图像描述（提示词）")

        if model is None:
            model = settings.get("model", config.DEFAULT_MODEL)

        params = {
            "model": model,
            "prompt": prompt,
            "n": n,
            "size": size,
            "output_format": output_format,
            "background": background,
        }
        if quality:
            params["quality"] = quality

        print(f"[AI 图像] 文生图生成中... 模型={model}  尺寸={size}  提示词={prompt[:60]}...")
        try:
            result = api_client.call_text_to_image(settings, params)
        except requests.exceptions.Timeout:
            raise RuntimeError(
                f"AI 图像生成超时（模型={model}，尺寸={size}）。\n"
                f"高清图像生成可能较慢，请稍后重试，或尝试较小的尺寸（如 1024x1024）。\n"
                f"如果持续超时，请检查服务器状态。"
            )
        except requests.exceptions.ConnectionError as e:
            raise RuntimeError(
                f"无法连接到服务器 {settings.get('baseUrl', config.DEFAULT_BASE_URL)}\n"
                f"请检查网络连接和服务器地址。\n原始错误: {e}"
            )
        images_data = result.get("data", [])
        print(f"[AI 图像] 已生成 {len(images_data)} 张图像")

        return (_images_to_tensor(images_data),)


# ============================================================
# 节点 2：AIImageEdit - 图像编辑
# ============================================================

class AIImageEdit:
    """
    图像编辑节点
    传入源图像 + 编辑描述，返回编辑后图像
    """

    @classmethod
    def INPUT_TYPES(cls):
        models = _model_list()
        sizes = _size_list()
        return {
            "required": {
                "输入图像": ("IMAGE",),
                "编辑描述": ("STRING", {
                    "multiline": True, "default": "",
                }),
                "图像尺寸": (sizes, {"default": sizes[0] if sizes else "1024x1024"}),
                "生成数量": ("INT", {"default": 1, "min": 1, "max": 10, "step": 1}),
                "图像质量": (_quality_list(), {"default": ""}),
                "输入保真度": (_input_fidelity_list(), {"default": ""}),
                "输出格式": (_format_list(), {"default": "png"}),
                "背景处理": (_bg_list(), {"default": "auto"}),
            },
            "optional": {
                "模型": (models, {"default": models[0] if models else "gpt-image-2-all"}),
                "配置": ("STRING", {
                    "default": "", "forceInput": True, "multiline": True,
                }),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("图像",)
    FUNCTION = "edit"
    CATEGORY = "AI 图像"

    def edit(self, **kwargs):
        image = kwargs.get("输入图像")
        prompt = kwargs.get("编辑描述", "")
        size = kwargs.get("图像尺寸", "1024x1024")
        n = kwargs.get("生成数量", 1)
        quality = kwargs.get("图像质量", "")
        input_fidelity = kwargs.get("输入保真度", "")
        output_format = kwargs.get("输出格式", "png")
        background = kwargs.get("背景处理", "auto")
        model = kwargs.get("模型")
        settings_json = kwargs.get("配置", "")

        settings = _resolve_settings(settings_json)

        if not settings.get("apiKey"):
            raise RuntimeError("请先添加「AI 图像 - API 设置」节点，填入 API 密钥后执行")

        if not prompt.strip():
            raise RuntimeError("请输入编辑描述")

        if model is None:
            model = settings.get("model", config.DEFAULT_MODEL)

        pil_img = tensor_to_pil(image)
        img_bytes = image_to_bytes(pil_img, "PNG")

        params = {
            "image": img_bytes,
            "fileName": "source.png",
            "model": model,
            "prompt": prompt,
            "n": n,
            "size": size,
            "output_format": output_format,
            "background": background,
        }
        if quality:
            params["quality"] = quality
        if input_fidelity:
            params["input_fidelity"] = input_fidelity

        print(f"[AI 图像] 图像编辑中... 模型={model}  尺寸={size}  描述={prompt[:60]}...")
        try:
            result = api_client.call_image_to_image(settings, params)
        except requests.exceptions.Timeout:
            raise RuntimeError(
                f"AI 图像编辑超时（模型={model}，尺寸={size}）。\n"
                f"图像编辑需要同时上传原图并处理，耗时较长。\n"
                f"当前超时设置为 600 秒，若仍超时可尝试使用较小的尺寸或降低保真度。"
            )
        except requests.exceptions.ConnectionError as e:
            raise RuntimeError(
                f"无法连接到服务器 {settings.get('baseUrl', config.DEFAULT_BASE_URL)}\n"
                f"请检查网络连接和服务器地址。\n原始错误: {e}"
            )
        images_data = result.get("data", [])
        print(f"[AI 图像] 已生成 {len(images_data)} 张图像")

        return (_images_to_tensor(images_data),)


# ============================================================
# 节点 3：AIImageVariation - 多图合成
# ============================================================

class AIImageVariation:
    """
    多图合成节点
    传入 2~5 张参考图 + 提示词，合成新图

    输入槽：参考图 1、参考图 2（必填） + 参考图 3、参考图 4、参考图 5（可选）
    """

    @classmethod
    def INPUT_TYPES(cls):
        models = _model_list()
        sizes = _size_list()
        return {
            "required": {
                "参考图 1": ("IMAGE",),
                "参考图 2": ("IMAGE",),
                "提示词": ("STRING", {
                    "multiline": True, "default": "",
                }),
                "图像尺寸": (sizes, {"default": sizes[0] if sizes else "1024x1024"}),
                "生成数量": ("INT", {"default": 1, "min": 1, "max": 10, "step": 1}),
                "图像质量": (_quality_list(), {"default": ""}),
                "输出格式": (_format_list(), {"default": "png"}),
                "背景处理": (_bg_list(), {"default": "auto"}),
            },
            "optional": {
                "参考图 3": ("IMAGE",),
                "参考图 4": ("IMAGE",),
                "参考图 5": ("IMAGE",),
                "模型": (models, {"default": models[0] if models else "gpt-image-2-all"}),
                "配置": ("STRING", {
                    "default": "", "forceInput": True, "multiline": True,
                }),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("图像",)
    FUNCTION = "variate"
    CATEGORY = "AI 图像"

    def variate(self, **kwargs):
        image_1 = kwargs.get("参考图 1")
        image_2 = kwargs.get("参考图 2")
        image_3 = kwargs.get("参考图 3")
        image_4 = kwargs.get("参考图 4")
        image_5 = kwargs.get("参考图 5")
        prompt = kwargs.get("提示词", "")
        size = kwargs.get("图像尺寸", "1024x1024")
        n = kwargs.get("生成数量", 1)
        quality = kwargs.get("图像质量", "")
        output_format = kwargs.get("输出格式", "png")
        background = kwargs.get("背景处理", "auto")
        model = kwargs.get("模型")
        settings_json = kwargs.get("配置", "")

        settings = _resolve_settings(settings_json)

        if not settings.get("apiKey"):
            raise RuntimeError("请先添加「AI 图像 - API 设置」节点，填入 API 密钥后执行")

        if not prompt.strip():
            raise RuntimeError("请输入提示词")

        if model is None:
            model = settings.get("model", config.DEFAULT_MODEL)

        # 收集所有已连接的图像（最少 2 张，最多 5 张）
        image_tensors = [image_1, image_2]
        for img in [image_3, image_4, image_5]:
            if img is not None:
                image_tensors.append(img)

        b64_list = []
        for t in image_tensors:
            if t.shape[0] > 1:
                t = t[0:1]
            b64_list.append(tensor_to_b64(t))

        params = {
            "model": model,
            "images": b64_list,
            "prompt": prompt,
            "n": n,
            "size": size,
            "output_format": output_format,
            "background": background,
        }
        if quality:
            params["quality"] = quality

        print(f"[AI 图像] 多图合成中... 模型={model}  参考图={len(b64_list)}张  提示词={prompt[:60]}...")
        try:
            result = api_client.call_text_to_image(settings, params)
        except requests.exceptions.Timeout:
            raise RuntimeError(
                f"AI 多图合成超时（模型={model}，尺寸={size}）。\n"
                f"多图合成需要处理多张参考图，耗时较长。\n"
                f"若持续超时可尝试减少参考图数量或使用较小尺寸。"
            )
        except requests.exceptions.ConnectionError as e:
            raise RuntimeError(
                f"无法连接到服务器 {settings.get('baseUrl', config.DEFAULT_BASE_URL)}\n"
                f"请检查网络连接。原始错误: {e}"
            )
        images_data = result.get("data", [])
        print(f"[AI 图像] 已生成 {len(images_data)} 张图像")

        return (_images_to_tensor(images_data),)


# ============================================================
# 辅助函数
# ============================================================

def _images_to_tensor(images_data):
    """API 返回的图片列表 → ComfyUI IMAGE tensor batch"""
    tensors = []
    for item in images_data:
        img_url = item.get("url")
        if not img_url and item.get("b64_json"):
            img_url = "data:image/png;base64," + item["b64_json"]
        if img_url:
            img_bytes = api_client.download_image(img_url)
            tensors.append(bytes_to_tensor(img_bytes))
    if not tensors:
        raise RuntimeError("API 未返回任何图像，请检查 API 密钥和模型是否正确")
    return torch.cat(tensors, dim=0)


def _resolve_settings(settings_json: str) -> dict:
    """解析配置来源，优先级：连线传入 > settings.json"""
    if settings_json and settings_json.strip():
        try:
            return json.loads(settings_json)
        except json.JSONDecodeError:
            print("[AI 图像] 配置解析失败，使用本地设置")
    return config.load_settings()


# ============================================================
# 节点映射
# ============================================================

NODE_CLASS_MAPPINGS = {
    "AIImageSettings": AIImageSettings,
    "AIImageGenerate": AIImageGenerate,
    "AIImageEdit": AIImageEdit,
    "AIImageVariation": AIImageVariation,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "AIImageSettings": "AI 图像 - API 设置",
    "AIImageGenerate": "AI 图像 - 文生图",
    "AIImageEdit": "AI 图像 - 图像编辑",
    "AIImageVariation": "AI 图像 - 多图合成",
}
