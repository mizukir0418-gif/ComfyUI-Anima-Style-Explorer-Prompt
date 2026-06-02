# ComfyUI Anima Style Explorer Prompt

A specialized ComfyUI side-panel plugin designed for exploring 2D anime-style artist prompts. It features high-security defenses, automated style interaction, seamless prompt management, and advanced macro-category wrapping.

---

## 🧩 Included Nodes (包含节点)

This plugin now provides a powerful 3-node ecosystem to fully manage your anime prompting workflow:
1. **Artist Pre-Config Outline (`AnimaArtistPreConfig`)** —— *NEW!* Manages global style categories (Character, Lineart, Painterly, etc.) and links them to artist slots.
2. **Anima 2B Prompt Template 1 (`Anima2BPromptTemplate1`)** —— *UPDATED!* Core artist prompt generator with 10 parallel artist channels (now supporting dynamic outline wrapping).
3. **Anima 2B Prompt Template 2 (`Anima2BPromptTemplate2`)** —— Standardized quality tags, style modifiers, eras, and score formatting.

---

## 🚀 Key Features

### ✨ New: Artist Pre-Config Outline (画师前置配置总纲)
* **Structural Macro Management**: Adds a dedicated controller featuring a built-in 8-point artistic outline text-box.
* **Dynamic Bracket Wrapping**: Automatically wraps raw artist tags into specific industry categories (e.g., transforming `(@mako:0.8)` into `[Lineart:(@mako:0.8)]`) based on your selection.
* **Channel-Specific Mapping**: Provides 9 separate dropdown slots corresponding directly to Artist channels 2 through 10.

### Embedded Style Explorer
* Summon a dedicated style-exploration sidebar directly within ComfyUI for a smooth browsing experience.

### Intelligent Cross-Site Search
* Automatically extracts Artist IDs from your clipboard.
* Cleans tags for Stable Diffusion (handles underscores/dashes automatically).
* Supports dual-site searching (Danbooru & E-Hentai) with one click.

### Automated Prompt Injection
* After copying an Artist ID from the sidebar, the node automatically fills it into the selected Anima Template node (Artist 1 to Artist 10).

### Industrial-Grade Security
* **Deep SSRF Defense**: Automatically resolves DNS to block internal networks, loopbacks, and cloud metadata addresses, preventing potential SSRF attacks.
* **Magic Byte Audit**: Validates image headers (Magic Bytes) to prevent malicious scripts or trojan horses disguised as images.
* **Stream Control**: Limits buffer size to 30MB to protect your disk storage.

---

## 💡 How to Use

### 1. Connecting the Pre-Config Outline (画师总纲连线)
* Add the `Artist Pre-Config Outline` node to your workspace.
* Connect its `artist_config` output port to the optional `artist_config` input port on **Anima 2B Prompt Template 1**.
* Use the dropdown menus (`artist_2_option` to `artist_10_option`) to classify each artist's role (e.g., select `Lineart` for a sketch master, or `Painterly` for a color expert). 
* *Note: `Artist 1` is kept as a raw bypass channel and will not be wrapped by the categories.*

### 2. Prompt Injection & Cleanup
* When paired with an Image Interrogator node, the node automatically injects your style tags at the beginning of the prompt. If the `character_from` field is empty, it is automatically skipped.
* **Streamlined Pipeline**: The outdated `year_top` and `year_top_switch` parameters have been fully removed from Template 1 to avoid prompt pollution.

### 3. Historical Style Adjustment
* Some artists have distinct styles across different eras (e.g., `@happoubi jin`). Use the "Era/Period" option in Template 2 to match the style to the artist's specific timeline.

### 4. Anima Style Explorer Integration
* **Search**: Use the Blue/Green buttons to search the copied Artist ID on Danbooru or E-hentai.
* **Yellow Sync Button**: First, select the `Anima-Style-Explorer-Prompt` node, click an artist image to copy the ID, then click the Yellow button to sync the ID into the text field.

> 💡 **Pro-Tip (Window Management)**: If the search window is covered by ComfyUI, click the canvas and move your mouse to the far right edge of your screen to pop it out.
> 
> 💡 **Quick Loading**: Drag images from Danbooru directly into your ComfyUI "Load Image" node.

---

## 🛠️ Installation

Open your terminal in the `ComfyUI/custom_nodes/` directory and run:

```bash
git clone https://github.com/mizukir0418-gif/ComfyUI-Anima-Style-Explorer-Prompt.git

---
workflow https://civitai.red/models/2640250?modelVersionId=2997669
