# 🎓 老师风格智能辅导机器人（最终完美修复版：选择题不拆分）
from functools import lru_cache

from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferWindowMemory
from langchain.chains import ConversationChain
from langchain.prompts.prompt import PromptTemplate
import time
import warnings
import mysql.connector
from neo4j import GraphDatabase

class QuestionService:
    def __init__(
        self,
    ) -> None:
        return

@lru_cache
def get_question_service(

) -> QuestionService:
    return QuestionService(
    )

warnings.filterwarnings("ignore")

# ===================== 配置区 =====================
API_KEY = ""#待填
MODEL = ""#待填
BASE_URL = ""#待填
TYPE_SPEED = 0.03

MYSQL_HOST = "39.107.241.146"
MYSQL_PORT = 3306
MYSQL_USER = "root"
MYSQL_PWD = "USTB@SH2026"
DB_NAME = "groub_c"

NEO4J_URI = "bolt://39.107.241.146:7687"
NEO4J_USER = "neo4j"
NEO4J_PWD = "USTB@SH2026"
# ====================================================

# AI 模型
llm = ChatOpenAI(
    api_key=API_KEY,
    model=MODEL,
    base_url=BASE_URL,
    temperature=0.7,
    max_tokens=1024
)

# 老师模板
template = """
你是专业、温柔、耐心的老师。
纯文本回答，简洁清晰。

对话历史：
{history}
学生：{input}
老师：
"""
prompt = PromptTemplate(input_variables=["history", "input"], template=template)
memory = ConversationBufferWindowMemory(k=5)
chat_chain = ConversationChain(llm=llm, memory=memory, prompt=prompt, verbose=False)

# 打字机输出
def stream_print(text, delay=TYPE_SPEED):
    try:
        if not text:
            print("\n🎓 老师：我没理解你的问题～\n")
            return
        print("\n🎓 老师：", end="")
        for c in text:
            print(c, end="", flush=True)
            time.sleep(delay)
        print("\n")
    except:
        print("\n🎓 老师：出错啦～\n")

# 菜单
def show_menu():
    print("\n" + "="*60)
    print("🎓 老师风格智能辅导机器人".center(60))
    print("="*60)
    print("  /menu    菜单")
    print("  /test    生成题目并保存数据库")
    print("  /exit    退出")
    print("="*60)

# Neo4j 获取知识点
def get_knowledge_from_neo4j():
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PWD))
        with driver.session() as session:
            res = session.run("MATCH (n) RETURN n LIMIT 10")
            nodes = []
            for r in res:
                n = r["n"]
                if "name" in n:
                    nodes.append(n["name"])
                elif "title" in n:
                    nodes.append(n["title"])
                else:
                    nodes.append(str(n))
        driver.close()
        return nodes
    except:
        return []

# --------------------- 【修复】AI出题：一道题占一行 ---------------------
def generate_questions(ks):
    if not ks:
        return "未获取到知识点"

    prompt = f"""
你是专业出题老师，请根据知识点出 3 道题目。
规则：
1. 可以是单选题或简答题
2. **单选题必须把题干+选项写在同一行**，用 | 分隔选项
3. 每道题占一行
4. 只输出题目，不输出多余内容

知识点：{ks}

请输出 3 道题：
"""
    return llm.invoke(prompt).content

# --------------------- 【修复】存入数据库：一道题 = 一条数据 ---------------------
def save_questions_to_mysql(content):
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PWD,
            database=DB_NAME
        )
        cursor = conn.cursor()

        SAFE_TASK_ID = 1

        # 按行读取，空行跳过
        lines = [line.strip() for line in content.splitlines() if line.strip()]

        for line in lines:
            cursor.execute("""
                INSERT INTO task_questions
                (task_id, question_text, correct_answer, is_passed, user_answer, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
            """, (
                SAFE_TASK_ID,
                line,        # 一整道题（含选项）存在一起
                "(开放题)",
                0,
                ""
            ))

        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print("❌ MySQL 错误：", e)
        return False

# 测试功能
def run_test():
    stream_print("正在从知识图谱获取知识点...")
    ks = get_knowledge_from_neo4j()
    if not ks:
        stream_print("未获取到知识点")
        return

    stream_print("正在生成题目...")
    qs = generate_questions(ks)
    stream_print(f"生成完成：\n{qs}")

    stream_print("正在保存到数据库...")
    if save_questions_to_mysql(qs):
        stream_print("✅ 题目已成功保存到 task_questions 表！")
    else:
        stream_print("❌ 保存失败")

# ===================== 主程序 =====================
show_menu()
while True:
    ipt = input("\n💬 你：").strip()
    if not ipt:
        continue

    if ipt.startswith("/"):
        cmd = ipt.lower()
        if cmd == "/menu":
            show_menu()
        elif cmd == "/test":
            run_test()
        elif cmd == "/exit":
            print("👋 再见！")
            break
        continue

    try:
        res = chat_chain.predict(input=ipt)
        stream_print(res)
    except:
        print("❌ 出错，请重试")