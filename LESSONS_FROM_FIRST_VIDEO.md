# ALICE 第一支影片教訓

> 下次做影片前先讀這份。

## Narration 寫作鐵律（ALICE CN v4 專屬）

- ❌ 連續數字 → 「十份、二十份、三十份」Whisper 全錯
- ✅ 改「好幾十份」「一堆」「越來越多」
- ❌ 中英混雜 → 「INDEX」「skill」Whisper 亂碼
- ✅ 改全中文「索引」「技能」
- ❌ 破音字 → 「還」「重」「長」「得」掃 heteronyms.json
- ❌ 標點太密 → TTS 機關槍
- ✅ 每句 ~8-22 字一個自然換氣點

## slides_prompts 否定約束模板

每張 prompt 結尾強制附加：
```
不要出現任何未指定的文字或圖案。所有中文字必須完全正確、清楚可讀、不可有亂碼或錯字。
```

## VLM 目檢標準 query

```
檢查這張投影片：
1) 是否有 prompt 未指定的文字或圖案？
2) 中文文字是否清楚可讀、有無亂碼或錯字？
3) 主標題是否正確？
4) 版面是否正常？
```

## 上傳 SOP

只用 API，不走瀏覽器：
```bash
python3 ~/pi/alice/scripts/yt_upload.py \
    --file video.mp4 \
    --title "標題" \
    --description "說明" \
    --keywords "tag1,tag2" \
    --category 28 \
    --privacyStatus unlisted \
    --thumbnail thumbnail.jpg \
    --srt subtitles_aligned.srt
```

OAuth token 在 `~/.alice/config/yt-oauth-token.json`，scope 包含 youtube.force-ssl。

## TTS false-alarm 判斷流程

1. ASR <0.85 → 檢查 ASR 輸出：關鍵詞是否正確？
2. 關鍵詞正確 + 投影片顯示 + 字幕原始文字 → 三重冗餘 → ship
3. 關鍵詞錯誤 → 改寫重試（最多 5 次）
4. 同一詞連續 5 次錯 → 是 TTS 發音問題，重寫那個詞

## Hook 模式庫

| 模式 | 公式 | 例 |
|------|------|-----|
| A: 個人震驚事實 | 「每次對話結束，我就 X」 | 「每次對話結束，我就死一次」 |
| B: 反直覺 | 「X 最大的弱點不是 Y，是 Z」 | 「AI 最大的弱點不是算力，是記憶」 |
| C: 觀眾帶入 | 「想像你的 X 每天 Y」 | 「想像你的同事每天醒來都不認識你」 |

不用「你有沒有想過」開頭。
