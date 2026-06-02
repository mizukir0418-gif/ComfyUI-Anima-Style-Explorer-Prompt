import { app } from "../../../scripts/app.js";

// 辅助函数：根据节点位置精准找出其所在的 Group（组）
function getGroupOfNode(node) {
    if (!node || !node.graph) return null;
    const groups = node.graph._groups || [];
    const x = node.pos[0];
    const y = node.pos[1];
    for (const group of groups) {
        if (x >= group.pos[0] && x <= (group.pos[0] + group.size[0]) &&
            y >= group.pos[1] && y <= (group.pos[1] + group.size[1])) {
            return group;
        }
    }
    return null;
}

// 辅助函数：控制整个 Group 内部所有节点的启用状态
function setGroupBypassState(graph, group, bypass) {
    if (!group || !graph) return;
    const nodesInGroup = graph._nodes.filter(node => {
        const x = node.pos[0];
        const y = node.pos[1];
        return (x >= group.pos[0] && x <= (group.pos[0] + group.size[0]) &&
                y >= group.pos[1] && y <= (group.pos[1] + group.size[1]));
    });
    for (const node of nodesInGroup) {
        if (node.type === "AnimaDynamicGroupSwitch") continue; // 跳过自身
        // mode 0 = Active (开启), mode 4 = Bypass (变灰关闭)
        node.mode = bypass ? 4 : 0; 
    }
}

app.registerExtension({
    name: "Anima.AnimaDynamicGroupSwitch",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "AnimaDynamicGroupSwitch") {
            
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                if (onNodeCreated) onNodeCreated.apply(this, arguments);
                
                // ➕ 按钮：增加风格插槽
                this.addWidget("button", "➕ Add Style Slot", null, () => {
                    const currentSlots = this.inputs ? this.inputs.length : 0;
                    if (currentSlots < 30) {
                        const nextIdx = currentSlots + 1;
                        this.addInput(`text_${nextIdx}`, "STRING");
                        this.updateGroupLabels();
                    }
                });
                
                // ➖ 按钮：减少风格插槽
                this.addWidget("button", "➖ Remove Style Slot", null, () => {
                    const currentSlots = this.inputs ? this.inputs.length : 0;
                    if (currentSlots > 1) {
                        this.removeInput(currentSlots - 1);
                        this.updateGroupLabels();
                    }
                });

                if (!this.inputs || this.inputs.length === 0) {
                    this.addInput("text_1", "STRING");
                }
                
                this.updateGroupLabels();
            };

            // 核心刷新：更新插槽名称与原生选择框选项
            nodeType.prototype.updateGroupLabels = function () {
                if (!this.inputs || !this.graph) return;
                
                let comboOptions = [];
                
                for (let i = 0; i < this.inputs.length; i++) {
                    const inputSlot = this.inputs[i];
                    const inputName = `text_${i + 1}`;
                    inputSlot.name = inputName; 
                    
                    let groupName = "Unconnected";
                    
                    if (inputSlot.link !== null) {
                        const link = this.graph.links[inputSlot.link];
                        if (link) {
                            const originNode = this.graph.getNodeById(link.origin_id);
                            const group = getGroupOfNode(originNode);
                            if (group) {
                                groupName = group.title || "Untitled Group";
                            }
                        }
                    }
                    
                    inputSlot.label = `${inputName} [${groupName}]`;
                    comboOptions.push(`${i + 1}: ${groupName}`);
                }
                
                // 🌟 直接更新纯正原生选择框的下拉列表值
                const switchWidget = this.widgets.find(w => w.name === "active_style");
                if (switchWidget) {
                    switchWidget.options.values = comboOptions;
                    if (!comboOptions.includes(switchWidget.value)) {
                        switchWidget.value = comboOptions[0] || "";
                    }
                }
                
                this.setSize(this.computeSize());
                this.setDirtyCanvas(true, true);
            };

            // 一键执行组的亮起/变灰控制
            nodeType.prototype.applyGroupBypassLogic = function (selectedValue) {
                if (!this.graph || !this.inputs || !selectedValue) return;
                
                const activeIdx = parseInt(String(selectedValue).split(":")[0]);
                if (isNaN(activeIdx)) return;
                
                for (let i = 0; i < this.inputs.length; i++) {
                    const inputSlot = this.inputs[i];
                    if (inputSlot.link !== null) {
                        const link = this.graph.links[inputSlot.link];
                        if (link) {
                            const originNode = this.graph.getNodeById(link.origin_id);
                            const group = getGroupOfNode(originNode);
                            if (group) {
                                const shouldBypass = (i + 1) !== activeIdx;
                                setGroupBypassState(this.graph, group, shouldBypass);
                            }
                        }
                    }
                }
                this.setDirtyCanvas(true, true);
            };

            // 监听连线变动
            const onConnectionsChange = nodeType.prototype.onConnectionsChange;
            nodeType.prototype.onConnectionsChange = function () {
                if (onConnectionsChange) onConnectionsChange.apply(this, arguments);
                setTimeout(() => { 
                    this.updateGroupLabels(); 
                    const switchWidget = this.widgets.find(w => w.name === "active_style");
                    if (switchWidget) this.applyGroupBypassLogic(switchWidget.value);
                }, 50);
            };

            // 工作流初次加载完毕时强制刷新
            const onConfigure = nodeType.prototype.onConfigure;
            nodeType.prototype.onConfigure = function () {
                if (onConfigure) onConfigure.apply(this, arguments);
                setTimeout(() => { 
                    this.updateGroupLabels(); 
                    const switchWidget = this.widgets.find(w => w.name === "active_style");
                    if (switchWidget) this.applyGroupBypassLogic(switchWidget.value);
                }, 150);
            };

            // 用户点击下拉菜单切换选项时激活
            const onWidgetChanged = nodeType.prototype.onWidgetChanged;
            nodeType.prototype.onWidgetChanged = function (name, value) {
                if (onWidgetChanged) onWidgetChanged.apply(this, arguments);
                if (name === "active_style") {
                    this.applyGroupBypassLogic(value);
                }
            };
        }
    }
});