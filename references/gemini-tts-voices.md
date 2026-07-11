# Gemini TTS 聲音選用指南

> 以下聲音均為 Gemini 3.1 Flash TTS (gemini-3.1-flash-tts-preview) 原生支援。
> 輸出為 PCM l16 24kHz mono，需 ffmpeg 轉 MP3 後使用。

## 聲音分類

| Voice | 特質 | 適用場景 |
|-------|------|----------|
| **Kore** | 溫潤、從容、像在講床邊故事 | 夜話、歐麗娟語氣、有哲思的長篇敘事 |
| **Lyra** | 輕柔、自然、像朋友聊天 | 日常對話、講故事、有聲書、生活分享 |
| **Vega** | 明亮、親切、帶教學感 | 日常宣導、教學影片、知識科普 |
| **Zephyr** | 端莊、正式、專業但不冷 | 公司影片、正式場合、品牌介紹 |
| **Nova** | 中性、溫和、不特別女性化 | 非女聲場景、中性配音、備用 |

## 快速對照

| 影片語氣 | 推薦聲音 |
|----------|----------|
| 夜話 / 歐麗娟語氣 / 哲思 | Kore |
| 日常對話 / 有聲書 / 說故事 | Lyra |
| 教學 / 科普 / 宣導 | Vega |
| 公司 / 正式 / 品牌 | Zephyr |

## 技術備註

- 必須用 `speechConfig.voiceConfig.prebuiltVoiceConfig.voiceName` 指定聲音
- 輸出 mime: `audio/l16; rate=24000; channels=1`
- 轉 MP3: `ffmpeg -f s16le -ar 24000 -ac 1 -i raw.l16 -codec:a libmp3lame -b:a 128k output.mp3`
- 成本：$1/1M input tokens（純文字，超便宜）
