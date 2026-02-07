import os
import json
import streamlit as st
from datetime import datetime, date
from openai import OpenAI
from typing import Dict, List, Optional
from dotenv import load_dotenv
from supabase import create_client, Client

# 加载 .env 文件（仅用于本地开发）
load_dotenv()

# 初始化 OpenAI 客户端（使用阿里云 Qwen-Max）
# 优先使用 st.secrets，其次使用环境变量
api_key = st.secrets.get("DASHSCOPE_API_KEY") or os.getenv("DASHSCOPE_API_KEY") or st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("请设置环境变量 DASHSCOPE_API_KEY 或 OPENAI_API_KEY")

client = OpenAI(
    api_key=api_key,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

# 初始化 Supabase 客户端
supabase_url = st.secrets.get("SUPABASE_URL") or os.getenv("SUPABASE_URL")
supabase_key = st.secrets.get("SUPABASE_KEY") or os.getenv("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    raise ValueError("请设置环境变量 SUPABASE_URL 和 SUPABASE_KEY")

supabase: Client = create_client(supabase_url, supabase_key)

# 页面配置
st.set_page_config(
    page_title="CET4 微写作训练",
    page_icon=":material/edit:",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={}
)

# 引入 Material Icons 字体并定义样式
st.markdown("""
<style>
    @font-face {
        font-family: 'Material Icons';
        font-style: normal;
        font-weight: 400;
        src: url(https://fonts.gstatic.com/s/materialicons/v140/flUhRq6tzZclQEJ-Vdg-IuiaDsNc.woff2) format('woff2');
    }

    .material-icon {
        font-family: 'Material Icons';
        font-size: 18px;
        vertical-align: text-bottom;
        margin-right: 6px;
        color: inherit;
        display: inline-block;
        line-height: 1;
        height: 18px;
        width: 18px;
    }

    .material-icon-large {
        font-family: 'Material Icons';
        font-size: 40px;
        color: #66bb6a;
        display: inline-block;
        line-height: 1;
    }
</style>
""", unsafe_allow_html=True)

# 隐藏顶部菜单栏和界面元素（简洁模式）
st.markdown("""
<style>
    /* 顶栏 - 设置与主背景一致的渐变色，使其与背景融为一体 */
    [data-testid="stHeader"] {
        background: linear-gradient(135deg, #f9fbe7 0%, #f1f8e9 50%, #e8f5e9 100%) !important;
        color: #2e5a3a !important;
    }
    [data-testid="stHeader"] div, [data-testid="stHeader"] span, [data-testid="stHeader"] p, [data-testid="stHeader"] label {
        color: #2e5a3a !important;
    }

    /* 侧边栏 - 浅薄荷绿渐变 */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #e0f2f1 0%, #b2dfdb 100%) !important;
        color: #2e5a3a !important;
    }
    [data-testid="stSidebar"] div, [data-testid="stSidebar"] span, [data-testid="stSidebar"] p, [data-testid="stSidebar"] label {
        color: #2e5a3a !important;
    }

    /* 主内容区 - 极淡的晨雾绿渐变 */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #f9fbe7 0%, #f1f8e9 50%, #e8f5e9 100%) !important;
    }

    /* 主内容区域文字颜色 - 柔和的深灰绿 */
    [data-testid="stAppViewContainer"] .main,
    [data-testid="stAppViewContainer"] div,
    [data-testid="stAppViewContainer"] span,
    [data-testid="stAppViewContainer"] p,
    [data-testid="stAppViewContainer"] label {
        color: #2e5a3a !important;
    }

    /* 标题颜色 - 保持普通颜色，不使用渐变文字效果 */
    h1, h2, h3, h4, h5, h6 {
        color: #2e5a3a !important;
    }

    /* 按钮样式 - 清新薄荷绿 */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #66bb6a 0%, #81c784 100%) !important;
        border: none !important;
        box-shadow: 0 4px 12px rgba(102, 187, 106, 0.25);
        transition: all 0.3s ease;
        color: #ffffff !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #81c784 0%, #a5d6a7 100%) !important;
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(102, 187, 106, 0.35);
        color: #ffffff !important;
    }
    .stButton > button {
        color: #2e5a3a !important;
        background: #ffffff !important;
        border: 1px solid #66bb6a !important;
    }
    .stButton > button:hover {
        color: #ffffff !important;
        background: #66bb6a !important;
    }

    /* 信息框 - 清新主题 */
    [data-testid="stInfo"], .stAlert[data-baseweb="toast"] {
        background: #ffffff !important;
        border-left: 4px solid #66bb6a !important;
        color: #2e5a3a !important;
        box-shadow: 0 2px 8px rgba(102, 187, 106, 0.1);
    }
    [data-testid="stInfo"] div, [data-testid="stInfo"] span, [data-testid="stInfo"] p {
        color: #2e5a3a !important;
    }
    [data-testid="stSuccess"] {
        background: #e8f5e9 !important;
        border-left: 4px solid #81c784 !important;
        color: #2e5a3a !important;
    }
    [data-testid="stSuccess"] div, [data-testid="stSuccess"] span, [data-testid="stSuccess"] p {
        color: #2e5a3a !important;
    }
    [data-testid="stWarning"] {
        background: #fff8e1 !important;
        border-left: 4px solid #ffd54f !important;
        color: #8d6e63 !important;
    }
    [data-testid="stWarning"] div, [data-testid="stWarning"] span, [data-testid="stWarning"] p {
        color: #8d6e63 !important;
    }
    [data-testid="stError"] {
        background: #ffebee !important;
        border-left: 4px solid #e57373 !important;
        color: #c62828 !important;
    }
    [data-testid="stError"] div, [data-testid="stError"] span, [data-testid="stError"] p {
        color: #c62828 !important;
    }

    /* 统计卡片 - 薄荷绿主题 */
    [data-testid="stMetricValue"] {
        color: #66bb6a !important;
        font-weight: normal !important;
    }
    [data-testid="stMetricLabel"] {
        color: #5a8f62 !important;
    }

    /* 侧边栏导航按钮 - 浅色背景 */
    [data-testid="stSidebar"] .stButton > button {
        color: #2e5a3a !important;
        text-align: left !important;
        background: rgba(255, 255, 255, 0.5) !important;
        border: 1px solid rgba(102, 187, 106, 0.3) !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        color: #ffffff !important;
        background: #66bb6a !important;
    }
    [data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #66bb6a 0%, #81c784 100%) !important;
        border: none !important;
        color: #ffffff !important;
    }
    [data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #81c784 0%, #a5d6a7 100%) !important;
    }

    /* expander 折叠框样式 */
    .streamlit-expanderHeader {
        color: #2e5a3a !important;
    }
    [data-testid="stExpander"] div {
        color: #2e5a3a !important;
    }

    /* caption 文字颜色 */
    .stCaption {
        color: #66bb6a !important;
    }

    /* info 框内文字颜色 */
    .stInfo {
        color: #2e5a3a !important;
    }

    /* multiselect 筛选器标签 - 与侧边栏同款浅绿 */
    [data-testid="stMultiSelect"] span[data-baseweb="tag"] {
        background: #ECF6F5 !important;
        border: 1px solid rgba(102, 187, 106, 0.3) !important;
        color: #2e5a3a !important;
    }
    [data-testid="stMultiSelect"] span[data-baseweb="tag"] span {
        color: #2e5a3a !important;
    }
</style>
""", unsafe_allow_html=True)

# 7 种微写作模式
WRITING_MODES = {
    0: "Phrase Practice",      # 周一 - 短语造句
    1: "Translation",          # 周二 - 翻译
    2: "Transition Practice",  # 周三 - 过渡练习
    3: "Sentence Structure",   # 周四 - 句式练习
    4: "Sentence Variety",     # 周五 - 句式多样性
    5: "Sentence Correction",  # 周六 - 句子改错
    6: "Paraphrasing"          # 周日 - 改写
}

# 初始化数据库表（兼容本地文件系统）
def init_data_files():
    # Supabase 数据库已在外部创建，无需本地初始化
    pass

# 读取薄弱点数据
def load_weakness_points() -> List[Dict]:
    try:
        response = supabase.table("weakness_points").select("*").order("created_at", desc=True).execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"读取薄弱点失败: {str(e)}")
        return []

# 保存薄弱点数据
def save_weakness_point(point: Dict, record_id: str = None):
    try:
        supabase.table("weakness_points").insert({
            "record_id": record_id,
            "type": point.get("type"),
            "issue": point.get("issue"),
            "correction": point.get("correction"),
            "mode": point.get("mode"),
            "timestamp": datetime.now().isoformat()
        }).execute()
    except Exception as e:
        st.error(f"保存薄弱点失败: {str(e)}")

# 删除同一题目的薄弱点
def delete_weakness_points_by_record(record_id: str):
    try:
        supabase.table("weakness_points").delete().eq("record_id", record_id).execute()
    except Exception as e:
        st.error(f"删除薄弱点失败: {str(e)}")

# 读取历史记录
def load_history() -> List[Dict]:
    try:
        response = supabase.table("practice_history").select("*").order("created_at", desc=True).execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"读取历史记录失败: {str(e)}")
        return []

