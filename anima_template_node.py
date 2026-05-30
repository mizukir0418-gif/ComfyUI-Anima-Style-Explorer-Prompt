import os
import re
import socket
import ipaddress
import uuid
import urllib.parse
import json
import aiohttp
import aiohttp.abc
from aiohttp import web
from server import PromptServer
import folder_paths

# =====================================================================
# 🛡️ 安全防御核心辅助函数 (100% 保持您原文件的完整代码不变)
# =====================================================================

def verify_and_get_safe_ips(hostname):
    """
    【核心防御升级】
    1. 同时解析 IPv4 和 IPv6，彻底封杀 IPv6 逃逸。
    2. 获取并返回所有经过严格审计的安全 IP 列表，为消灭 DNS 重绑定做准备。
    """
    try:
        # 获取该域名的所有 IP 记录（包含 IPv4 和 IPv6）
        addr_info = socket.getaddrinfo(hostname, None)
        safe_ips = []
        
        for item in addr_info:
            family, _, _, _, sockaddr = item
            ip_str = sockaddr[0]
            
            # 移除 IPv6 潜在的 scope id 干扰
            if '%' in ip_str:
                ip_str = ip_str.split('%')[0]
                
            ip = ipaddress.ip_address(ip_str)
            
            # 严格审查：只要解析出的 IP 列表中有任何一个命中了内网、回环或本地链路，直接全盘拒绝
            if ip.is_private or ip.is_loopback or ip.is_link_local:
                return False, []
                
            safe_ips.append((family, ip_str))
            
        if not safe_ips:
            return False, []
            
        return True, safe_ips
    except Exception:
        return False, []

def verify_image_dna(file_path):
    """
    核心防御 2：真·图片 DNA 校验器（魔术字节审计）
    强行读取文件最前方的二进制字节，挂羊头卖狗肉的假图片在这里会瞬间露馅
    """
    try:
        if not os.path.exists(file_path):
            return False
            
        with open(file_path, "rb") as f:
            header = f.read(12)  # 只读前 12 个字节，极速且不占内存
            
        # 常见图片的真身二进制特征码（Magic Bytes）
        if header.startswith(b'\x89PNG\r\n\x1a\n'):
            return "png"
        if header.startswith(b'\xff\xd8\xff'):
            return "jpeg"
        if header.startswith(b'GIF87a') or header.startswith(b'GIF89a'):
            return "gif"
        if header.startswith(b'RIFF') and b'WEBP' in header:
            return "webp"
            
        return False  # 基因不匹配，断定为危险或伪装文件
    except Exception:
        return False

# =====================================================================
# 🌐 跨域安全下载路由注册 (100% 保持您原文件的完整代码不变)
# =====================================================================

MAX_SIZE = 30 * 1024 * 1024  # 硬限制最大 30MB

