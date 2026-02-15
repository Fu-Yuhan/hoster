"""AI智慧农业 —— Streamlit 对话界面"""

import os, json
import streamlit as st
from openai import OpenAI
from tools import TOOL_DEFS, call_tool, init_db

# ═══════════════════ 初始化 ═══════════════════

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

init_db()

API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
BASE_URL = os.environ.get("API_BASE", "https://api.deepseek.com")
MODEL    = os.environ.get("MODEL", "deepseek-chat")   # DeepSeek-V3

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

SYSTEM = """你是「农智」—— AI 智慧农业助手。
你管理的农场分为 东北、西北、东南、西南 四个区域，每个区域配有温度、湿度、CO₂、光照传感器。

你的能力：
1. 查询任意区域的实时传感器数据或历史趋势
2. 查看某区域所有传感器概览
3. 对指定区域浇水（需指定水量）
4. 读写系统操作日志

请根据传感器数据给出专业农业建议。始终使用中文回复。"""

# ═══════════════════ 页面 ═══════════════════

st.set_page_config(page_title="🌾 AI智慧农业", page_icon="🌾")
st.title("🌾 AI 智慧农业助手")

with st.sidebar:
    st.header("ℹ️ 系统信息")
    st.markdown(
        "**区域** 东北 · 西北 · 东南 · 西南\n\n"
        "**传感器** 温度 · 湿度 · CO₂ · 光照\n\n"
        "**操作** 浇水 · 日志读写"
    )
    st.divider()
    if st.button("🗑️ 清空对话", use_container_width=True):
        st.session_state.clear()
        st.rerun()

if not API_KEY:
    st.error("⚠️ 请设置环境变量 `DEEPSEEK_API_KEY`，或在 `.env` 中写入。")
    st.stop()

# ═══════════════════ 会话状态 ═══════════════════

if "msgs" not in st.session_state:
    st.session_state.msgs = [{"role": "system", "content": SYSTEM}]
    st.session_state.tool_names = {}          # tool_call_id → 函数名

# ═══════════════════ 渲染历史消息 ═══════════════════

for m in st.session_state.msgs:
    role = m["role"]
    content = m.get("content")

    if role == "user":
        st.chat_message("user").write(content)

    elif role == "assistant" and content:
        st.chat_message("assistant").write(content)

    elif role == "tool":
        name = st.session_state.tool_names.get(m.get("tool_call_id"), "工具")
        with st.chat_message("assistant", avatar="🔧"):
            with st.expander(f"📊 {name}", expanded=False):
                try:
                    st.json(json.loads(content))
                except Exception:
                    st.code(content)

# 引导提示
if len(st.session_state.msgs) == 1:
    st.caption("💡 试试：「查看东南区概况」「东北区过去6小时温度趋势」「给西北区浇水30升」「查看操作日志」")

# ═══════════════════ 用户输入 & 多轮工具调用 ═══════════════════

if prompt := st.chat_input("请输入您的问题…"):
    st.session_state.msgs.append({"role": "user", "content": prompt})

    with st.spinner("🌱 分析中…"):
        for _ in range(10):                        # 最多 10 轮工具调用
            try:
                resp = client.chat.completions.create(
                    model=MODEL,
                    messages=st.session_state.msgs,
                    tools=TOOL_DEFS,
                )
            except Exception as e:
                st.error(f"API 调用失败：{e}")
                st.stop()

            msg = resp.choices[0].message

            # ── 序列化 assistant 消息 ──
            entry: dict = {"role": "assistant", "content": msg.content}
            if msg.tool_calls:
                entry["tool_calls"] = [
                    {"id": tc.id, "type": "function",
                     "function": {"name": tc.function.name,
                                  "arguments": tc.function.arguments}}
                    for tc in msg.tool_calls
                ]
            st.session_state.msgs.append(entry)

            if not msg.tool_calls:
                break

            # ── 执行每个工具 ──
            for tc in msg.tool_calls:
                fn_name = tc.function.name
                fn_args = json.loads(tc.function.arguments)
                result  = call_tool(fn_name, fn_args)

                st.session_state.tool_names[tc.id] = fn_name
                st.session_state.msgs.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                })

    st.rerun()