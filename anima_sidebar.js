import { app } from "../../scripts/app.js";

let sidebar = null;
let iframe = null;

// 🍞 优雅的全局微型提示框（Toast）- 非阻塞，绝对安全
function showToast(message) {
    let toast = document.getElementById('anima-toast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'anima-toast';
        toast.style = "position: fixed; bottom: 20px; right: 440px; background: rgba(37, 99, 235, 0.95); color: #fff; padding: 10px 18px; border-radius: 6px; z-index: 100000; transition: opacity 0.3s, transform 0.3s; font-size: 13px; font-weight: 500; box-shadow: 0 4px 12px rgba(0,0,0,0.3); transform: translateY(0);";
        document.body.appendChild(toast);
    }
    toast.innerText = message;
    toast.style.opacity = '1';
    setTimeout(() => { toast.style.opacity = '0'; }, 2300);
}

function createAnimaSidebar() {
    if (sidebar) return;

    // 1. 创建主侧边栏容器
    sidebar = document.createElement("div");
    sidebar.id = "anima-style-explorer-sidebar";
    sidebar.style.position = "fixed";
    sidebar.style.right = "0";
    sidebar.style.top = "0";
    sidebar.style.width = "420px";
    sidebar.style.height = "100%";
    sidebar.style.zIndex = "9999";
    sidebar.style.background = "#1c1c1f";
    sidebar.style.boxShadow = "-5px 0 25px rgba(0,0,0,0.6)";
    sidebar.style.transition = "transform 0.25s ease-in-out";
    sidebar.style.transform = "translateX(100%)";
    sidebar.style.display = "flex";
    sidebar.style.flexDirection = "column";
    sidebar.style.borderLeft = "2px solid #3f3f46";

    // 2. 头部标题
    const header = document.createElement("div");
    header.style.display = "flex";
    header.style.justifyContent = "space-between";
    header.style.alignItems = "center";
    header.style.padding = "10px 15px";
    header.style.background = "#27272a";
    header.style.borderBottom = "1px solid #3f3f46";
    header.style.color = "#ffffff";
    header.style.fontSize = "13px";
    header.style.fontWeight = "bold";
    header.innerText = "Anima Style Explorer";

    const closeBtn = document.createElement("button");
    closeBtn.innerText = "✕";
    closeBtn.style.background = "none";
    closeBtn.style.border = "none";
    closeBtn.style.color = "#a1a1aa";
    closeBtn.style.cursor = "pointer";
    closeBtn.onclick = () => { sidebar.style.transform = "translateX(100%)"; };
    header.appendChild(closeBtn);
    sidebar.appendChild(header);

    // 3. 搜索与控制面板
    const searchPanel = document.createElement("div");
    searchPanel.style.display = "flex";
    searchPanel.style.flexDirection = "column";
    searchPanel.style.gap = "8px";
    searchPanel.style.padding = "10px 15px";
    searchPanel.style.background = "#141416";
    searchPanel.style.borderBottom = "2px solid #27272a";

    const inputLabel = document.createElement("label");
    inputLabel.innerText = "📋 智能流控制器 (点击上方原作者图片可激活复制)";
    inputLabel.style.color = "#a1a1aa";
    inputLabel.style.fontSize = "11px";
    searchPanel.appendChild(inputLabel);

    // 第一排按钮：外网检索
    const btnContainer = document.createElement("div");
    btnContainer.style.display = "flex";
    btnContainer.style.gap = "10px";

    async function performSmartSearch(targetSite) {
        try {
            const clipboardText = await navigator.clipboard.readText();
            let searchUrl = targetSite === "dobooru" ? "https://danbooru.donmai.us/" : "https://e-hentai.org/";
            if (clipboardText && clipboardText.trim() !== "") {
                // 🛡️ 【安全符号洗涤器】彻底干掉开头的 @ 和所有地方的反斜杠 \
                let baseCleanName = clipboardText.replace(/^@/, "").replace(/\\/g, "").trim();
                if (targetSite === "dobooru") {
                    let cleanNameDB = baseCleanName.replace(/\s+/g, "_");
                    searchUrl = `https://danbooru.donmai.us/posts?tags=${encodeURIComponent(cleanNameDB)}`;
                } else {
                    searchUrl = `https://e-hentai.org/?f_search=${encodeURIComponent(baseCleanName)}`;
                }
            }

            const screenWidth = window.screen.availWidth;
            const screenHeight = window.screen.availHeight;
            const winWidth = Math.floor(screenWidth * 0.35);
            const winHeight = screenHeight;
            const left = screenWidth - winWidth;
            const top = 0;

            const windowFeatures = `width=${winWidth},height=${winHeight},left=${left},top=${top},resizable=yes,scrollbars=yes,location=yes,status=yes`;
            window.Danbooru_E_Hentai_SplitWindow = window.open(searchUrl, "Danbooru_E_Hentai_SplitWindow", windowFeatures);
        } catch (err) {
            showToast("❌ 读取剪贴板失败，请确保浏览器已授权剪贴板读取权限！");
        }
    }

    const btnDobooru = document.createElement("button");
    btnDobooru.innerHTML = "🔍 Danbooru 搜索";
    btnDobooru.style = "flex: 1; background: #2563eb; color: #ffffff; border: none; padding: 6px 0; border-radius: 4px; cursor: pointer; font-size: 12px;";
    btnDobooru.onclick = () => performSmartSearch("dobooru");

    const btnEHentai = document.createElement("button");
    btnEHentai.innerHTML = "🔍 E-Hentai 搜索";
    btnEHentai.style = "flex: 1; background: #059669; color: #ffffff; border: none; padding: 6px 0; border-radius: 4px; cursor: pointer; font-size: 12px;";
    btnEHentai.onclick = () => performSmartSearch("e-hentai");

    btnContainer.appendChild(btnDobooru);
    btnContainer.appendChild(btnEHentai);
    searchPanel.appendChild(btnContainer);

    // 第二排按钮：自动寻轨填入 ComfyUI 节点
    const btnFillNode = document.createElement("button");
    btnFillNode.innerHTML = "✍️ 将已复制画师自动填入选中节点";
    btnFillNode.style = "width: 100%; background: #eab308; color: #1c1c1f; border: none; padding: 7px 0; border-radius: 4px; cursor: pointer; font-weight: bold; font-size: 12px; margin-top: 2px; transition: background 0.2s;";
    btnFillNode.onmouseenter = () => btnFillNode.style.background = "#ca8a04";
    btnFillNode.onmouseleave = () => btnFillNode.style.background = "#eab308";
    btnFillNode.onclick = async () => {
        try {
            const clipboardText = await navigator.clipboard.readText();
            if (!clipboardText || clipboardText.trim() === "") {
                showToast("⚠️ 剪贴板里空空如也，请先点击下方的风格图片！");
                return;
            }

            const canvas = app.canvas;
            if (!canvas || !canvas.selected_nodes || Object.keys(canvas.selected_nodes).length === 0) {
                showToast("⚠️ 请先在画布上鼠标点击选中你的 Anima 节点！");
                return;
            }

            for (const nodeId in canvas.selected_nodes) {
                const node = canvas.selected_nodes[nodeId];
                // 🔄 此处已修改：只针对新拆分出来的 Template 1 节点生效
                if (node.comfyClass === "Anima2BPromptTemplate1") {
                    let isFilled = false;
                    for (let i = 1; i <= 10; i++) {
                        const widget = node.widgets.find(w => w.name === `artist_${i}`);
                        if (widget && (!widget.value || widget.value.trim() === "" || widget.value === "0")) {
                            widget.value = clipboardText.trim();
                            if (widget.callback) widget.callback(widget.value);
                            isFilled = true;
                            showToast(`✨ 成功填入槽位 artist_${i}: ${widget.value}`);
                            break;
                        }
                    }
                    if (!isFilled) {
                        const widget = node.widgets.find(w => w.name === "artist_1");
                        if (widget) {
                            widget.value = clipboardText.trim();
                            if (widget.callback) widget.callback(widget.value);
                            showToast(`🔥 槽位已满，已强行覆盖 artist_1: ${widget.value}`);
                        }
                    }
                    canvas.draw(true, true);
                    return;
                }
            }
            showToast("⚠️ 当前选中的节点不是 Anima 提示词模板 1 节点！");
        } catch (err) {
            showToast("❌ 无法读取剪贴板，请检查浏览器权限");
        }
    };
    searchPanel.appendChild(btnFillNode);
    sidebar.appendChild(searchPanel);

    // 4. 原作者风格浏览器嵌套
    iframe = document.createElement("iframe");
    iframe.src = "https://thetacursed.github.io/Anima-Style-Explorer/";
    iframe.setAttribute("allow", "clipboard-read; clipboard-write"); 
    iframe.style.width = "100%";
    iframe.style.height = "calc(100% - 135px)";
    iframe.style.border = "none";
    iframe.style.background = "#ffffff";
    sidebar.appendChild(iframe);

    document.body.appendChild(sidebar);
}

