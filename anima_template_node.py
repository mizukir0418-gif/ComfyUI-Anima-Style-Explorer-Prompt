import os
import re
import socket
import ipaddress
import uuid
import urllib.parse
import aiohttp
import aiohttp.abc
from aiohttp import web
from server import PromptServer
import folder_paths

# =====================================================================
# 🛡️ 安全防御核心辅助函数
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
# 🌐 跨域安全下载路由注册
# =====================================================================

MAX_SIZE = 30 * 1024 * 1024  # 硬限制最大 30MB

@PromptServer.instance.routes.post("/anima/upload_url")
async def upload_url_route(request):
    """
    黑科技安全路由：接收前端拖拽的网页 URL 并安全下载到本地 input 文件夹
    """
    temp_target_path = None
    try:
        # 【关卡 1】解析前端请求
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

        # 【关卡 2】一次性获取并深度审计 IPv4/IPv6 地址
        is_safe, safe_ips = verify_and_get_safe_ips(hostname)
        if not is_safe:
            return web.json_response({"success": False, "error": "安全防御：禁止访问内网或解析异常"}, status=403)
            
        input_dir = folder_paths.get_input_directory()

        # 【关卡 3】提取原始文件名并加上 .downloading 安全锁
        original_filename = os.path.basename(parsed_url.path)
        if not original_filename or "." not in original_filename:
            original_filename = f"anima_drag_{uuid.uuid4().hex[:8]}.png"

        temp_target_path = os.path.join(input_dir, original_filename + ".downloading")
        
        # 【关卡 4】物理绝对路径死锁判定 (防路径穿越)
        if not os.path.abspath(temp_target_path).startswith(os.path.abspath(input_dir)):
            return web.json_response({"success": False, "error": "安全防御：检测到路径穿越攻击"}, status=403)

        # 【关卡 5】【核心黑科技】构造死锁 DNS 绑定解析器
        # 强行让 aiohttp 在后续请求中只能使用我们刚刚验证过的安全 IP，绝不允许它重新查 DNS 
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

        # 将死锁解析器注入自定义连接器，同时禁用 DNS 缓存防止污染
        connector = aiohttp.TCPConnector(resolver=PinResolver(), use_dns_cache=False)

        # 【关卡 6】使用安全连接器发起流式下载
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(url, timeout=10) as response:
                if response.status != 200:
                    return web.json_response({"success": False, "error": f"HTTP {response.status}"}, status=400)

                # 预防性检查 Content-Length
                content_length = response.headers.get("Content-Length")
                if content_length and int(content_length) > MAX_SIZE:
                    return web.json_response({"success": False, "error": "文件体积超出30MB限制"}, status=400)

                # 真实数据流硬截断
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

        # 【关卡 7】下载完成后，立即进行 DNA 级别的魔术字节审计
        actual_type = verify_image_dna(temp_target_path)
        if not actual_type:
            if os.path.exists(temp_target_path):
                os.remove(temp_target_path)
            return web.json_response({"success": False, "error": "安全拦截：该文件伪装成图片格式，实际上不是真正的图片！"}, status=400)

        # 【关卡 8】安全后缀修正与自增防覆盖逻辑
        name_without_ext, _ = os.path.splitext(original_filename)
        expected_ext = ".jpg" if actual_type == "jpeg" else f".{actual_type}"
        
        final_filename = f"{name_without_ext}{expected_ext}"
        final_target_path = os.path.join(input_dir, final_filename)
        
        # 防覆盖：如果存在同名文件，自动追加计数后缀
        counter = 1
        while os.path.exists(final_target_path):
            final_filename = f"{name_without_ext}_{counter:05d}{expected_ext}"
            final_target_path = os.path.join(input_dir, final_filename)
            counter += 1

        # 将临时文件重命名为最终的安全文件
        os.rename(temp_target_path, final_target_path)

        return web.json_response({"success": True, "name": final_filename})

    except Exception as e:
        # 容错处理：如果中途出错，销毁损坏的下载中文件
        if temp_target_path and os.path.exists(temp_target_path):
            try:
                os.remove(temp_target_path)
            except Exception:
                pass
        return web.json_response({"success": False, "error": f"下载或安全审计失败: {str(e)}"}, status=500)


# =====================================================================
# 🧩 ComfyUI 提示词核心节点逻辑
# =====================================================================

class AnimaPromptTemplateNode:
    def __init__(self):
        pass
        
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "artist_1": ("STRING", {"default": "@modare"}),
                "artist_2": ("STRING", {"default": "@mako \\(makoda\\)"}),
                "weight_2": ("FLOAT", {"default": 0.8, "min": 0.0, "max": 2.0, "step": 0.05}),
                "artist_3": ("STRING", {"default": "@mocha \\(cotton\\)"}),
                "weight_3": ("FLOAT", {"default": 0.35, "min": 0.0, "max": 2.0, "step": 0.05}),
                "artist_4": ("STRING", {"default": "@nana kagura"}),
                "weight_4": ("FLOAT", {"default": 0.8, "min": 0.0, "max": 2.0, "step": 0.05}),
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
                "character_from": ("STRING", {"default": "hololive"}),
                "style_tags": ("STRING", {
                    "multiline": True, 
                    "default": "crisp lines, smooth semi-realistic shading, ray tracing, translucent hair, detailed eyes, masterfully composed light, subtle gloss on lips, high contrast vignette."
                }),
                "year": ("STRING", {"default": "2021"}),
                "quality_tags": ("STRING", {"multiline": True, "default": "newest, masterpiece, best quality"}),
                "score_a": ("INT", {"default": 8, "min": 1, "max": 10, "step": 1}),
                "score_b": ("INT", {"default": 7, "min": 1, "max": 10, "step": 1}),
            },
            "optional": {
                "upstream_text": ("STRING", {"forceInput": True}), 
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "build_prompt"
    CATEGORY = "PromptHelper"

    def build_prompt(self, artist_1, artist_2, weight_2, artist_3, weight_3, artist_4, weight_4, artist_5, weight_5, 
                     artist_6, weight_6, artist_7, weight_7, artist_8, weight_8, artist_9, weight_9, artist_10, weight_10, 
                     character_from, style_tags, year, quality_tags, score_a, score_b, upstream_text=""):
        
        artist_list = []
        if artist_1 and artist_1.strip() and artist_1.strip() != "0":
            artist_list.append(artist_1.strip())
            
        extra_artists = [
            (artist_2, weight_2), (artist_3, weight_3), (artist_4, weight_4), (artist_5, weight_5),
            (artist_6, weight_6), (artist_7, weight_7), (artist_8, weight_8), (artist_9, weight_9), (artist_10, weight_10)
        ]
        
        for art_name, weight in extra_artists:
            if art_name and art_name.strip() and art_name.strip() != "0":
                artist_list.append(f"({art_name.strip()}:{weight:.2f})")
                
        artists_str = ",".join(artist_list)
        if artists_str:
            artists_str += ","

        char_from_str = f"The character is from:{character_from.strip()}." if character_from.strip() else ""
        s_tags = style_tags.strip()
        year_str = f"year {year.strip()}," if year.strip() else ""
        
        q_tags = quality_tags.strip()
        if q_tags and not q_tags.endswith(','):
            q_tags = q_tags + ","

        scores_str = f"score_{score_a},score_{score_b}."
        fixed_template = f"{artists_str}{char_from_str}{s_tags}{year_str}{q_tags}{scores_str}"
        
        if upstream_text and upstream_text.strip():
            final_prompt = f"{fixed_template}{upstream_text.strip()}"
        else:
            final_prompt = fixed_template
            
        return (final_prompt,)