# 保存练习记录
def save_practice(record: Dict, update_record_id: str = None):
    try:
        if update_record_id:
            # 更新已有记录
            supabase.table("practice_history").update({
                "mode": record.get("mode"),
                "question": record.get("question"),
                "user_answer": record.get("user_answer"),
                "evaluation": record.get("evaluation"),
                "timestamp": record.get("timestamp", datetime.now().isoformat())
            }).eq("record_id", update_record_id).execute()
        else:
            # 创建新记录
            record["record_id"] = f"{datetime.now().timestamp()}"
            record["timestamp"] = datetime.now().isoformat()
            supabase.table("practice_history").insert({
                "record_id": record["record_id"],
                "mode": record.get("mode"),
                "question": record.get("question"),
                "user_answer": record.get("user_answer"),
                "evaluation": record.get("evaluation"),
                "timestamp": record["timestamp"]
            }).execute()
    except Exception as e:
        st.error(f"保存练习记录失败: {str(e)}")

# 保存每日题目
def save_daily_question(date_str: str, question: Dict):
    try:
        # 检查是否已存在
        response = supabase.table("daily_questions").select("*").eq("date_str", date_str).execute()
        if response.data:
            # 更新
            supabase.table("daily_questions").update({
                "question": question,
                "timestamp": datetime.now().isoformat()
            }).eq("date_str", date_str).execute()
        else:
            # 插入
            supabase.table("daily_questions").insert({
                "date_str": date_str,
                "question": question,
                "timestamp": datetime.now().isoformat()
            }).execute()
    except Exception as e:
        st.error(f"保存每日题目失败: {str(e)}")

# 加载每日题目
def load_daily_question(date_str: str) -> Optional[Dict]:
    try:
        response = supabase.table("daily_questions").select("*").eq("date_str", date_str).execute()
        if response.data and len(response.data) > 0:
            return response.data[0].get("question")
        return None
    except Exception as e:
        st.error(f"加载每日题目失败: {str(e)}")
        return None

# 获取当天的练习模式
def get_today_mode() -> str:
    today = date.today().weekday()
    return WRITING_MODES[today]