function showAnimaSidebar() {
    createAnimaSidebar();
    sidebar.style.transform = "translateX(0%)";
}

app.registerExtension({
    name: "Comfy.AnimaSidebarPlus",
    
    async setup() {
        // ⚡ 异能 1：边缘悬停自动聚焦并排外网窗口
        window.addEventListener("mousemove", (e) => {
            if (e.clientX >= window.innerWidth - 30) {
                if (window.Danbooru_E_Hentai_SplitWindow && !window.Danbooru_E_Hentai_SplitWindow.closed) {
                    window.Danbooru_E_Hentai_SplitWindow.focus();
                }
            }
        });

        // ⚡ 异能 2：清爽安全的原生图片拖拽解析器（已合并最新防护机制）
        window.addEventListener("drop", async (event) => {
            let url = event.dataTransfer.getData("text/plain") || event.dataTransfer.getData("text/uri-list");
            const html = event.dataTransfer.getData("text/html");
            
            if (html && (!url || !url.startsWith("http"))) {
                const match = html.match(/src=["'](.*?)["']/);
                if (match) {
                    url = match[1];
                }
            }
            
            if (!url || !url.startsWith("http")) return;

            const canvas = app.canvas;
            if (!canvas) return;

            const pos = canvas.convertEventToCanvasOffset({ clientX: event.clientX, clientY: event.clientY });
            const node = canvas.getNodeOnPos(pos[0], pos[1]);
            
            if (!node?.widgets) return;

            const imageWidget = node.widgets.find(w => w.name === "image");
            if (!imageWidget) return;

            event.preventDefault();
            event.stopPropagation();
            
            const oldVal = imageWidget.value;
            imageWidget.value = "⚡ 正在通过后端下载云端原图...";
            
            try {
                const response = await fetch("/anima/upload_url", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ url })
                });
                const result = await response.json();
                
                if (result.name) {
                    imageWidget.value = result.name;
                    if (imageWidget.callback) {
                        imageWidget.callback(result.name);
                    }
                    node.setSize(node.computeSize());
                    app.graph.setDirtyCanvas(true, true);
                    showToast("✅ 图片导入成功");
                } else {
                    imageWidget.value = oldVal;
                    showToast(`❌ ${result.error || "下载失败"}`);
                }
            } catch (err) {
                console.error(err);
                imageWidget.value = oldVal;
                showToast("❌ 无法连接到 ComfyUI 后端图片下载服务！");
            }
        }, true);
    },

    async nodeCreated(node) {
        // 🔄 此处已修改：让“打开风格浏览器”按钮精准渲染在新拆分出来的 Template 1 节点底部
        if (node.comfyClass === "Anima2BPromptTemplate1") {
            node.addWidget(
                "button", 
                "🌐 打开风格浏览器 (Anima Explorer)", 
                null, 
                () => {
                    showAnimaSidebar();
                }
            );
        }
    }
});