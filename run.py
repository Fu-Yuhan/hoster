"""AI智慧农业 —— Streamlit 对话界面（流式思考）"""

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

# ═══════════════════ 用户输入 & 多轮工具调用（流式） ═══════════════════

if prompt := st.chat_input("请输入您的问题…"):
    # 添加用户消息
    st.session_state.msgs.append({"role": "user", "content": prompt})

    # 最多进行 10 轮工具调用
    for _ in range(10):
        # 创建占位符用于流式显示本轮助手回复
        with st.chat_message("assistant"):
            placeholder = st.empty()

        # 发起流式请求
        try:
            stream = client.chat.completions.create(
                model=MODEL,
                messages=st.session_state.msgs,
                tools=TOOL_DEFS,
                stream=True,
            )
        except Exception as e:
            st.error(f"API 调用失败：{e}")
            st.stop()

        # 收集流式数据
        full_content = ""
        tool_calls_dict = {}  # index -> 累积的 tool_call 信息

        for chunk in stream:
            delta = chunk.choices[0].delta

            # 处理文本内容
            if delta.content:
                full_content += delta.content
                placeholder.markdown(full_content + "▌")  # 显示光标

            # 处理工具调用（可能分片）
            if delta.tool_calls:
                for tc_chunk in delta.tool_calls:
                    idx = tc_chunk.index
                    if idx not in tool_calls_dict:
                        tool_calls_dict[idx] = {
                            "id": None,
                            "name": None,
                            "arguments": ""
                        }
                    # 累积信息
                    if tc_chunk.id:
                        tool_calls_dict[idx]["id"] = tc_chunk.id
                    if tc_chunk.function and tc_chunk.function.name:
                        tool_calls_dict[idx]["name"] = tc_chunk.function.name
                    if tc_chunk.function and tc_chunk.function.arguments:
                        tool_calls_dict[idx]["arguments"] += tc_chunk.function.arguments

        # 流结束，更新占位符为最终内容（去掉光标）
        if full_content:
            placeholder.markdown(full_content)
        else:
            # 如果没有任何文本（直接调用工具），可显示一个简短提示
            placeholder.markdown("*(正在调用工具...)*")

        # 构建完整的 assistant 消息
        assistant_msg = {"role": "assistant", "content": full_content or None}
        if tool_calls_dict:
            # 按索引排序，组装成标准格式
            tool_calls = []
            for idx in sorted(tool_calls_dict.keys()):
                tc = tool_calls_dict[idx]
                tool_calls.append({
                    "id": tc["id"],
                    "type": "function",
                    "function": {
                        "name": tc["name"],
                        "arguments": tc["arguments"]
                    }
                })
            assistant_msg["tool_calls"] = tool_calls

        # 将本轮助手消息加入历史
        st.session_state.msgs.append(assistant_msg)

        # 如果没有工具调用，结束本轮对话
        if not tool_calls_dict:
            break

        # 执行所有工具调用
        for tc in tool_calls:
            fn_name = tc["function"]["name"]
            fn_args = json.loads(tc["function"]["arguments"])
            result = call_tool(fn_name, fn_args)

            # 记录工具名（用于渲染时显示）
            st.session_state.tool_names[tc["id"]] = fn_name

            # 将工具结果加入历史
            st.session_state.msgs.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": result,
            })

        # 继续下一轮（让模型根据工具结果继续思考）

    # 所有轮次结束后刷新页面，显示完整对话（包括工具结果）
    st.rerun()