import logging

class AnimaDynamicGroupSwitchNode:
    def __init__(self):
        pass
        
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                # 🌟 关键点1：恢复为原生的 COMBO 列表类型。这样前端会自动渲染出完美的、可以点击弹出的选择框
                "active_style": (["1: Unconnected"],),
            },
            "optional": {
                # 支持 1-30 个风格文本通道
                f"text_{i}": ("STRING", {"forceInput": True}) for i in range(1, 31)
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "execute_switch"
    CATEGORY = "Anima2B"

    @classmethod
    def VALIDATE_INPUTS(s, **kwargs):
        # 🌟 关键点2：ComfyUI 官方高级接口。只要返回 True，后端就会放行所有前端动态生成的选项
        # 彻底解决 Value not in list 的死板报错，同时百分百保留原生下拉选择框功能
        return True

    def execute_switch(self, active_style, **kwargs):
        try:
            # 从 "2: cool color palette" 中切出通道数字 2
            idx = int(str(active_style).split(":")[0])
        except Exception:
            idx = 1
            
        target_key = f"text_{idx}"
        selected_text = kwargs.get(target_key, "")
        return (selected_text,)