from .anima_template_node import AnimaPromptTemplateNode

# 告诉 ComfyUI 这个插件里有哪些节点类
NODE_CLASS_MAPPINGS = {
    "AnimaPromptTemplateNode": AnimaPromptTemplateNode
}

# 节点在 ComfyUI 里的显示名称
NODE_DISPLAY_NAME_MAPPINGS = {
    "AnimaPromptTemplateNode": "Anima 2B Prompt Template"
}

# 告诉 ComfyUI 自动加载本目录下的 js 文件夹
WEB_DIRECTORY = "./js"

# ⚠️ 注意下面是双下划线 __all__
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']