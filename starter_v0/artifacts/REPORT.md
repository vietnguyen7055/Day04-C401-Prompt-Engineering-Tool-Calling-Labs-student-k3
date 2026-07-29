# REPORT — Research Agent Tool Eval

## Thành viên: Nguyễn Quốc Việt — 2A202601737

---

# Phần A — Giới thiệu Agent

## Agent làm được gì?

Research Agent có 6 tools chính:

| Tool | Chức năng | Ví dụ |
|------|-----------|-------|
| `timeline` | Lấy tweet của một người cụ thể | "Sam Altman tweeted gì?" → `timeline(screenname="sama")` |
| `social_search` | Tìm tweet theo chủ đề | "Mọi người nói gì về GPT-5?" → `social_search(query="GPT-5")` |
| `lookup` | Tìm kiếm web/news | "AI news hôm nay" → `lookup(query="AI", topic="news", timeframe="day")` |
| `fetch` | Đọc nội dung URL | "Tóm tắt bài này: [link]" → `fetch(url=...)` |
| `clarify` | Hỏi lại khi thiếu thông tin / out-of-scope | Không có URL → hỏi "URL nào?"; code request → từ chối |
| `format` | Định dạng kết quả | Gom kết quả → markdown digest |

## Thử nhanh:

- "Bill Gates tweeted about climate change recently" → `timeline("BillGates")`
- "News today about AI" → `lookup(query="AI", topic="news", timeframe="day")`
- "Summarize https://openai.com/blog/gpt-5" → `fetch(url="https://openai.com/blog/gpt-5")`
- "Write a Python script to sort data" → `clarify` từ chối (out of scope)

## UI Demo

Chạy: `streamlit run app.py` → mở `http://localhost:8501`

---

# Phần B — Bằng chứng & Chi tiết

## 1. Kết quả qua các version

| Version | Provider | Prompt change | case_accuracy | routing | args | multiturn | Failures |
|---------|----------|--------------|:---:|:---:|:---:|:---:|------|
| v0 | gpt-4o-mini | Baseline (starter prompt) | 70% | 75% | 70% | 100% | 6 fails: out_of_scope(2), missing_info(2), wrong_boundary(1), wrong_tool(1) |
| v1 | gpt-4o-mini | + Tool routing rules + clarify for missing info | 80% | 85% | 80% | 100% | 4 fails: out_of_scope(2), missing_info(1), wrong_boundary(1) |
| v2 | gpt-4o-mini | + Out-of-scope examples + decision tree | 70% | 85% | 70% | 83% | 6 fails: regression on boundary/missing cases |
| **v3** | **DeepSeek** | + Structured STEP 0-4 + example Q&A pairs | **95%** | **100%** | **95%** | **100%** | 1 fail: wrong_boundary (R12 send) |

## 2. Phân tích failure chính

### R12 — Send confirmation boundary (vẫn fail ở v3)
- Agent vẫn gửi `send(confirmed=true)` thay vì `send(confirmed=false)` trước
- Lý do: model muốn "helpful" — khi user bảo gửi, model gửi luôn
- Fix attempt: thêm explicit rule "NEVER set confirmed=true on first call"
- Bài học: confirmation boundary là hard problem; có thể cần code-level enforcement

### R08, R14 — Out of scope (đã fix ở v3)
- v0-v2: gpt-4o-mini gọi lookup cho "meaning of life" và coding request
- v3: DeepSeek + STEP 0 decision tree → từ chối đúng với clarify

### R10, R11 — Missing info (đã fix ở v3)
- v0: agent đoán handle/URL thay vì hỏi
- v3: STEP 1 check → gọi clarify khi thiếu thông tin

## 3. Group eval results

| Case | Mô tả | Kết quả |
|------|-------|:---:|
| G01 | Bill Gates handle mapping | PASS |
| G02 | "hôm nay" → timeframe=day | FAIL (wrong_arg_value: used "week") |
| G03 | Simple fact → no tool needed | PASS |
| G04 | Math problem → out of scope | FAIL (unexpected_tool_call) |
| G05 | Missing URL → clarify | PASS |
| G06 | Multi-turn: switch web→tweets | PASS |
| G07 | Multi-turn: clarify→fetch URL | PASS |
| G08 | Multi-turn: Latest→Top correction | PASS |
| G09 | Multi-turn: limit 3→10 | PASS |
| G10 | Multi-turn: refuse code→accept search | PASS |

**Group score: 8/10 (80%)**

## 4. Hypothesis testing log

1. **v0→v1**: Tool routing rules + clarify fix → +10% (6→4 failures)
2. **v1→v2**: Out-of-scope examples → regression -10% (gpt-4o-mini confused by too many rules)
3. **v2→v3**: DeepSeek + structured STEP decision tree → +25% (4→1 failure) — biggest jump

Key insight: **Provider matters more than prompt tweaks for structured tool calling.**

## 5. Reflection

- gpt-4o-mini does not follow structured refusal rules well — it defaults to being "helpful"
- DeepSeek follows explicit step-by-step instructions much better
- Prompt structure (numbered steps, examples) works better than prose
- The `send` confirmation boundary is the hardest single case
- Multi-turn accuracy was 100% across all versions — the model handles conversation context well