@PromptServer.instance.routes.post("/anima/upload_url")
async def upload_url_route(request):
    """
    黑科技安全路由：接收前端拖拽的网页 URL 并安全下载到本地 input 文件夹
    """
    temp_target_path = None
    try:
        data = await request.json()
        url = data.get("url")
        if not url:
            return web.json_response({"success": False, "error": "未接收到有效的图片URL"}, status=400)
            
        parsed_url = urllib.parse.urlparse(url)
        if parsed_url.scheme not in ("http", "https"):
            return web.json_response({"success": False, "error": "安全防御：非法协议"}, status=403)
            
        hostname = parsed_url.hostname
        if not hostname:
            return web.json_response({"success": False, "error": "安全防御：非法主机名"}, status=403)

        is_safe, safe_ips = verify_and_get_safe_ips(hostname)
        if not is_safe:
            return web.json_response({"success": False, "error": "安全防御：禁止访问内网或解析异常"}, status=403)
            
        input_dir = folder_paths.get_input_directory()

        original_filename = os.path.basename(parsed_url.path)
        if not original_filename or "." not in original_filename:
            original_filename = f"anima_drag_{uuid.uuid4().hex[:8]}.png"

        temp_target_path = os.path.join(input_dir, original_filename + ".downloading")
        
        if not os.path.abspath(temp_target_path).startswith(os.path.abspath(input_dir)):
            return web.json_response({"success": False, "error": "安全防御：检测到路径穿越攻击"}, status=403)

        class PinResolver(aiohttp.abc.AbstractResolver):
            async def resolve(self, host, port=0, family=socket.AF_INET):
                res = []
                for fam, ip_str in safe_ips:
                    res.append({
                        'hostname': host,
                        'host': ip_str,
                        'port': port,
                        'family': fam,
                        'proto': 0,
                        'flags': 0
                    })
                return res
            async def close(self): pass

        connector = aiohttp.TCPConnector(resolver=PinResolver(), use_dns_cache=False)

        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(url, timeout=10) as response:
                if response.status != 200:
                    return web.json_response({"success": False, "error": f"HTTP {response.status}"}, status=400)

                content_length = response.headers.get("Content-Length")
                if content_length and int(content_length) > MAX_SIZE:
                    return web.json_response({"success": False, "error": "文件体积超出30MB限制"}, status=400)

                size_counter = 0
                with open(temp_target_path, "wb") as f:
                    async for chunk in response.content.iter_chunked(8192):
                        size_counter += len(chunk)
                        if size_counter > MAX_SIZE:
                            f.close()
                            if os.path.exists(temp_target_path):
                                os.remove(temp_target_path)
                            return web.json_response({"success": False, "error": "实际数据流超出大小限制"}, status=400)
                        f.write(chunk)

        actual_type = verify_image_dna(temp_target_path)
        if not actual_type:
            if os.path.exists(temp_target_path):
                os.remove(temp_target_path)
            return web.json_response({"success": False, "error": "安全拦截：该文件伪装成图片格式，实际上不是真正的图片！"}, status=400)

        name_without_ext, _ = os.path.splitext(original_filename)
        expected_ext = ".jpg" if actual_type == "jpeg" else f".{actual_type}"
        
        final_filename = f"{name_without_ext}{expected_ext}"
        final_target_path = os.path.join(input_dir, final_filename)
        
        counter = 1
        while os.path.exists(final_target_path):
            final_filename = f"{name_without_ext}_{counter:05d}{expected_ext}"
            final_target_path = os.path.join(input_dir, final_filename)
            counter += 1

        os.rename(temp_target_path, final_target_path)
        return web.json_response({"success": True, "name": final_filename})

    except Exception as e:
        if temp_target_path and os.path.exists(temp_target_path):
            try:
                os.remove(temp_target_path)
            except Exception:
                pass
        return web.json_response({"success": False, "error": f"下载或安全审计失败: {str(e)}"}, status=500)


# =====================================================================
# 🧩 🌟 新增前置节点：Anima 2B Artist Pre-Config Outline (画师前置配置总纲)
# =====================================================================

