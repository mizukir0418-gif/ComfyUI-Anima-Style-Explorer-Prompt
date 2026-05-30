from .anima_template_node import Anima2BArtistPreConfigOutlineNode, Anima2BPromptTemplate1Node, Anima2BPromptTemplate2Node

# 告诉 ComfyUI 这个插件里有哪些节点类
NODE_CLASS_MAPPINGS = {
    "Anima2BArtistPreConfigOutline": Anima2BArtistPreConfigOutlineNode,
    "Anima2BPromptTemplate1": Anima2BPromptTemplate1Node,
    "Anima2BPromptTemplate2": Anima2BPromptTemplate2Node
}

# 节点在 ComfyUI 里的显示名称
NODE_DISPLAY_NAME_MAPPINGS = {
    "Anima2BArtistPreConfigOutline": "Anima 2B Artist Pre-Config Outline",
    "Anima2BPromptTemplate1": "Anima 2B Prompt Template 1",
    "Anima2BPromptTemplate2": "Anima 2B Prompt Template 2"
}

# 告诉 ComfyUI 自动加载本目录下的 js 文件夹
WEB_DIRECTORY = "./js"

# ⚠️ 注意下面是双下怀线 __all__
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']