# 生成题目
def generate_question(mode: str, weakness_points: List[Dict] = None) -> Dict:
    mode_prompts = {
        "Phrase Practice": f"""请生成一个CET4水平的短语造句题目。每次生成必须完全不同，不要重复之前的题目。
要求：
1. 给出1-2个CET4写作常用短语或搭配（如：in addition、as a result、pay attention to等）
2. 要求学生用给定的短语造句
3. 短语场景要多样化，涵盖学习、生活、工作、环境等不同主题
4. 每次选择不同的短语
5. 建议作答时间：3-5分钟
6. 造句约10-20词

返回JSON格式：
{{
    "phrases": ["短语1", "短语2（可选）"],
    "hint": "提示信息（可以给一个造句场景或主题建议）"
}}""",

        "Translation": f"""请生成一个CET4水平的英译中题目。每次生成必须完全不同，不要重复之前的题目。
要求：
1. 中文句子表达常见场景（学习、生活、工作）
2. 包含2-3个重点词汇或短语
3. 适合CET4词汇水平
4. 场景要多样化，不要重复
5. 建议作答时间：5-8分钟
6. 翻译后英文约15-25词

返回JSON格式：
{{
    "chinese_sentence": "中文句子",
    "key_words": ["重点词1", "重点词2"],
    "hint": "提示信息"
}}""",

        "Transition Practice": f"""请生成一个CET4水平的过渡练习题目。每次生成必须完全不同，不要重复之前的题目。
要求：
1. 给出两个独立的句子片段或观点
2. 要求学生用合适的过渡词/过渡句连接起来
3. 过渡词要多样化（如：however、therefore、in addition、on the other hand等）
4. 场景要多样化，不要重复
5. 建议作答时间：3-5分钟
6. 连接后约20-30词

返回JSON格式：
{{
    "part1": "第一部分句子",
    "part2": "第二部分句子",
    "hint": "提示可能的过渡词类型"
}}""",

        "Sentence Structure": f"""请生成一个CET4水平的句式练习题目。每次生成必须完全不同，不要重复之前的题目。
要求：
1. 给出一个常用句型结构（如：It is...that...、There is no doubt that...、Not only...but also...、It is universally acknowledged that...等）
2. 要求学生用这个句型造句
3. 句型要多样化，每次选择不同的句型
4. 建议作答时间：3-5分钟
5. 造句约15-25词

返回JSON格式：
{{
    "structure": "句型结构",
    "structure_example": "句型示例（可选）",
    "hint": "提示信息（可以给一个造句主题）"
}}""",

        "Sentence Variety": f"""请生成一个CET4水平的句式多样性题目。每次生成必须完全不同，不要重复之前的题目。
要求：
1. 给出一个普通句型
2. 要求学生改写成特定句型（如：倒装句、强调句、被动语态、虚拟语气等）
3. 句型转换类型要多样化
4. 内容场景要多样化
5. 建议作答时间：5-7分钟
6. 改写后句子约15-25词

返回JSON格式：
{{
    "original_sentence": "原句",
    "target_type": "目标句型（如倒装句/强调句/被动语态等）",
    "hint": "提示信息"
}}""",

        "Sentence Correction": f"""请生成一个CET4水平的病句题目。每次生成必须完全不同，不要重复之前的题目。
要求：
1. 句子长度15-25词
2. 包含常见的语法错误（如时态、主谓一致、冠词、介词等）
3. 错误要隐蔽但有迹可循
4. 内容要多样化，涵盖学习、生活、工作等不同场景
5. 建议作答时间：3-5分钟

返回JSON格式：
{{
    "question": "包含错误的句子",
    "error_type": "错误类型",
    "hint": "提示信息（不直接给出答案）"
}}""",

        "Paraphrasing": f"""请生成一个CET4水平的改写题目。每次生成必须完全不同，不要重复之前的题目。
要求：
1. 给出一个表达清晰的句子
2. 要求学生换一种方式表达相同意思
3. 使用不同的词汇或句式
4. 句子内容要多样化，不要重复
5. 建议作答时间：5-8分钟
6. 改写后句子约15-25词

返回JSON格式：
{{
    "original_sentence": "原句",
    "hint": "提示信息（如可以使用的同义词或句型）"
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
def evaluate_answer(mode: str, question: Dict, user_answer: str, record_id: str = None, auto_save_weakness: bool = True) -> Dict:
    mode_prompts = {
        "Phrase Practice": f"""请批改以下短语造句题目。

短语：{', '.join(question.get('phrases', []))}
用户造句：{user_answer}

你是我同桌，用轻松亲切的中文口吻批改，多鼓励。给出参考造句和更多示例。
如果用户造句中有错误或可以改进的地方，请在 details 中列出，包含：
- type: 错误类型标签，严格按照以下规则分类：
  * "注意"：语法错误（时态、主谓一致、冠词、介词等）或单词错误（拼写错误、用词错误、词汇选择不当等）
  * "建议"：语法和单词都正确，仅仅是表达不够流畅、不够优美或可以更地道
  * "其他"：不属于以上两种情况的问题
- original_sentence: 用户句子中可以改进的部分（保持原样）
- correction: 更好的表达建议，英文部分必须用英文表达

返回JSON格式：
{{
    "summary": "整体评价（中文）",
    "reference_sentence": "参考造句（英文）",
    "high_score_expression": "更多示例（英文）",
    "details": [
        {{
            "type": "注意/建议/其他",
            "original_sentence": "用户句子中可以改进的部分",
            "correction": "更好的表达建议（英文部分用英文）"
        }}
    ]
}}""",

        "Translation": f"""请批改以下翻译题目。

中文句子：{question.get('chinese_sentence', '')}
重点词汇：{', '.join(question.get('key_words', []))}
用户答案：{user_answer}

你是我同桌，用轻松亲切的中文口吻批改，多鼓励。给出参考译文和高分表达。
如果用户答案中有错误或可以改进的地方，请在 details 中列出，包含：
- type: 错误类型标签，严格按照以下规则分类：
  * "注意"：语法错误（时态、主谓一致、冠词、介词等）或单词错误（拼写错误、用词错误、词汇选择不当等）
  * "建议"：语法和单词都正确，仅仅是表达不够流畅、不够优美或可以更地道
  * "其他"：不属于以上两种情况的问题
- original_sentence: 用户有问题的原句片段（保持原样）
- correction: 修改建议，英文部分必须用英文表达，中文部分用中文表达

返回JSON格式：
{{
    "summary": "整体评价（中文）",
    "reference_translation": "参考译文（英文）",
    "high_score_expression": "高分表达（英文）",
    "details": [
        {{
            "type": "注意/建议/其他",
            "original_sentence": "用户有问题的原句片段",
            "correction": "修改建议（英文部分用英文，中文部分用中文）"
        }}
    ]
}}""",

        "Transition Practice": f"""请批改以下过渡练习题目。

第一部分：{question.get('part1', '')}
第二部分：{question.get('part2', '')}
用户答案：{user_answer}

你是我同桌，用轻松亲切的中文口吻批改，多鼓励。给出参考答案和更多过渡词选择。
如果用户答案中的过渡词使用可以改进，请在 details 中列出，包含：
- type: 错误类型标签，严格按照以下规则分类：
  * "注意"：语法错误（时态、主谓一致、冠词、介词等）或单词错误（拼写错误、用词错误、词汇选择不当等）
  * "建议"：语法和单词都正确，仅仅是表达不够流畅、不够优美或可以更地道
  * "其他"：不属于以上两种情况的问题
- original_sentence: 用户的原句（保持原样）
- correction: 更好的过渡词选择和解释，英文部分必须用英文表达

返回JSON格式：
{{
    "summary": "整体评价（中文）",
    "reference_answer": "参考答案（英文）",
    "high_score_expression": "更多过渡词（英文）",
    "details": [
        {{
            "type": "注意/建议/其他",
            "original_sentence": "用户的原句",
            "correction": "更好的过渡词选择和解释（英文部分用英文）"
        }}
    ]
}}""",

        "Sentence Structure": f"""请批改以下句式练习题目。

句型结构：{question.get('structure', '')}
用户造句：{user_answer}

你是我同桌，用轻松亲切的中文口吻批改，多鼓励。给出参考造句和更多示例。
如果用户造句中有错误或可以改进的地方，请在 details 中列出，包含：
- type: 错误类型标签，严格按照以下规则分类：
  * "注意"：语法错误（时态、主谓一致、冠词、介词等）或单词错误（拼写错误、用词错误、词汇选择不当等）
  * "建议"：语法和单词都正确，仅仅是表达不够流畅、不够优美或可以更地道
  * "其他"：不属于以上两种情况的问题
- original_sentence: 用户句子中可以改进的部分（保持原样）
- correction: 更好的表达建议，英文部分必须用英文表达

返回JSON格式：
{{
    "summary": "整体评价（中文）",
    "reference_sentence": "参考造句（英文）",
    "high_score_expression": "更多示例（英文）",
    "details": [
        {{
            "type": "注意/建议/其他",
            "original_sentence": "用户句子中可以改进的部分",
            "correction": "更好的表达建议（英文部分用英文）"
        }}
    ]
}}""",

        "Sentence Variety": f"""请批改以下句式多样性题目。

原句：{question.get('original_sentence', '')}
目标句型：{question.get('target_type', '')}
用户答案：{user_answer}

你是我同桌，用轻松亲切的中文口吻批改，多鼓励。给出参考答案和其他转换方式。
如果用户答案中的句式转换可以改进，请在 details 中列出，包含：
- type: 错误类型标签，严格按照以下规则分类：
  * "注意"：语法错误（时态、主谓一致、冠词、介词等）或单词错误（拼写错误、用词错误、词汇选择不当等）
  * "建议"：语法和单词都正确，仅仅是表达不够流畅、不够优美或可以更地道
  * "其他"：不属于以上两种情况的问题
- original_sentence: 用户的原句（保持原样）
- correction: 更好的转换方式和解释，英文部分必须用英文表达

返回JSON格式：
{{
    "summary": "整体评价（中文）",
    "reference_answer": "参考答案（英文）",
    "high_score_expression": "其他方式（英文）",
    "details": [
        {{
            "type": "注意/建议/其他",
            "original_sentence": "用户的原句",
            "correction": "更好的转换方式和解释（英文部分用英文）"
        }}
    ]
}}""",

        "Sentence Correction": f"""请批改以下句子改错题目。

原句（包含错误）：{question.get('question', '')}
错误类型：{question.get('error_type', '')}
用户答案：{user_answer}

你是我同桌，用轻松亲切的中文口吻批改，多鼓励。给出正确答案和高分表达。
如果用户答案中有错误，请在 details 中列出每个错误，包含：
- type: 错误类型标签，严格按照以下规则分类：
  * "注意"：语法错误（时态、主谓一致、冠词、介词等）或单词错误（拼写错误、用词错误、词汇选择不当等）
  * "建议"：语法和单词都正确，仅仅是表达不够流畅、不够优美或可以更地道
  * "其他"：不属于以上两种情况的问题
- original_sentence: 用户有问题的原句片段（保持原样）
- correction: 修改建议，英文部分必须用英文表达，中文部分用中文表达

返回JSON格式：
{{
    "summary": "整体评价（中文）",
    "correct_answer": "正确答案（英文）",
    "high_score_expression": "高分表达（英文）",
    "details": [
        {{
            "type": "注意/建议/其他",
            "original_sentence": "用户有问题的原句片段",
            "correction": "修改建议（英文部分用英文，中文部分用中文）"
        }}
    ]
}}""",

        "Paraphrasing": f"""请批改以下改写题目。

原句：{question.get('original_sentence', '')}
用户答案：{user_answer}

你是我同桌，用轻松亲切的中文口吻批改，多鼓励。给出参考改写和更好的改写方式。
如果用户答案中的改写可以改进，请在 details 中列出，包含：
- type: 错误类型标签，严格按照以下规则分类：
  * "注意"：语法错误（时态、主谓一致、冠词、介词等）或单词错误（拼写错误、用词错误、词汇选择不当等）
  * "建议"：语法和单词都正确，仅仅是表达不够流畅、不够优美或可以更地道
  * "其他"：不属于以上两种情况的问题
- original_sentence: 用户的改写（保持原样）
- correction: 更好的改写方式和解释，英文部分必须用英文表达

返回JSON格式：
{{
    "summary": "整体评价（中文）",
    "reference_paraphrase": "参考改写（英文）",
    "high_score_expression": "更好的方式（英文）",
    "details": [
        {{
            "type": "注意/建议/其他",
            "original_sentence": "用户的改写",
            "correction": "更好的改写方式和解释（英文部分用英文）"
        }}
    ]
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

        # 保存薄弱点 - 从 details 中提取信息
        if auto_save_weakness and result.get("details"):
            for detail in result["details"]:
                original = detail.get("original_sentence", "")
                correction = detail.get("correction", "")
                type_tag = detail.get("type", "其他")

                # 如果新格式有数据，使用新格式
                if original and correction:
                    # 使用AI生成的type标签
                    save_weakness_point({
                        "type": type_tag,
                        "issue": original,
                        "correction": correction,
                        "mode": mode
                    }, record_id=record_id)
                # 兼容旧格式（comment 字段）
                elif detail.get("comment"):
                    comment = detail.get("comment", "")
                    # 旧格式需要自己分类
                    type_str = "其他"

                    # 语法错误相关关键词 -> 归类到"注意"
                    grammar_keywords = [
                        "语法", "拼写", "时态", "主谓一致", "冠词", "介词", "动词", "名词",
                        "形容词", "副词", "错误", "应为", "应该是", "注意", "拼写错误",
                        "语法错误", "时态错误", "主谓不一致"
                    ]
                    for keyword in grammar_keywords:
                        if keyword in comment:
                            type_str = "注意"
                            break

                    # 表达相关关键词 -> 归类到"建议"
                    if type_str == "其他":
                        expression_keywords = [
                            "建议", "更好的表达", "可以改为", "表达", "流畅", "优美",
                            "更符合", "习惯", "地道", "高级", "改写"
                        ]
                        for keyword in expression_keywords:
                            if keyword in comment:
                                type_str = "建议"
                                break

                    # 提取修改建议
                    correction = ""
                    suggestion_patterns = [
                        "建议", "改为", "应该是", "可以改为", "更好的表达", "注意", "应为"
                    ]

                    for pattern in suggestion_patterns:
                        idx = comment.find(pattern)
                        if idx != -1:
                            correction = comment[idx:].strip()
                            break

                    # 如果没有找到明显的建议关键词，尝试其他模式
                    if not correction:
                        # 尝试提取引号中的内容作为修改建议
                        import re
                        quoted_content = re.findall(r"'([^']+)'", comment)
                        if len(quoted_content) >= 2:
                            correction = f"改为 '{quoted_content[1]}'"
                        elif len(quoted_content) == 1:
                            correction = f"参考：'{quoted_content[0]}'"

                    save_weakness_point({
                        "type": type_str,
                        "issue": comment,
                        "correction": correction,
                        "mode": mode
                    }, record_id=record_id)

        return result
    except Exception as e:
        st.error(f"批改失败: {str(e)}")
        return None

# AI 助手对话
def ask_ai_assistant(question: str):
    try:
        response = client.chat.completions.create(
            model="qwen-max",
            messages=[
                {"role": "system", "content": "你是我的英语学习搭子！我们都是四级备考的战友。请用轻松、口语化的中文跟我交流，就像朋友聊天一样。回答问题时：1）不要追求简洁，可以详细展开讲；2）结合四级备考的背景，补充相关的考点、高频词汇、易错点等；3）多用例子和场景帮助理解；4）鼓励我，给我实用的学习建议。记住：我们是朋友，不是师生！"},
                {"role": "user", "content": question}
            ],
            temperature=0.8,
            max_tokens=2000,
            stream=True
        )
        return response
    except Exception as e:
        return f"抱歉，我遇到了一些问题：{str(e)}"

# 侧边栏
def sidebar():
    with st.sidebar:
        # 计算坚持天数
        history = load_history()
        persistence_days = 0
        if history:
            dates = [h.get("timestamp", "").split("T")[0] for h in history if h.get("timestamp")]
            unique_dates = set(dates)
            persistence_days = len(unique_dates)
        
        # 标题
        st.markdown(
            f"""
            <div style='text-align: center; padding: 20px; background: linear-gradient(135deg, rgba(255,255,255,0.7) 0%, rgba(255,255,255,0.4) 100%); border-radius: 16px; backdrop-filter: blur(10px); margin-bottom: 20px; box-shadow: 0 4px 12px rgba(102, 187, 106, 0.15);'>
                <div class='material-icon-large'>edit_note</div>
                <h2 style='margin: 8px 0 12px 0; font-size: 22px; color: #2e5a3a; font-weight: 600; font-family: Georgia, "Times New Roman", serif;'>CET4 微写作</h2>
                <div style='border-top: 1px solid rgba(102, 187, 106, 0.3); padding-top: 12px;'>
                    <div style='font-family: Georgia, "Times New Roman", serif; font-size: 18px; color: #66bb6a; font-weight: normal; line-height: 1; margin-bottom: 4px;'>坚持 {persistence_days} 天</div>
                    <div style='font-size: 10px; color: #2e5a3a; letter-spacing: 1px;'>KEEP LEARNING</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        st.markdown("---")
        
        # 页面导航 - 使用自定义样式
        st.markdown("<h3 style='font-size: 14px; margin-bottom: 10px;'><span class='material-icon'>menu_book</span>页面导航</h3>", unsafe_allow_html=True)
        
        # 获取当前页面
        if "current_page" not in st.session_state:
            st.session_state.current_page = "练习页"
        
        page = st.session_state.current_page
        
        # 自定义导航按钮 - 竖向排版
        if st.button("今日练习", icon=":material/edit_note:", use_container_width=True, key="nav_practice"):
            st.session_state.current_page = "练习页"
            st.rerun()

        if st.button("薄弱点页", icon=":material/analytics:", use_container_width=True, key="nav_weakness"):
            st.session_state.current_page = "薄弱点页"
            st.rerun()

        if st.button("历史记录", icon=":material/history:", use_container_width=True, key="nav_history"):
            st.session_state.current_page = "历史记录"
            st.rerun()

        # Ask AI 按钮
        if st.button("AI 提问", icon=":material/smart_toy:", use_container_width=True, type="primary"):
            st.session_state.current_page = "AI 聊天"
            st.rerun()
        
        st.markdown("---")
        
        # 显示当前练习模式
        st.markdown("<h3 style='font-size: 14px; margin-bottom: 10px;'><span class='material-icon'>calendar_today</span>今日信息</h3>", unsafe_allow_html=True)
        today_mode = get_today_mode()
        st.info(f"**练习模式：** {today_mode}")
        
        st.markdown("---")
        st.markdown("<h3 style='font-size: 14px; margin-bottom: 10px;'><span class='material-icon'>bar_chart</span>练习统计</h3>", unsafe_allow_html=True)
        
        weakness_points = load_weakness_points()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("总练习", len(history))
        with col2:
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

    # 检查今日是否已完成练习
    history = load_history()
    today_records = [h for h in history if h.get("timestamp", "").startswith(today)]

    # 如果今日已完成练习，显示历史记录
    if today_records and not st.session_state.question:
        st.subheader("✅ 今日练习已完成")
        st.markdown("---")

        # 显示今日所有练习记录
        for i, record in enumerate(today_records, 1):
            mode = record.get("mode", "")
            question = record.get("question", {})
            user_answer = record.get("user_answer", "")
            evaluation = record.get("evaluation", {})
            record_id = record.get("record_id", "")

            st.markdown(f"**练习 {i}：{mode}**")

            # 显示题目
            if mode == "Phrase Practice":
                phrases = ', '.join(question.get('phrases', []))
                st.info(f"**短语：** {phrases}")
                if question.get('hint'):
                    st.caption(f"💡 提示：{question.get('hint', '')}")
            elif mode == "Translation":
                st.info(f"**中文句子：** {question.get('chinese_sentence', '')}")
                if question.get('hint'):
                    st.caption(f"💡 提示：{question.get('hint', '')}")
                if question.get('key_words'):
                    st.caption(f"🔑 重点词汇：{', '.join(question.get('key_words', []))}")
            elif mode == "Transition Practice":
                st.info(f"**第一部分：** {question.get('part1', '')}")
                st.info(f"**第二部分：** {question.get('part2', '')}")
                if question.get('hint'):
                    st.caption(f"💡 提示：{question.get('hint', '')}")
            elif mode == "Sentence Structure":
                st.info(f"**句型结构：** {question.get('structure', '')}")
                if question.get('structure_example'):
                    st.caption(f"📝 句型示例：{question.get('structure_example', '')}")
                if question.get('hint'):
                    st.caption(f"💡 提示：{question.get('hint', '')}")
            elif mode == "Sentence Variety":
                st.info(f"**原句：** {question.get('original_sentence', '')}")
                if question.get('target_type'):
                    st.caption(f"🎯 目标句型：{question.get('target_type', '')}")
                if question.get('hint'):
                    st.caption(f"💡 提示：{question.get('hint', '')}")
            elif mode == "Sentence Correction":
                st.info(f"**病句：** {question.get('question', '')}")
                if question.get('hint'):
                    st.caption(f"💡 提示：{question.get('hint', '')}")
                if question.get('error_type'):
                    st.caption(f"🔍 错误类型：{question.get('error_type', '')}")
            elif mode == "Paraphrasing":
                st.info(f"**原句：** {question.get('original_sentence', '')}")
                if question.get('hint'):
                    st.caption(f"💡 提示：{question.get('hint', '')}")

            # 显示用户答案
            st.write(f"✍️ 你的答案：{user_answer}")

            # 显示批改结果
            if evaluation:
                st.markdown("---")
                st.subheader("📊 批改结果")

                # 整体评价
                st.success(evaluation.get("summary", ""))

                # 参考答案（根据不同题型显示不同字段）
                if "correct_answer" in evaluation:
                    st.info(f"✅ **正确答案：** {evaluation['correct_answer']}")
                elif "reference_translation" in evaluation:
                    st.info(f"✅ **参考译文：** {evaluation['reference_translation']}")
                elif "reference_answer" in evaluation:
                    st.info(f"✅ **参考答案：** {evaluation['reference_answer']}")
                elif "reference_sentence" in evaluation:
                    st.info(f"✅ **参考造句：** {evaluation['reference_sentence']}")
                elif "reference_paraphrase" in evaluation:
                    st.info(f"✅ **参考改写：** {evaluation['reference_paraphrase']}")

                # 高分表达
                if "high_score_expression" in evaluation:
                    st.warning(f"⭐ **高分表达：** {evaluation['high_score_expression']}")

                # 详细反馈
                if evaluation.get("details"):
                    st.markdown("---")
                    st.subheader("🔍 详细反馈")
                    for detail in evaluation["details"]:
                        original = detail.get("original_sentence", "")
                        correction = detail.get("correction", "")
                        # 兼容旧格式
                        if not original and not correction:
                            original = detail.get("comment", "")

                        if original:
                            with st.expander(f"❌ {original[:50]}..."):
                                st.error(f"**问题：** {original}")
                                if correction:
                                    st.success(f"**建议：** {correction}")

            # 刷新批改按钮
            st.markdown("---")
            if st.button(f"刷新批改结果 (练习 {i})", icon=":material/refresh:", key=f"refresh_history_{i}", use_container_width=True):
                with st.spinner("正在重新批改..."):
                    # 先获取新批改结果（不自动保存薄弱点）
                    new_evaluation = evaluate_answer(mode, question, user_answer, record_id=record_id, auto_save_weakness=False)

                    # 只有批改成功才更新数据
                    if new_evaluation:
                        # 删除旧薄弱点
                        delete_weakness_points_by_record(record_id)

                        # 手动保存新薄弱点
                        if new_evaluation.get("details"):
                            for detail in new_evaluation["details"]:
                                original = detail.get("original_sentence", "")
                                correction = detail.get("correction", "")
                                type_tag = detail.get("type", "其他")

                                if original and correction:
                                    save_weakness_point({
                                        "type": type_tag,
                                        "issue": original,
                                        "correction": correction,
                                        "mode": mode
                                    }, record_id=record_id)

                        # 更新历史记录，覆盖同一题目的批改结果
                        save_practice({
                            "mode": mode,
                            "question": question,
                            "user_answer": user_answer,
                            "evaluation": new_evaluation
                        }, update_record_id=record_id)
                        st.rerun()
                    else:
                        st.error("批改失败，请重试")

            st.caption(f"🕐 时间：{record.get('timestamp', '')}")
            st.markdown("---")

        # 继续练习按钮
        if st.button("继续练习", icon=":material/refresh:", type="primary", use_container_width=True):
            with st.spinner("正在生成题目..."):
                weakness_points = load_weakness_points()
                question = generate_question(get_today_mode(), weakness_points)
                if question:
                    st.session_state.question = question
                    st.session_state.user_answer = ""
                    st.session_state.evaluation = None
                    st.session_state.submitted = False
                    # 保存到本地
                    save_daily_question(today, question)
                    st.rerun()

        return

    # 首次加载时，从本地读取今日题目（如果存在）
    if not st.session_state.question:
        saved_question = load_daily_question(today)
        if saved_question:
            st.session_state.question = saved_question

    # 生成题目按钮（显示在题目上方，用于首次生成）
    if not st.session_state.question:
        if st.button("生成今日题目", icon=":material/auto_awesome:", type="primary", use_container_width=True):
            with st.spinner("正在生成题目..."):
                question = generate_question(get_today_mode())
                if question:
                    st.session_state.question = question
                    # 保存到本地
                    save_daily_question(today, question)
    
    # 显示题目
    if st.session_state.question:
        q = st.session_state.question
        
        st.subheader("📋 题目")
        
        mode = get_today_mode()
        if mode == "Phrase Practice":
            phrases = ', '.join(q.get('phrases', []))
            st.info(f"**短语：** {phrases}")
            st.caption(f"💡 提示：{q.get('hint', '')}")
            st.caption(f"⏱️ 建议作答时间：3-5分钟")
            st.caption(f"📝 建议字数：10-20词")
        
        elif mode == "Translation":
            st.info(f"**中文句子：** {q.get('chinese_sentence', '')}")
            st.caption(f"💡 提示：{q.get('hint', '')}")
            st.caption(f"🔑 重点词汇：{', '.join(q.get('key_words', []))}")
            st.caption(f"⏱️ 建议作答时间：5-8分钟")
            st.caption(f"📝 建议字数：15-25词")
        
        elif mode == "Transition Practice":
            st.info(f"**第一部分：** {q.get('part1', '')}")
            st.info(f"**第二部分：** {q.get('part2', '')}")
            st.caption(f"💡 提示：{q.get('hint', '')}")
            st.caption(f"⏱️ 建议作答时间：3-5分钟")
            st.caption(f"📝 建议字数：20-30词")
        
        elif mode == "Sentence Structure":
            st.info(f"**句型结构：** {q.get('structure', '')}")
            if q.get('structure_example'):
                st.caption(f"📝 句型示例：{q.get('structure_example', '')}")
            st.caption(f"💡 提示：{q.get('hint', '')}")
            st.caption(f"⏱️ 建议作答时间：3-5分钟")
            st.caption(f"📝 建议字数：15-25词")
        
        elif mode == "Sentence Variety":
            st.info(f"**原句：** {q.get('original_sentence', '')}")
            st.caption(f"🎯 目标句型：{q.get('target_type', '')}")
            st.caption(f"💡 提示：{q.get('hint', '')}")
            st.caption(f"⏱️ 建议作答时间：5-7分钟")
            st.caption(f"📝 建议字数：15-25词")
        
        elif mode == "Sentence Correction":
            st.info(f"**病句：** {q.get('question', '')}")
            st.caption(f"💡 提示：{q.get('hint', '')}")
            st.caption(f"🔍 错误类型：{q.get('error_type', '')}")
            st.caption(f"⏱️ 建议作答时间：3-5分钟")
        
        elif mode == "Paraphrasing":
            st.info(f"**原句：** {q.get('original_sentence', '')}")
            st.caption(f"💡 提示：{q.get('hint', '')}")
            st.caption(f"⏱️ 建议作答时间：5-8分钟")
            st.caption(f"📝 建议字数：15-25词")
        
        st.markdown("---")
        
        # 用户输入
        if not st.session_state.submitted:
            st.subheader("✍️ 你的答案")
            user_answer = st.text_area(
                "",
                value=st.session_state.user_answer,
                height=150,
                placeholder="在这里输入你的答案...",
                key="user_answer_input",
                label_visibility="collapsed"
            )

            # 统计英语单词数
            import re
            # 匹配英语单词（只包含字母，可能包含连字符或撇号）
            english_words = re.findall(r"[a-zA-Z]+(?:['-]?[a-zA-Z]+)*", user_answer)
            word_count = len(english_words)
            st.caption(f"📊 单词数：{word_count}")

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

                            # 保存练习记录（新建记录）
                            save_practice({
                                "mode": mode,
                                "question": st.session_state.question,
                                "user_answer": user_answer,
                                "evaluation": st.session_state.evaluation
                            })
                            # 保存 record_id 到 session_state，用于刷新批改
                            history = load_history()
                            if history:
                                st.session_state.current_record_id = history[-1].get("record_id")
                    else:
                        st.warning("请先输入你的答案！")
            
            with col2:
                if st.button("刷新题目", icon=":material/refresh:", use_container_width=True):
                    with st.spinner("正在刷新题目..."):
                        question = generate_question(get_today_mode())
                        if question:
                            st.session_state.question = question
                            st.session_state.user_answer = ""
                            st.session_state.evaluation = None
                            st.session_state.submitted = False
                            st.rerun()
            
            with col3:
                if st.button("清空输入", icon=":material/delete:", use_container_width=True):
                    st.session_state.user_answer = ""
                    st.rerun()
        
        # 显示批改结果
        if st.session_state.submitted and st.session_state.evaluation:
            st.markdown("---")
            st.subheader("📊 批改结果")

            eval_result = st.session_state.evaluation

            # 整体评价
            st.success(eval_result.get("summary", ""))

            # 参考答案（根据不同题型显示不同字段）
            if "correct_answer" in eval_result:
                st.info(f"✅ **正确答案：** {eval_result['correct_answer']}")
            elif "reference_translation" in eval_result:
                st.info(f"✅ **参考译文：** {eval_result['reference_translation']}")
            elif "reference_answer" in eval_result:
                st.info(f"✅ **参考答案：** {eval_result['reference_answer']}")
            elif "reference_sentence" in eval_result:
                st.info(f"✅ **参考造句：** {eval_result['reference_sentence']}")
            elif "reference_paraphrase" in eval_result:
                st.info(f"✅ **参考改写：** {eval_result['reference_paraphrase']}")

            # 高分表达
            if "high_score_expression" in eval_result:
                st.warning(f"⭐ **高分表达：** {eval_result['high_score_expression']}")

            # 详细反馈
            if eval_result.get("details"):
                st.markdown("---")
                st.subheader("🔍 详细反馈")
                for detail in eval_result["details"]:
                    original = detail.get("original_sentence", "")
                    correction = detail.get("correction", "")

                    # 兼容旧格式
                    if not original and not correction:
                        original = detail.get("comment", "")

                    if original:
                        with st.expander(f"❌ {original[:50]}..."):
                            st.error(f"**问题：** {original}")
                            if correction:
                                st.success(f"**建议：** {correction}")

            # 刷新批改结果和继续练习按钮
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("刷新批改结果", icon=":material/refresh:", use_container_width=True):
                    with st.spinner("正在重新批改..."):
                        # 先获取新批改结果（不自动保存薄弱点）
                        new_evaluation = evaluate_answer(
                            mode,
                            st.session_state.question,
                            st.session_state.user_answer,
                            record_id=st.session_state.get("current_record_id"),
                            auto_save_weakness=False
                        )

                        # 只有批改成功才更新数据
                        if new_evaluation:
                            # 删除旧薄弱点
                            if st.session_state.get("current_record_id"):
                                delete_weakness_points_by_record(st.session_state.current_record_id)

                            # 手动保存新薄弱点
                            if new_evaluation.get("details"):
                                for detail in new_evaluation["details"]:
                                    original = detail.get("original_sentence", "")
                                    correction = detail.get("correction", "")
                                    type_tag = detail.get("type", "其他")

                                    if original and correction:
                                        save_weakness_point({
                                            "type": type_tag,
                                            "issue": original,
                                            "correction": correction,
                                            "mode": mode
                                        }, record_id=st.session_state.get("current_record_id"))

                            st.session_state.evaluation = new_evaluation

                            # 更新历史记录，覆盖同一题目的批改结果
                            if st.session_state.get("current_record_id"):
                                save_practice({
                                    "mode": mode,
                                    "question": st.session_state.question,
                                    "user_answer": st.session_state.user_answer,
                                    "evaluation": new_evaluation
                                }, update_record_id=st.session_state.current_record_id)
                            st.rerun()
                        else:
                            st.error("批改失败，请重试")

            with col2:
                if st.button("继续练习", icon=":material/refresh:", type="primary", use_container_width=True):
                    st.session_state.question = None
                    st.session_state.user_answer = ""
                    st.session_state.evaluation = None
                    st.session_state.submitted = False
                    st.session_state.current_record_id = None
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

    st.subheader("📈 薄弱点统计")
    # 使用横向排列显示统计卡片
    if type_counts:
        # 根据类型数量动态调整列数
        num_types = len(type_counts)
        if num_types <= 3:
            cols = st.columns(num_types)
        else:
            cols = st.columns(3)

        for i, (ptype, count) in enumerate(type_counts.items()):
            with cols[i % 3]:
                st.metric(ptype, count)

    # 筛选功能
    st.markdown("---")
    st.markdown("📝 薄弱点详情")

    # 获取所有类型
    all_types = list(type_counts.keys())
    all_types.sort()

    # 添加筛选器
    selected_types = st.multiselect(
        "筛选类型",
        options=all_types,
        default=all_types,
        key="weakness_filter"
    )

    # 根据筛选过滤薄弱点
    if selected_types:
        filtered_points = [p for p in weakness_points if p.get("type", "其他") in selected_types]
    else:
        filtered_points = weakness_points
    # 按模式分组
    mode_groups = {}
    for point in filtered_points:
        mode = point.get("mode", "其他")
        if mode not in mode_groups:
            mode_groups[mode] = []
        mode_groups[mode].append(point)

    for mode, points in mode_groups.items():
        with st.expander(f"📌 {mode} ({len(points)}个)"):
            for i, point in enumerate(points, 1):
                type_text = point.get('type', '')
                # 根据类型设置不同的标签颜色，使用与侧边栏按钮相同的背景和边框
                if type_text == "注意":
                    tag_style = "background: rgba(255, 255, 255, 0.5); border: 1px solid rgba(102, 187, 106, 0.3); color: #e57373; padding: 2px 8px; border-radius: 4px; font-size: 12px; display: inline-block;"
                elif type_text == "建议":
                    tag_style = "background: rgba(255, 255, 255, 0.5); border: 1px solid rgba(102, 187, 106, 0.3); color: #66bb6a; padding: 2px 8px; border-radius: 4px; font-size: 12px; display: inline-block;"
                else:
                    tag_style = "background: rgba(255, 255, 255, 0.5); border: 1px solid rgba(102, 187, 106, 0.3); color: #5a8f62; padding: 2px 8px; border-radius: 4px; font-size: 12px; display: inline-block;"
                st.markdown(f"**{i}.** <span style='{tag_style}'>{type_text}</span>", unsafe_allow_html=True)
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
    col1, col2 = st.columns(2)
    with col1:
        st.metric("总练习次数", len(history))
    with col2:
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
                if mode == "Phrase Practice":
                    phrases = ', '.join(question.get('phrases', []))
                    st.info(f"短语：{phrases}")
                elif mode == "Translation":
                    st.info(f"题目：{question.get('chinese_sentence', '')}")
                elif mode == "Transition Practice":
                    st.info(f"题目：{question.get('part1', '')} + {question.get('part2', '')}")
                elif mode == "Sentence Structure":
                    st.info(f"句型：{question.get('structure', '')}")
                elif mode == "Sentence Variety":
                    st.info(f"原句：{question.get('original_sentence', '')}")
                elif mode == "Sentence Correction":
                    st.info(f"题目：{question.get('question', '')}")
                elif mode == "Paraphrasing":
                    st.info(f"题目：{question.get('original_sentence', '')}")
                
                # 显示用户答案
                st.write(f"✍️ 你的答案：{user_answer}")
                
                # 显示评价
                if evaluation:
                    summary = evaluation.get("summary", "")
                    st.info(f"📝 {summary}")
                    
                    # 显示薄弱点详情
                    details = evaluation.get("details", [])
                    if details:
                        st.markdown("---")
                        st.markdown("🔍 薄弱点详情")
                        for detail in details:
                            original = detail.get("original_sentence", "")
                            correction = detail.get("correction", "")

                            # 兼容旧格式
                            if not original and not correction:
                                original = detail.get("comment", "")

                            if original:
                                with st.expander(f"❌ {original[:50]}..."):
                                    st.error(f"**问题：** {original}")
                                    if correction:
                                        st.success(f"**建议：** {correction}")
                
                st.caption(f"🕐 时间：{record.get('timestamp', '')}")
                st.markdown("---")

# 对话管理辅助函数
def init_ai_chat_state():
    """初始化 AI 聊天状态"""
    if "ai_conversations" not in st.session_state:
        st.session_state.ai_conversations = []
    if "current_conversation_id" not in st.session_state:
        st.session_state.current_conversation_id = None

def create_new_conversation():
    """创建新对话"""
    import time
    conversation = {
        "id": f"conv_{int(time.time())}",
        "title": "新对话",
        "created_at": datetime.now().isoformat(),
        "messages": []
    }
    st.session_state.ai_conversations.insert(0, conversation)
    st.session_state.current_conversation_id = conversation["id"]
    return conversation["id"]

def get_current_conversation():
    """获取当前对话"""
    conv_id = st.session_state.current_conversation_id
    if not conv_id:
        return None
    for conv in st.session_state.ai_conversations:
        if conv["id"] == conv_id:
            return conv
    return None

def add_message_to_conversation(role, content):
    """添加消息到当前对话"""
    conv = get_current_conversation()
    if conv:
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        conv["messages"].append(message)

        # 如果是第一条用户消息，更新对话标题
        if role == "user" and len(conv["messages"]) == 1:
            conv["title"] = content[:30] + ("..." if len(content) > 30 else "")

def get_conversation_context(conv_id=None, max_turns=5):
    """获取对话上下文"""
    if not conv_id:
        conv_id = st.session_state.current_conversation_id
    if not conv_id:
        return []

    conv = get_current_conversation()
    if not conv:
        return []

    messages = conv["messages"]
    # 保留最近的 N 轮对话（1轮 = 1个用户 + 1个助手）
    if len(messages) > max_turns * 2:
        messages = messages[-max_turns * 2:]

    # 转换为 API 格式
    api_messages = []
    for msg in messages:
        api_messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    return api_messages

def ask_ai_with_context(messages):
    """带上下文的 AI 调用"""
    system_prompt = "你是我的英语学习搭子！我们都是四级备考的战友。请用轻松、口语化的中文跟我交流，就像朋友聊天一样。回答问题时：1）不要追求简洁，可以详细展开讲；2）结合四级备考的背景，补充相关的考点、高频词汇、易错点等；3）多用例子和场景帮助理解；4）鼓励我，给我实用的学习建议。记住：我们是朋友，不是师生！"

    # 构建消息列表
    api_messages = [
        {"role": "system", "content": system_prompt}
    ]
    api_messages.extend(messages)

    try:
        response = client.chat.completions.create(
            model="qwen-max",
            messages=api_messages,
            temperature=0.8,
            max_tokens=2000,
            stream=True
        )
        return response
    except Exception as e:
        return None

# AI 聊天页面
def ai_chat_page():
    # 初始化状态
    init_ai_chat_state()

    # 如果没有对话，创建新对话
    if not st.session_state.ai_conversations:
        create_new_conversation()

    # 布局：左侧对话列表，右侧聊天区域
    col1, col2 = st.columns([1, 3])

    # 左侧：对话列表
    with col1:

        # 新建对话按钮
        if st.button("新建对话", icon=":material/add:", use_container_width=True, key="new_conv"):
            create_new_conversation()
            st.rerun()

        # 显示对话列表
        for conv in st.session_state.ai_conversations:
            is_current = conv["id"] == st.session_state.current_conversation_id

            # 显示对话信息
            with st.container():
                col_title, col_del = st.columns([4, 1])
                with col_title:
                    if st.button(
                        conv["title"],
                        key=f"conv_{conv['id']}",
                        use_container_width=True,
                        type="primary" if is_current else "secondary"
                    ):
                        st.session_state.current_conversation_id = conv["id"]
                        st.rerun()
                with col_del:
                    if st.button("×", key=f"del_{conv['id']}", help="删除对话"):
                        st.session_state.ai_conversations = [
                            c for c in st.session_state.ai_conversations
                            if c["id"] != conv["id"]
                        ]
                        if st.session_state.current_conversation_id == conv["id"]:
                            if st.session_state.ai_conversations:
                                st.session_state.current_conversation_id = st.session_state.ai_conversations[0]["id"]
                            else:
                                create_new_conversation()
                        st.rerun()

                st.caption(f"🕐 {conv['created_at'].split('T')[0]}")

    # 右侧：聊天区域
    with col2:
        conv = get_current_conversation()
        if not conv:
            st.info("没有选中的对话")
            return

        # 显示历史消息
        if not conv["messages"]:
            st.info("开始一个新的对话吧！有什么英语学习问题尽管问我。")
        else:
            for message in conv["messages"]:
                with st.chat_message(message["role"]):
                    st.write(message["content"])

        # 聊天输入框
        user_input = st.chat_input("输入你的问题...")

        if user_input:
            # 添加用户消息
            add_message_to_conversation("user", user_input)

            # 显示用户消息
            with st.chat_message("user"):
                st.write(user_input)

            # 获取上下文
            context = get_conversation_context()

            # 调用 AI
            with st.chat_message("assistant"):
                with st.spinner("正在思考..."):
                    response_stream = ask_ai_with_context(context)

                    if response_stream:
                        # 使用 st.write_stream 进行流式输出
                        full_response = st.write_stream(response_stream)

                        # 添加助手消息
                        add_message_to_conversation("assistant", full_response)

                        # AI 回答完成后，使用 rerun 刷新页面并滚动到底部
                        st.rerun()
                    else:
                        st.error("抱歉，我遇到了一些问题，请稍后再试。")

# 主函数
def main():
    init_data_files()

    # 侧边栏
    page = sidebar()

    # 主内容区域
    if page == "练习页":
        practice_page()
    elif page == "薄弱点页":
        weakness_page()
    elif page == "历史记录":
        history_page()
    elif page == "AI 聊天":
        ai_chat_page()

if __name__ == "__main__":
    main()