class Anima2BArtistPreConfigOutlineNode:
    def __init__(self):
        pass
        
    @classmethod
    def INPUT_TYPES(s):
        # 预定义核心总纲的常用美学标签，并提供5个自定义映射插槽
        OPTIONS_LIST = [
            "None",
            "Character design", "Eye detailing",
            "Lineart", "Ink work",
            "Cel-shading", "Painterly", "Color Palette",
            "Fabric drapery", "Mechanical detailing",
            "Scenic Background", "Environment Design",
            "Atmospheric Lighting", "Rim Light",
            "VFX", "Particle effects",
            "Cinematic Framing", "Camera Perspective",
            "Custom_Slot_1", "Custom_Slot_2", "Custom_Slot_3", "Custom_Slot_4", "Custom_Slot_5"
        ]
        
        default_outline = (
            "【前置配置总纲】\n"
            "├── 1. 角色形体 ── [Character design / Eye detailing]\n"
            "├── 2. 线条线稿 ── [Lineart / Ink work]\n"
            "├── 3. 色彩渲染 ── [Cel-shading / Painterly / Color Palette]\n"
            "├── 4. 服饰道具 ── [Fabric drapery / Mechanical detailing]\n"
            "├── 5. 场景美术 ── [Scenic Background / Environment Design]\n"
            "├── 6. 光影氛围 ── [Atmospheric Lighting / Rim Light]\n"
            "├── 7. 视觉特效 ── [VFX / Particle effects]\n"
            "└── 8. 构图镜头 ── [Cinematic Framing / Camera Perspective]\n\n"
            "# 您可以在下方通过冒号新增、修改或覆盖自定义槽位名，例如：\n"
            "# Custom_Slot_1: Cyberpunk Style\n"
            "# Custom_Slot_2: Watercolor"
        )
        
        return {
            "required": {
                "outline_switch": ("BOOLEAN", {"default": True}),
                "artist_2_opt": (OPTIONS_LIST, {"default": "None"}),
                "artist_3_opt": (OPTIONS_LIST, {"default": "None"}),
                "artist_4_opt": (OPTIONS_LIST, {"default": "None"}),
                "artist_5_opt": (OPTIONS_LIST, {"default": "None"}),
                "artist_6_opt": (OPTIONS_LIST, {"default": "None"}),
                "artist_7_opt": (OPTIONS_LIST, {"default": "None"}),
                "artist_8_opt": (OPTIONS_LIST, {"default": "None"}),
                "artist_9_opt": (OPTIONS_LIST, {"default": "None"}),
                "artist_10_opt": (OPTIONS_LIST, {"default": "None"}),
                "custom_outline": ("STRING", {"multiline": True, "default": default_outline}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("outline_data",)
    FUNCTION = "export_outline"
    CATEGORY = "PromptHelper"

    def export_outline(self, outline_switch, artist_2_opt, artist_3_opt, artist_4_opt, artist_5_opt,
                       artist_6_opt, artist_7_opt, artist_8_opt, artist_9_opt, artist_10_opt, custom_outline=""):
        
        # 解析文本框中的自定义映射关系（支持英文冒号 ':' 和中文冒号 '：'）
        custom_mapping = {}
        if custom_outline and custom_outline.strip():
            for line in custom_outline.split("\n"):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if ":" in line or "：" in line:
                    parts = re.split(r':|：', line, maxsplit=1)
                    key = parts[0].strip()
                    val = parts[1].strip()
                    custom_mapping[key] = val

        opts_raw = [
            artist_2_opt, artist_3_opt, artist_4_opt, artist_5_opt,
            artist_6_opt, artist_7_opt, artist_8_opt, artist_9_opt, artist_10_opt
        ]
        
        # 如果选中的是自定义槽位且文本框有定义，自动替换为文本框写明的字符串
        resolved_options = []
        for opt in opts_raw:
            if opt in custom_mapping:
                resolved_options.append(custom_mapping[opt])
            else:
                resolved_options.append(opt)
                
        # 将配置数据打包为 JSON 字符串安全传输给节点1
        out_package = {
            "switch": outline_switch,
            "options": resolved_options
        }
        
        return (json.dumps(out_package),)


# =====================================================================
# 🧩 节点 1：Anima 2B Prompt Template 1 (画师控制 - 已移除顶部年代控制并支持总纲)
# =====================================================================

class Anima2BPromptTemplate1Node:
    def __init__(self):
        pass
        
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "artist_1": ("STRING", {"default": ""}), # 默认置空
                "artist_2": ("STRING", {"default": "@nakamura takeshi"}),
                "weight_2": ("FLOAT", {"default": 0.6, "min": 0.0, "max": 2.0, "step": 0.05}),
                "artist_3": ("STRING", {"default": "@zhibuji loom"}),
                "weight_3": ("FLOAT", {"default": 0.6, "min": 0.0, "max": 2.0, "step": 0.05}),
                "artist_4": ("STRING", {"default": "@momoko \\(momopoco\\)"}),
                "weight_4": ("FLOAT", {"default": 0.6, "min": 0.0, "max": 2.0, "step": 0.05}),
                "artist_5": ("STRING", {"default": "@koi han"}),
                "weight_5": ("FLOAT", {"default": 0.65, "min": 0.0, "max": 2.0, "step": 0.05}),
                "artist_6": ("STRING", {"default": ""}),
                "weight_6": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.05}),
                "artist_7": ("STRING", {"default": ""}),
                "weight_7": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.05}),
                "artist_8": ("STRING", {"default": ""}),
                "weight_8": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.05}),
                "artist_9": ("STRING", {"default": ""}),
                "weight_9": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.05}),
                "artist_10": ("STRING", {"default": ""}),
                "weight_10": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.05}),
            },
            "optional": {
                "upstream_text": ("STRING", {"forceInput": True}), 
                "outline_data": ("STRING", {"forceInput": True}), # 接收自总纲节点的配置流
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "build_prompt"
    CATEGORY = "PromptHelper"

    def build_prompt(self, artist_1, artist_2, weight_2, artist_3, weight_3, 
                     artist_4, weight_4, artist_5, weight_5, artist_6, weight_6, 
                     artist_7, weight_7, artist_8, weight_8, artist_9, weight_9, 
                     artist_10, weight_10, upstream_text="", outline_data=""):
        
        # 解析前置总纲节点的配置
        outline_switch = False
        outline_options = ["None"] * 9
        
        if outline_data and outline_data.strip():
            try:
                package = json.loads(outline_data)
                outline_switch = package.get("switch", False)
                outline_options = package.get("options", ["None"] * 9)
            except Exception:
                pass

        artist_list = []
        # artist_1 独立处理（跳过总纲包络，保留原始基础位置，默认空置则不输出）
        if artist_1 and artist_1.strip() and artist_1.strip() != "0":
            artist_list.append(artist_1.strip())
            
        extra_artists = [
            (artist_2, weight_2), (artist_3, weight_3), (artist_4, weight_4), (artist_5, weight_5),
            (artist_6, weight_6), (artist_7, weight_7), (artist_8, weight_8), (artist_9, weight_9), (artist_10, weight_10)
        ]
        
        if outline_switch:
            # 当开关打开，从 artist_2 开始应用大纲包络
            outline_artist_elements = []
            for i, (art_name, weight) in enumerate(extra_artists):
                if art_name and art_name.strip() and art_name.strip() != "0":
                    opt = outline_options[i] if i < len(outline_options) else "None"
                    if opt and opt != "None":
                        # 格式化样式：Character design:(@nakamura takeshi:0.6)
                        outline_artist_elements.append(f"{opt}:({art_name.strip()}:{weight:.2f})")
                    else:
                        outline_artist_elements.append(f"({art_name.strip()}:{weight:.2f})")
            
            if outline_artist_elements:
                # 拼接生成形如 [Character design:(@nakamura takeshi:0.6), Lineart:(@zhibuji loom:0.6)].
                artists_str = "[" + ", ".join(outline_artist_elements) + "]."
            else:
                artists_str = ""
                
            if artist_list:
                artists_str = ", ".join(artist_list) + ". " + artists_str
        else:
            # 如果总纲开关关闭，回退到原始的标准无包络格式
            for art_name, weight in extra_artists:
                if art_name and art_name.strip() and art_name.strip() != "0":
                    artist_list.append(f"({art_name.strip()}:{weight:.2f})")
            artists_str = ", ".join(artist_list)
            if artists_str:
                artists_str += "."

        if artists_str and not artists_str.endswith(" "):
            artists_str += " "
            
        fixed_template = artists_str
        
        if upstream_text and upstream_text.strip():
            final_prompt = f"{fixed_template}{upstream_text.strip()}"
        else:
            final_prompt = fixed_template.strip()
            
        return (final_prompt,)


# =====================================================================
# 🧩 节点 2：Anima 2B Prompt Template 2 (核心标签、评分与自定义文本 - 100% 保持您原文件不变)
# =====================================================================

class Anima2BPromptTemplate2Node:
    def __init__(self):
        pass
        
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "character_from": ("STRING", {"default": "hololive"}),
                "character_from_switch": ("BOOLEAN", {"default": True}),
                
                "style_tags": ("STRING", {
                    "multiline": True, 
                    "default": "crisp lines, smooth semi-realistic shading, ray tracing, translucent hair, detailed eyes, masterfully composed light, subtle gloss on lips, high contrast vignette."
                }),
                "style_tags_switch": ("BOOLEAN", {"default": True}),
                
                "year": ("STRING", {"default": "2021"}),
                "year_switch": ("BOOLEAN", {"default": True}),
                
                "quality_tags": ("STRING", {"multiline": True, "default": "newest, masterpiece, best quality"}),
                "quality_tags_switch": ("BOOLEAN", {"default": True}),
                
                "score_a": ("INT", {"default": 8, "min": 1, "max": 10, "step": 1}),
                "score_a_switch": ("BOOLEAN", {"default": True}),
                
                "score_b": ("INT", {"default": 7, "min": 1, "max": 10, "step": 1}),
                "score_b_switch": ("BOOLEAN", {"default": True}),
                
                "custom_text": ("STRING", {"multiline": True, "default": ""}),
                "custom_text_switch": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "template1_text": ("STRING", {"forceInput": True}), 
                "upstream_text": ("STRING", {"forceInput": True}),  
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "build_prompt"
    CATEGORY = "PromptHelper"

    def build_prompt(self, character_from, character_from_switch, style_tags, style_tags_switch, 
                     year, year_switch, quality_tags, quality_tags_switch, score_a, score_a_switch, 
                     score_b, score_b_switch, custom_text, custom_text_switch, template1_text="", upstream_text=""):
        
        # 1. 角色来源：规范化冒号与句尾空格
        char_from_str = f"The character is from: {character_from.strip()}. " if (character_from_switch and character_from and character_from.strip()) else ""
        
        # 2. 风格标签：使用正则把所有逗号后面都强制补上单个空格，并确保句尾以句号加空格结束
        if style_tags_switch and style_tags and style_tags.strip():
            s_tags = style_tags.strip()
            s_tags = re.sub(r',\s*', ', ', s_tags)
            if not s_tags.endswith(('.', ',', ';')):
                s_tags = s_tags + ". "
            else:
                s_tags = s_tags.rstrip() + " "
        else:
            s_tags = ""
            
        # 3. 年代标签
        year_str = f"year {year.strip()}, " if (year_switch and year and year.strip()) else ""
        
        # 4. 质量标签【彻底修复】：强制清洗内部的所有逗号，确保全部带有“逗号+空格”
        if quality_tags_switch and quality_tags and quality_tags.strip():
            q_tags = quality_tags.strip()
            q_tags = re.sub(r',\s*', ', ', q_tags)
            
            if not q_tags.endswith(('.', ',')):
                q_tags = q_tags + ", "
            else:
                q_tags = q_tags.rstrip() + " "
        else:
            q_tags = ""

        # 5. 评分标签
        score_list = []
        if score_a_switch:
            score_list.append(f"score_{score_a}")
        if score_b_switch:
            score_list.append(f"score_{score_b}")
        scores_str = ", ".join(score_list) + ". " if score_list else ""
        
        # 6. 自定义文本：同样引入内部逗号规范化
        c_text = custom_text.strip() if (custom_text_switch and custom_text and custom_text.strip()) else ""
        if c_text:
            c_text = re.sub(r',\s*', ', ', c_text)
            if not c_text.endswith(('.', ',')):
                c_text = c_text + ", "
            else:
                c_text = c_text.rstrip() + " "

        # 核心格式化干净拼接
        fixed_template = f"{char_from_str}{s_tags}{year_str}{q_tags}{scores_str}{c_text}"
        final_prompt = fixed_template
        
        # 外部链接段落的空格强化防御
        if template1_text and template1_text.strip():
            final_prompt = f"{template1_text.strip()} {final_prompt}"
            
        if upstream_text and upstream_text.strip():
            final_prompt = f"{final_prompt.strip()} {upstream_text.strip()}"
            
        return (final_prompt,)

# =====================================================================
# 🚀 ComfyUI 节点内部映射字典 (已追加新节点类)
# =====================================================================

NODE_CLASS_MAPPINGS = {
    "Anima2BArtistPreConfigOutline": Anima2BArtistPreConfigOutlineNode,
    "Anima2BPromptTemplate1": Anima2BPromptTemplate1Node,
    "Anima2BPromptTemplate2": Anima2BPromptTemplate2Node
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Anima2BArtistPreConfigOutline": "Anima 2B Artist Pre-Config Outline",
    "Anima2BPromptTemplate1": "Anima 2B Prompt Template 1",
    "Anima2BPromptTemplate2": "Anima 2B Prompt Template 2"
}