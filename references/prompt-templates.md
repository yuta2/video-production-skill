# Slides Prompt 模板系統

> 根據選擇的風格，自動套入對應的 prompt 結構。
> 使用方式：寫 slides_prompts.json 時，只需寫每張投影片的內容骨架，
> 風格前綴和後綴由模板自動附加。

## 風格 A：黑板手繪 (blackboard)

**適用場景：** 教學影片、技術解說、概念說明
**生圖模型：** gpt-image-2 或 gemini-3.1-flash-image

### 模板

```
白底手繪教學風，教授板書風格。主標題用超大粗黑體繁體中文寫「{title}」副標「{subtitle}」。{illustration}。所有中文字必須完全正確、清楚可讀、不可有亂碼或錯字。不要出現任何未指定的文字或圖案。
```

### 欄位說明
- `{title}`：主標題（大字，5-10 字）
- `{subtitle}`：副標（小字，10-20 字）
- `{illustration}`：插畫描述（如「左下角畫一個小機器人頭上冒出問號」或「中間畫一個盾牌寫 IMMUNE」）

### 範例
```
白底手繪教學風，教授板書風格。主標題用超大粗黑體繁體中文寫「記憶過載」副標「三十份交接檔，全讀要半小時」。下方畫一堆文件堆成小山，旁邊寫「過期」「不準」「蒸發」。所有中文字必須完全正確、清楚可讀、不可有亂碼或錯字。不要出現任何未指定的文字或圖案。
```

---

## 風格 B：小愛麗絲手繪水彩 (alice-watercolor)

**適用場景：** 夜話、溫馨敘事、個人故事
**生圖模型：** gemini-3.1-flash-image（推薦）或 gpt-image-2
**風格檔：** `~/Desktop/ALICE風格/xiao_alice_storybook_watercolor_global_style.yaml`

### 模板

```
Cozy hand-drawn watercolor storybook infographic, warm parchment paper background, soft brown hand-drawn lines, warm amber and cream palette with storybook blue accents.

Header on a cream scroll banner: 「{title}」
Blue ribbon subtitle: 「{subtitle}」

{illustration}

Lower left: cute chibi Xiao Alice (小愛麗絲) with gentle smile, holding a quill pen.
Clear, readable Traditional Chinese text. No garbled characters. No text beyond what is specified.
所有中文字必須完全正確、清楚可讀、不可有亂碼或錯字。不要出現任何未指定的文字或圖案。
```

### 欄位說明
- `{title}`：主標題（放在奶油色捲軸 banner 上）
- `{subtitle}`：副標（放在藍色絲帶上）
- `{illustration}`：畫面中央的圖像描述（可為空字串）

### 範例
```
Cozy hand-drawn watercolor storybook infographic, warm parchment paper background, soft brown hand-drawn lines, warm amber and cream palette with storybook blue accents.

Header on a cream scroll banner: 「記憶過載」
Blue ribbon subtitle: 「三十份交接檔，全讀要半小時」

A pile of old parchment documents stacked like a small mountain, some with faded ink, surrounded by tiny floating labels reading "過期" "不準" "蒸發" in soft brown ink.

Lower left: cute chibi Xiao Alice (小愛麗絲) with gentle smile, holding a quill pen.
Clear, readable Traditional Chinese text. No garbled characters. No text beyond what is specified.
所有中文字必須完全正確、清楚可讀、不可有亂碼或錯字。不要出現任何未指定的文字或圖案。
```

---

## 使用原則

1. `{illustration}` 是從 narration 內容轉化的視覺元素——**一張投影片一個核心畫面**，不要塞多個主題
2. 每張投影片的 `{title}` 必須是 narration 該段的濃縮（3-8 字）
3. 風格 B 的小愛麗絲不需每張都寫——模板已自動附加
4. 否定約束永遠放結尾，不可省略
