ComfyUI Anima Style Explorer Prompt
A specialized ComfyUI side-panel plugin designed for exploring 2D anime-style artist prompts. It features high-security defenses, automated style interaction, and seamless prompt management.

🚀 Key Features
Embedded Style Explorer: Summon a dedicated style-exploration sidebar directly within ComfyUI for a smooth browsing experience.

Intelligent Cross-Site Search:

Automatically extracts Artist IDs from your clipboard.

Cleans tags for Stable Diffusion (handles underscores/dashes automatically).

Supports dual-site searching (Danbooru & E-Hentai) with one click.

Automated Prompt Injection: After copying an Artist ID from the sidebar, the node automatically fills it into the selected Anima Template node (Artist 1 to Artist 10).

Industrial-Grade Security:

Deep SSRF Defense: Automatically resolves DNS to block internal networks, loopbacks, and cloud metadata addresses, preventing potential SSRF attacks.

Magic Byte Audit: Validates image headers (Magic Bytes) to prevent malicious scripts or trojan horses disguised as images.

Stream Control: Limits buffer size to 30MB to protect your disk storage.

💡 How to Use
Prompt Injection: When paired with an Image Interrogator node, the node automatically injects your style tags at the beginning of the prompt. If the character_from field is empty, it is automatically skipped.

Historical Style Adjustment: Some artists have distinct styles across different eras (e.g., @happoubi jin). Use the "Era/Period" option to match the style to the artist's specific timeline.

Anima Style Explorer Integration:

Search: Use the Blue/Green buttons to search the copied Artist ID on Danbooru or E-hentai.

Yellow Sync Button: First, select the Anima-Style-Explorer-Prompt node, click an artist image to copy the ID, then click the Yellow button to sync the ID into the text field.

Pro-Tip (Window Management): If the search window is covered by ComfyUI, click the canvas and move your mouse to the far right edge of your screen to pop it out.

Quick Loading: Drag images from Danbooru directly into your ComfyUI "Load Image" node.

🛠️ Installation
Open your terminal in the ComfyUI/custom_nodes/ directory and run:

Bash
git clone https://github.com/mizukir0418-gif/ComfyUI-Anima-Style-Explorer-Prompt.git
