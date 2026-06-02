from .anima_template_node import Anima2BArtistPreConfigOutlineNode, Anima2BPromptTemplate1Node, Anima2BPromptTemplate2Node
# 🌟 导入新开发的动态组切换节点
from .anima_group_switch_node import AnimaDynamicGroupSwitchNode

# 告诉 ComfyUI 这个插件里有哪些节点类
NODE_CLASS_MAPPINGS = {
    "Anima2BArtistPreConfigOutline": Anima2BArtistPreConfigOutlineNode,
    "Anima2BPromptTemplate1": Anima2BPromptTemplate1Node,
    "Anima2BPromptTemplate2": Anima2BPromptTemplate2Node,
    # 🌟 注册新节点到映射中
    "AnimaDynamicGroupSwitch": AnimaDynamicGroupSwitchNode
}

# 节点在 ComfyUI 里的显示名称
NODE_DISPLAY_NAME_MAPPINGS = {
    "Anima2BArtistPreConfigOutline": "Anima 2B Artist Pre-Config Outline",
    "Anima2BPromptTemplate1": "Anima 2B Prompt Template 1",
    "Anima2BPromptTemplate2": "Anima 2B Prompt Template 2",
    # 🌟 设定新节点在 UI 右键菜单里的漂亮大名
    "AnimaDynamicGroupSwitch": "Anima 2B Dynamic Group Switcher"
}

# 告诉 ComfyUI 自动加载本目录下的 js 文件夹
WEB_DIRECTORY = "./js"

# ⚠️ 注意下面是双下划线 __all__
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']