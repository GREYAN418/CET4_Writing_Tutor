import os
import json
import streamlit as st
from datetime import datetime, date
from openai import OpenAI
from typing import Dict, List, Optional
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 初始化 OpenAI 客户端（使用阿里云 Qwen-Max）
# 支持 DASHSCOPE_API_KEY 或 OPENAI_API_KEY 环境变量
api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("请设置环境变量 DASHSCOPE_API_KEY 或 OPENAI_API_KEY")

client = OpenAI(
    api_key=api_key,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

# 页面配置
st.set_page_config(
    page_title="CET4 微写作训练",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={}
)

# 隐藏顶部菜单栏
st.markdown("""
<style>
    [data-testid="stHeader"] {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

# 7 种微写作模式
WRITING_MODES = {
    0: "Sentence Correction",  # 周一
    1: "Translation",          # 周二
    2: "Word Upgrading",       # 周三
    3: "Logic Linking",        # 周四
    4: "Sentence Combining",   # 周五
    5: "Paraphrasing",         # 周六
    6: "Brainstorming"         # 周日
}

# 数据文件路径
DATA_DIR = "data"
WEAKNESS_FILE = os.path.join(DATA_DIR, "weakness_points.json")
HISTORY_FILE = os.path.join(DATA_DIR, "practice_history.json")
DAILY_QUESTION_FILE = os.path.join(DATA_DIR, "daily_question.json")

# 初始化数据目录和文件
def init_data_files():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(WEAKNESS_FILE):
        with open(WEAKNESS_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=2)
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=2)
    if not os.path.exists(DAILY_QUESTION_FILE):
        with open(DAILY_QUESTION_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False, indent=2)

# 读取薄弱点数据
def load_weakness_points() -> List[Dict]:
    try:
        with open(WEAKNESS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

# 保存薄弱点数据
def save_weakness_point(point: Dict):
    points = load_weakness_points()
    points.append({
        **point,
        "timestamp": datetime.now().isoformat()
    })
    with open(WEAKNESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(points, f, ensure_ascii=False, indent=2)

# 读取历史记录
def load_history() -> List[Dict]:
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

# 保存练习记录
def save_practice(record: Dict):
    history = load_history()
    history.append({
        **record,
        "timestamp": datetime.now().isoformat()
    })
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

# 保存每日题目
def save_daily_question(date_str: str, question: Dict):
    try:
        with open(DAILY_QUESTION_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except:
        data = {}
    
    data[date_str] = {
        "question": question,
        "timestamp": datetime.now().isoformat()
    }
    
    with open(DAILY_QUESTION_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 加载每日题目
def load_daily_question(date_str: str) -> Optional[Dict]:
    try:
        with open(DAILY_QUESTION_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get(date_str, {}).get("question")
    except:
        return None

# 获取当天的练习模式
def get_today_mode() -> str:
    today = date.today().weekday()
    return WRITING_MODES[today]

# 生成题目（结合薄弱点）
def generate_question(mode: str, weakness_points: List[Dict]) -> Dict:
    weakness_context = ""
    if weakness_points:
        # 只取薄弱点类型，不发送具体内容，避免AI重复生成相似题目
        recent_points = weakness_points[-5:]
        weakness_types = set(p.get('type', '') for p in recent_points)
        weakness_context = "\n".join([
            f"- {ptype}" 
            for ptype in weakness_types
        ])
    
    mode_prompts = {
        "Sentence Correction": f"""请生成一个CET4水平的病句题目。每次生成必须完全不同，不要重复之前的题目。
要求：
1. 句子长度15-25词
2. 包含常见的语法错误（如时态、主谓一致、冠词、介词等）
3. 错误要隐蔽但有迹可循
4. 内容要多样化，涵盖学习、生活、工作等不同场景

如果用户有薄弱点，请参考以下信息针对性地出题：
{weakness_context}

返回JSON格式：
{{
    "question": "包含错误的句子",
    "error_type": "错误类型",
    "hint": "提示信息（不直接给出答案）"
}}""",
        
        "Translation": f"""请生成一个CET4水平的英译中题目。每次生成必须完全不同，不要重复之前的题目。
要求：
1. 中文句子表达常见场景（学习、生活、工作）
2. 包含2-3个重点词汇或短语
3. 适合CET4词汇水平
4. 场景要多样化，不要重复

如果用户有薄弱点，请参考以下信息针对性地出题：
{weakness_context}

返回JSON格式：
{{
    "chinese_sentence": "中文句子",
    "key_words": ["重点词1", "重点词2"],
    "hint": "提示信息"
}}""",
        
        "Word Upgrading": f"""请生成一个CET4水平的词汇升级题目。每次生成必须完全不同，不要重复之前的题目。
要求：
1. 给出一个基础词汇（如 good, bad, think 等）
2. 要求用户写出更高级的同义替换词
3. 适合CET4写作提升
4. 每次选择不同的基础词汇

如果用户有薄弱点，请参考以下信息针对性地出题：
{weakness_context}

返回JSON格式：
{{
    "basic_word": "基础词汇",
    "word_meaning": "词义",
    "hint": "提示信息（如词性、语境等）"
}}""",
        
        "Logic Linking": f"""请生成一个CET4水平的逻辑连接题目。每次生成必须完全不同，不要重复之前的题目。
要求：
1. 给出两个相关的简单句
2. 要求用户用合适的连接词合并
3. 句子内容贴近学生生活
4. 场景要多样化，不要重复

如果用户有薄弱点，请参考以下信息针对性地出题：
{weakness_context}

返回JSON格式：
{{
    "sentence1": "句子1",
    "sentence2": "句子2",
    "hint": "提示可能的连接词类型"
}}""",
        
        "Sentence Combining": f"""请生成一个CET4水平的句子合并题目。每次生成必须完全不同，不要重复之前的题目。
要求：
1. 给出2-3个简单短句
2. 要求学生合并成一个复合句
3. 包含定语从句、状语从句等CET4句型
4. 场景要多样化，不要重复

如果用户有薄弱点，请参考以下信息针对性地出题：
{weakness_context}

返回JSON格式：
{{
    "sentences": ["句子1", "句子2", "句子3（可选）"],
    "target_structure": "目标句型（如定语从句）",
    "hint": "提示信息"
}}""",
        
        "Paraphrasing": f"""请生成一个CET4水平的改写题目。每次生成必须完全不同，不要重复之前的题目。
要求：
1. 给出一个表达清晰的句子
2. 要求学生换一种方式表达相同意思
3. 使用不同的词汇或句式
4. 句子内容要多样化，不要重复

如果用户有薄弱点，请参考以下信息针对性地出题：
{weakness_context}

返回JSON格式：
{{
    "original_sentence": "原句",
    "hint": "提示信息（如可以使用的同义词或句型）"
}}""",
        
        "Brainstorming": f"""请生成一个CET4水平的头脑风暴题目。每次生成必须完全不同，不要重复之前的题目。
要求：
1. 给出一个常见的话题（如环保、学习、健康等）
2. 要求学生列出3个相关论点
3. 适合写作练习
4. 话题要多样化，不要重复

如果用户有薄弱点，请参考以下信息针对性地出题：
{weakness_context}

返回JSON格式：
{{
    "topic": "话题",
    "topic_background": "话题背景说明",
    "hint": "提示可能的思考角度"
}}"""
    }
    
    prompt = mode_prompts.get(mode, mode_prompts["Sentence Correction"])
    
    try:
        response = client.chat.completions.create(
            model="qwen-max",
            messages=[
                {"role": "system", "content": "你是一个专业的英语教学助手，专门帮助CET4学生提升写作能力。请严格按照JSON格式返回。每次生成题目时都要确保内容完全不同，不要重复。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.9,
            max_tokens=500
        )
        
        content = response.choices[0].message.content.strip()
        # 清理可能的 markdown 代码块标记
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        
        return json.loads(content)
    except Exception as e:
        st.error(f"生成题目失败: {str(e)}")
        return None

# 批改用户答案
def evaluate_answer(mode: str, question: Dict, user_answer: str) -> Dict:
    mode_prompts = {
        "Sentence Correction": f"""请批改以下句子改写题目。

原句（包含错误）：{question.get('question', '')}
错误类型：{question.get('error_type', '')}
用户答案：{user_answer}

你是我同桌，用轻松亲切的口吻批改，多鼓励。给出正确答案和高分表达。如果答案正确，details 可以为空数组。

返回JSON格式：
{{
    "summary": "整体评价",
    "is_correct": true/false,
    "correct_answer": "正确答案",
    "high_score_expression": "高分表达",
    "details": []
}}""",
        
        "Translation": f"""请批改以下翻译题目。

中文句子：{question.get('chinese_sentence', '')}
重点词汇：{', '.join(question.get('key_words', []))}
用户答案：{user_answer}

你是我同桌，用轻松亲切的口吻批改，多鼓励。给出参考译文和高分表达。如果答案正确，details 可以为空数组。

返回JSON格式：
{{
    "summary": "整体评价",
    "is_correct": true/false,
    "reference_translation": "参考译文",
    "high_score_expression": "高分表达",
    "details": []
}}""",
        
        "Word Upgrading": f"""请批改以下词汇升级题目。

基础词汇：{question.get('basic_word', '')}
词义：{question.get('word_meaning', '')}
用户答案：{user_answer}

你是我同桌，用轻松亲切的口吻批改，多鼓励。给出更多高级同义词和使用示例。如果答案正确，details 可以为空数组。

返回JSON格式：
{{
    "summary": "整体评价",
    "is_correct": true/false,
    "suggested_words": ["高级词1", "高级词2"],
    "high_score_expression": "使用示例",
    "details": []
}}""",
        
        "Logic Linking": f"""请批改以下逻辑连接题目。

句子1：{question.get('sentence1', '')}
句子2：{question.get('sentence2', '')}
用户答案：{user_answer}

你是我同桌，用轻松亲切的口吻批改，多鼓励。给出参考答案和更多连接词选择。如果答案正确，details 可以为空数组。

返回JSON格式：
{{
    "summary": "整体评价",
    "is_correct": true/false,
    "reference_answer": "参考答案",
    "high_score_expression": "更多连接词",
    "details": []
}}""",
        
        "Sentence Combining": f"""请批改以下句子合并题目。

原句：{', '.join(question.get('sentences', []))}
目标句型：{question.get('target_structure', '')}
用户答案：{user_answer}

你是我同桌，用轻松亲切的口吻批改，多鼓励。给出参考答案和其他合并方式。如果答案正确，details 可以为空数组。

返回JSON格式：
{{
    "summary": "整体评价",
    "is_correct": true/false,
    "reference_answer": "参考答案",
    "high_score_expression": "其他方式",
    "details": []
}}""",
        
        "Paraphrasing": f"""请批改以下改写题目。

原句：{question.get('original_sentence', '')}
用户答案：{user_answer}

你是我同桌，用轻松亲切的口吻批改，多鼓励。给出参考改写和更好的改写方式。如果答案正确，details 可以为空数组。

返回JSON格式：
{{
    "summary": "整体评价",
    "is_correct": true/false,
    "reference_paraphrase": "参考改写",
    "high_score_expression": "更好的方式",
    "details": []
}}""",
        
        "Brainstorming": f"""请批改以下头脑风暴题目。

话题：{question.get('topic', '')}
用户答案：{user_answer}

你是我同桌，用轻松亲切的口吻批改，多鼓励。给出更多论点建议和高分论点示例。如果答案正确，details 可以为空数组。

返回JSON格式：
{{
    "summary": "整体评价",
    "is_correct": true/false,
    "suggested_points": ["论点1", "论点2"],
    "high_score_expression": "高分论点",
    "details": []
}}"""
    }
    
    prompt = mode_prompts.get(mode, mode_prompts["Sentence Correction"])
    
    try:
        response = client.chat.completions.create(
            model="qwen-max",
            messages=[
                {"role": "system", "content": "你是一个专业的英语教学助手，专门帮助CET4学生提升写作能力。请严格按照JSON格式返回。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )
        
        content = response.choices[0].message.content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        
        result = json.loads(content)
        
        # 保存薄弱点
        if result.get("details"):
            for detail in result["details"]:
                save_weakness_point({
                    "type": detail.get("type", ""),
                    "issue": detail.get("issue", ""),
                    "correction": detail.get("correction", ""),
                    "mode": mode
                })
        
        return result
    except Exception as e:
        st.error(f"批改失败: {str(e)}")
        return None

# AI 助手对话
def ask_ai_assistant(question: str) -> str:
    try:
        response = client.chat.completions.create(
            model="qwen-max",
            messages=[
                {"role": "system", "content": "你是一个友好的英语学习助手，专门帮助CET4学生解答英语学习问题（非作文批改类）。请用简洁、鼓励的语气回答。"},
                {"role": "user", "content": question}
            ],
            temperature=0.7,
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"抱歉，我遇到了一些问题：{str(e)}"

# 侧边栏
def sidebar():
    with st.sidebar:
        # 标题
        st.markdown(
            """
            <div style='text-align: center; padding: 10px 0 5px 0;'>
                <h1 style='margin: 0; color: #1f77b4; font-size: 32px;'>✍️</h1>
                <h2 style='margin: 5px 0 0 0; font-size: 20px;'>CET4 微写作</h2>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        st.markdown("---")
        
        # 页面导航 - 使用自定义样式
        st.markdown("<h3 style='font-size: 14px; margin-bottom: 10px;'>📚 页面导航</h3>", unsafe_allow_html=True)
        
        # 获取当前页面
        if "current_page" not in st.session_state:
            st.session_state.current_page = "练习页"
        
        page = st.session_state.current_page
        
        # 自定义导航按钮 - 竖向排版
        if st.button("📝 练习页", use_container_width=True, key="nav_practice"):
            st.session_state.current_page = "练习页"
            st.rerun()
        
        if st.button("📊 薄弱点页", use_container_width=True, key="nav_weakness"):
            st.session_state.current_page = "薄弱点页"
            st.rerun()
        
        if st.button("📜 历史记录", use_container_width=True, key="nav_history"):
            st.session_state.current_page = "历史记录"
            st.rerun()
        
        # Ask AI 按钮
        if st.button("🤖 AI 提问", use_container_width=True, type="primary"):
            st.session_state.show_ai_dialog = True
        
        st.markdown("---")
        
        # 显示当前练习模式
        st.markdown("<h3 style='font-size: 14px; margin-bottom: 10px;'>📅 今日信息</h3>", unsafe_allow_html=True)
        today_mode = get_today_mode()
        st.info(f"**练习模式：** {today_mode}")
        
        st.markdown("<h3 style='font-size: 14px; margin-bottom: 10px;'>📊 练习统计</h3>", unsafe_allow_html=True)
        
        # 显示练习统计
        history = load_history()
        weakness_points = load_weakness_points()
        
        # 计算正确率 - 修复 evaluation 为 None 的 bug
        correct_count = sum(1 for h in history if h.get("evaluation") and h.get("evaluation", {}).get("is_correct"))
        accuracy = round(correct_count / len(history) * 100, 1) if history else 0
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("总练习", len(history))
        with col2:
            st.metric("正确率", f"{accuracy}%")
        
        st.metric("薄弱点", len(weakness_points))
    
    return page

# 练习页面
def practice_page():
    st.header(f"📝 今日练习：{get_today_mode()}")
    st.markdown("---")
    
    # 初始化会话状态
    if "question" not in st.session_state:
        st.session_state.question = None
    if "user_answer" not in st.session_state:
        st.session_state.user_answer = ""
    if "evaluation" not in st.session_state:
        st.session_state.evaluation = None
    if "submitted" not in st.session_state:
        st.session_state.submitted = False
    
    # 获取今天的日期
    today = date.today().isoformat()
    
    # 首次加载时，从本地读取今日题目（如果存在）
    if not st.session_state.question:
        saved_question = load_daily_question(today)
        if saved_question:
            st.session_state.question = saved_question
    
    # 生成题目按钮（显示在题目上方，用于首次生成）
    if not st.session_state.question:
        if st.button("🎲 生成今日题目", type="primary", use_container_width=True):
            with st.spinner("正在生成题目..."):
                weakness_points = load_weakness_points()
                question = generate_question(get_today_mode(), weakness_points)
                if question:
                    st.session_state.question = question
                    # 保存到本地
                    save_daily_question(today, question)
    
    # 显示题目
    if st.session_state.question:
        q = st.session_state.question
        
        st.subheader("📋 题目")
        
        mode = get_today_mode()
        if mode == "Sentence Correction":
            st.info(f"**病句：** {q.get('question', '')}")
            st.caption(f"💡 提示：{q.get('hint', '')}")
            st.caption(f"🔍 错误类型：{q.get('error_type', '')}")
        
        elif mode == "Translation":
            st.info(f"**中文句子：** {q.get('chinese_sentence', '')}")
            st.caption(f"💡 提示：{q.get('hint', '')}")
            st.caption(f"🔑 重点词汇：{', '.join(q.get('key_words', []))}")
        
        elif mode == "Word Upgrading":
            st.info(f"**基础词汇：** {q.get('basic_word', '')}")
            st.caption(f"📖 词义：{q.get('word_meaning', '')}")
            st.caption(f"💡 提示：{q.get('hint', '')}")
        
        elif mode == "Logic Linking":
            st.info(f"**句子1：** {q.get('sentence1', '')}")
            st.info(f"**句子2：** {q.get('sentence2', '')}")
            st.caption(f"💡 提示：{q.get('hint', '')}")
        
        elif mode == "Sentence Combining":
            st.info(f"**句子：**")
            for i, sent in enumerate(q.get('sentences', []), 1):
                st.write(f"{i}. {sent}")
            st.caption(f"🎯 目标句型：{q.get('target_structure', '')}")
            st.caption(f"💡 提示：{q.get('hint', '')}")
        
        elif mode == "Paraphrasing":
            st.info(f"**原句：** {q.get('original_sentence', '')}")
            st.caption(f"💡 提示：{q.get('hint', '')}")
        
        elif mode == "Brainstorming":
            st.info(f"**话题：** {q.get('topic', '')}")
            st.caption(f"📝 话题背景：{q.get('topic_background', '')}")
            st.caption(f"💡 提示：{q.get('hint', '')}")
        
        st.markdown("---")
        
        # 用户输入
        if not st.session_state.submitted:
            st.subheader("✍️ 你的答案")
            user_answer = st.text_area(
                "请输入你的答案：",
                value=st.session_state.user_answer,
                height=150,
                placeholder="在这里输入你的答案..."
            )
            
            # 提交按钮
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.button("提交答案", type="primary", use_container_width=True):
                    if user_answer.strip():
                        with st.spinner("正在批改..."):
                            st.session_state.evaluation = evaluate_answer(
                                mode,
                                st.session_state.question,
                                user_answer
                            )
                            st.session_state.submitted = True
                            
                            # 保存练习记录
                            save_practice({
                                "mode": mode,
                                "question": st.session_state.question,
                                "user_answer": user_answer,
                                "evaluation": st.session_state.evaluation
                            })
                    else:
                        st.warning("请先输入你的答案！")
            
            with col2:
                if st.button("🔄 刷新题目", use_container_width=True):
                    with st.spinner("正在刷新题目..."):
                        weakness_points = load_weakness_points()
                        question = generate_question(get_today_mode(), weakness_points)
                        if question:
                            st.session_state.question = question
                            st.session_state.user_answer = ""
                            st.session_state.evaluation = None
                            st.session_state.submitted = False
                            st.rerun()
            
            with col3:
                if st.button("🗑️ 清空输入", use_container_width=True):
                    st.session_state.user_answer = ""
                    st.rerun()
        
        # 显示批改结果
        if st.session_state.submitted and st.session_state.evaluation:
            st.markdown("---")
            st.subheader("📊 批改结果")
            
            eval_result = st.session_state.evaluation
            
            # 整体评价
            st.success(eval_result.get("summary", ""))
            
            # 是否正确
            if eval_result.get("is_correct"):
                st.balloons()
            
            # 参考答案
            if "correct_answer" in eval_result:
                st.info(f"✅ **正确答案：** {eval_result['correct_answer']}")
            elif "reference_translation" in eval_result:
                st.info(f"✅ **参考译文：** {eval_result['reference_translation']}")
            elif "reference_answer" in eval_result:
                st.info(f"✅ **参考答案：** {eval_result['reference_answer']}")
            elif "reference_paraphrase" in eval_result:
                st.info(f"✅ **参考改写：** {eval_result['reference_paraphrase']}")
            
            # 高分表达
            if "high_score_expression" in eval_result:
                st.warning(f"⭐ **高分表达：** {eval_result['high_score_expression']}")
            
            # 建议词汇
            if "suggested_words" in eval_result:
                st.warning(f"📚 **建议词汇：** {', '.join(eval_result['suggested_words'])}")
            
            # 建议论点
            if "suggested_points" in eval_result:
                st.warning(f"💡 **建议论点：**")
                for i, point in enumerate(eval_result["suggested_points"], 1):
                    st.write(f"{i}. {point}")
            
            # 详细反馈
            if eval_result.get("details"):
                st.markdown("---")
                st.subheader("🔍 详细反馈")
                for detail in eval_result["details"]:
                    with st.expander(f"❌ {detail.get('type', '')}问题"):
                        st.error(f"**问题：** {detail.get('issue', '')}")
                        st.success(f"**建议：** {detail.get('correction', '')}")
            
            # 继续练习按钮
            st.markdown("---")
            if st.button("🔄 继续练习", type="primary", use_container_width=True):
                st.session_state.question = None
                st.session_state.user_answer = ""
                st.session_state.evaluation = None
                st.session_state.submitted = False
                st.rerun()

# 薄弱点页面
def weakness_page():
    st.header("📊 薄弱点分析")
    st.markdown("---")
    
    weakness_points = load_weakness_points()
    
    if not weakness_points:
        st.info("还没有薄弱点记录，加油练习吧！")
        return
    
    # 按类型统计
    type_counts = {}
    for point in weakness_points:
        ptype = point.get("type", "其他")
        type_counts[ptype] = type_counts.get(ptype, 0) + 1
    
    st.subheader("📈 薄弱点分布")
    col1, col2 = st.columns(2)
    with col1:
        for ptype, count in type_counts.items():
            st.metric(ptype, count)
    
    with col2:
        if type_counts:
            st.bar_chart(type_counts)
    
    # 详细列表
    st.markdown("---")
    st.subheader("📝 薄弱点详情")
    
    # 按模式分组
    mode_groups = {}
    for point in weakness_points:
        mode = point.get("mode", "其他")
        if mode not in mode_groups:
            mode_groups[mode] = []
        mode_groups[mode].append(point)
    
    for mode, points in mode_groups.items():
        with st.expander(f"📌 {mode} ({len(points)}个)"):
            for i, point in enumerate(points, 1):
                st.markdown(f"**{i}. {point.get('type', '')}**")
                st.write(f"❌ 问题：{point.get('issue', '')}")
                st.write(f"✅ 建议：{point.get('correction', '')}")
                st.caption(f"🕐 时间：{point.get('timestamp', '')}")
                st.markdown("---")

# 历史记录页面
def history_page():
    st.header("📜 练习历史")
    st.markdown("---")
    
    history = load_history()
    
    if not history:
        st.info("还没有练习记录，开始练习吧！")
        return
    
    # 统计信息
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("总练习次数", len(history))
    with col2:
        # 计算正确率 - 修复 evaluation 为 None 的 bug
        correct_count = sum(1 for h in history if h.get("evaluation") and h.get("evaluation", {}).get("is_correct"))
        accuracy = round(correct_count / len(history) * 100, 1) if history else 0
        st.metric("正确率", f"{accuracy}%")
    with col3:
        # 练习模式分布
        mode_counts = {}
        for h in history:
            mode = h.get("mode", "其他")
            mode_counts[mode] = mode_counts.get(mode, 0) + 1
        most_common = max(mode_counts.items(), key=lambda x: x[1])[0] if mode_counts else "无"
        st.metric("最常练习", most_common)
    
    st.markdown("---")
    
    # 按日期分组显示
    date_groups = {}
    for record in reversed(history):
        timestamp = record.get("timestamp", "")
        date_str = timestamp.split("T")[0] if timestamp else "未知日期"
        if date_str not in date_groups:
            date_groups[date_str] = []
        date_groups[date_str].append(record)
    
    for date_str, records in date_groups.items():
        with st.expander(f"📅 {date_str} ({len(records)}条记录)"):
            for i, record in enumerate(records, 1):
                mode = record.get("mode", "")
                question = record.get("question", {})
                user_answer = record.get("user_answer", "")
                evaluation = record.get("evaluation", {})
                
                st.markdown(f"**{i}. {mode}**")
                
                # 显示题目
                if mode == "Sentence Correction":
                    st.info(f"题目：{question.get('question', '')}")
                elif mode == "Translation":
                    st.info(f"题目：{question.get('chinese_sentence', '')}")
                elif mode == "Word Upgrading":
                    st.info(f"题目：{question.get('basic_word', '')} - {question.get('word_meaning', '')}")
                elif mode == "Logic Linking":
                    st.info(f"题目：{question.get('sentence1', '')} + {question.get('sentence2', '')}")
                elif mode == "Sentence Combining":
                    sentences = question.get('sentences', [])
                    st.info(f"题目：{' + '.join(sentences)}")
                elif mode == "Paraphrasing":
                    st.info(f"题目：{question.get('original_sentence', '')}")
                elif mode == "Brainstorming":
                    st.info(f"话题：{question.get('topic', '')}")
                
                # 显示用户答案
                st.write(f"✍️ 你的答案：{user_answer}")
                
                # 显示评价
                if evaluation:
                    summary = evaluation.get("summary", "")
                    is_correct = evaluation.get("is_correct", False)
                    
                    if is_correct:
                        st.success(f"✅ {summary}")
                    else:
                        st.warning(f"⚠️ {summary}")
                
                st.caption(f"🕐 时间：{record.get('timestamp', '')}")
                st.markdown("---")

# AI 助手对话框
def ai_assistant_dialog():
    if st.session_state.get("show_ai_dialog", False):
        st.markdown("---")
        st.subheader("🤖 AI 助手")
        
        st.write("有什么英语学习问题吗？我可以帮你解答（非作文批改类）")
        
        question = st.text_area(
            "请输入你的问题：",
            height=100,
            placeholder="例如：如何正确使用 'affect' 和 'effect'？",
            key="ai_question"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("发送", type="primary", key="ai_send"):
                if question.strip():
                    with st.spinner("思考中..."):
                        answer = ask_ai_assistant(question)
                    st.session_state.ai_answer = answer
                else:
                    st.warning("请输入问题！")
        
        with col2:
            if st.button("关闭", key="ai_close"):
                st.session_state.show_ai_dialog = False
                st.session_state.ai_answer = None
                st.rerun()
        
        # 显示 AI 回答
        if st.session_state.get("ai_answer"):
            st.success(st.session_state.ai_answer)

# 主函数
def main():
    init_data_files()
    
    # 侧边栏
    page = sidebar()
    
    # AI 助手对话框
    ai_assistant_dialog()
    
    # 主内容区域
    if page == "练习页":
        practice_page()
    elif page == "薄弱点页":
        weakness_page()
    elif page == "历史记录":
        history_page()

if __name__ == "__main__":
    main()