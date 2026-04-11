import streamlit as st
import pandas as pd
import os
from datetime import datetime

# ================= 基本配置 =================
DATA_FILE = "data.csv"
PLAN_FILE = "homework_plan.csv"
STUDENT_FILE = "students.csv"
TEACHER_PASSWORD = "teacher123"

st.set_page_config(page_title="智能作业时间管理系统", layout="centered")

# ================= 初始化 CSV =================
def init_csv(path, columns):
    if not os.path.exists(path):
        pd.DataFrame(columns=columns).to_csv(path, index=False)

init_csv(
    DATA_FILE,
    ["提交时间","学号","姓名","日期","学科","作业内容","完成时间(分钟)"]
)
init_csv(
    PLAN_FILE,
    ["日期","学科","作业内容"]
)
init_csv(
    STUDENT_FILE,
    ["学号","姓名","密码"]
)

def load_csv(path):
    return pd.read_csv(path, dtype=str)

def save_csv(df, path):
    df.to_csv(path, index=False)

# ================= 页面选择 =================
st.title("📘 智能作业时间管理系统")
role = st.radio("请选择身份：", ["学生", "老师"], key="role_switch")

# ================= 身份切换保护 =================
if "current_role" not in st.session_state:
    st.session_state.current_role = role

if st.session_state.current_role != role:
    st.session_state.current_role = role
    st.session_state.student_logged_in = False
    st.session_state.teacher_logged_in = False
    st.session_state.pop("student_name", None)

# ==================================================
# 👨‍🎓 学生端
# ==================================================
if role == "学生":
    if "student_logged_in" not in st.session_state:
        st.session_state.student_logged_in = False

    st.subheader("👨‍🎓 学生登录")
    sid = st.text_input("学号", key="stu_sid")
    pwd = st.text_input("密码", type="password", key="stu_pwd")

    if st.button("登录", key="stu_login_btn"):
        students = load_csv(STUDENT_FILE)
        match = students[
            (students["学号"] == sid.strip()) &
            (students["密码"] == pwd.strip())
        ]
        if not match.empty:
            st.session_state.student_logged_in = True
            st.session_state.student_name = match.iloc[0]["姓名"]
            st.success("登录成功 ✅")
        else:
            st.error("学号或密码错误")

    if not st.session_state.student_logged_in:
        st.info("请先登录学生账号")
    else:
        st.divider()
        st.write(f"欢迎你，**{st.session_state.student_name}**")

        # ✅ 新增：注销账号
        with st.expander("⚠️ 注销账号（谨慎操作）"):
            confirm = st.checkbox("我确认要注销自己的账号")
            if st.button("注销账号"):
                if confirm:
                    students = load_csv(STUDENT_FILE)
                    students = students[students["学号"] != sid]
                    save_csv(students, STUDENT_FILE)
                    st.session_state.student_logged_in = False
                    st.warning("账号已注销，已退出登录")
                    st.stop()

        today = datetime.now().strftime("%Y-%m-%d")
        plans = load_csv(PLAN_FILE)
        today_tasks = plans[plans["日期"] == today]

        st.markdown("### ✅ 今日作业完成时间登记")
        if today_tasks.empty:
            st.info("今天暂无作业")
        else:
            st.dataframe(today_tasks, use_container_width=True)

            task_idx = st.selectbox(
                "选择作业",
                today_tasks.index,
                format_func=lambda i:
                    f"{today_tasks.loc[i,'学科']}｜{today_tasks.loc[i,'作业内容']}",
                key="stu_task_select"
            )

            minutes = st.number_input(
                "完成时间（分钟）",
                min_value=0,
                step=5,
                key="stu_minutes"
            )

            if st.button("提交完成时间", key="stu_submit_time"):
                if minutes > 0:
                    data = load_csv(DATA_FILE)
                    task = today_tasks.loc[task_idx]
                    data = pd.concat([data, pd.DataFrame([{
                        "提交时间": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "学号": sid,
                        "姓名": st.session_state.student_name,
                        "日期": today,
                        "学科": task["学科"],
                        "作业内容": task["作业内容"],
                        "完成时间(分钟)": str(minutes)
                    }])], ignore_index=True)
                    save_csv(data, DATA_FILE)
                    st.success("完成时间已保存 ✅")

        st.divider()
        st.markdown("### 📊 我的完成时间统计（按学科）")
        data = load_csv(DATA_FILE)
        my = data[data["学号"] == sid]

        if not my.empty:
            my["完成时间(分钟)"] = my["完成时间(分钟)"].astype(int)
            st.bar_chart(my.groupby("学科")["完成时间(分钟)"].sum())

# ==================================================
# 👩‍🏫 老师端
# ==================================================
elif role == "老师":
    if "teacher_logged_in" not in st.session_state:
        st.session_state.teacher_logged_in = False

    st.subheader("👩‍🏫 教师登录")
    pwd = st.text_input("教师密码", type="password", key="teacher_pwd")

    if st.button("登录", key="teacher_login_btn"):
        if pwd == TEACHER_PASSWORD:
            st.session_state.teacher_logged_in = True
            st.success("登录成功 ✅")
        else:
            st.error("密码错误")

    if not st.session_state.teacher_logged_in:
        st.info("请输入教师密码登录")
    else:
        st.divider()

        # ===== 学生账号管理（原样保留）=====
        st.markdown("## 👥 学生账号管理")
        students = load_csv(STUDENT_FILE)

        with st.expander("➕ 新增学生账号"):
            new_sid = st.text_input("学号", key="add_sid")
            new_name = st.text_input("姓名", key="add_name")
            new_pwd = st.text_input("密码", key="add_pwd")

            if st.button("添加账号", key="add_student_btn"):
                students = pd.concat([students, pd.DataFrame([{
                    "学号": new_sid.strip(),
                    "姓名": new_name.strip(),
                    "密码": new_pwd.strip()
                }])], ignore_index=True)
                save_csv(students, STUDENT_FILE)
                st.success("学生账号已添加 ✅")

        with st.expander("✏️ 修改学生账号"):
            if not students.empty:
                sel_sid = st.selectbox(
                    "选择学生",
                    students["学号"],
                    key="edit_student_select"
                )
                stu = students[students["学号"] == sel_sid].iloc[0]

                edit_name = st.text_input("姓名", stu["姓名"], key="edit_name")
                edit_pwd = st.text_input("密码", stu["密码"], key="edit_pwd")

                if st.button("保存修改", key="save_student_edit"):
                    students.loc[students["学号"] == sel_sid, "姓名"] = edit_name
                    students.loc[students["学号"] == sel_sid, "密码"] = edit_pwd
                    save_csv(students, STUDENT_FILE)
                    st.success("学生账号已修改 ✅")

        st.dataframe(students, use_container_width=True)
# ✅ 新增：删除学生账号
        with st.expander("🗑️ 删除学生账号（谨慎操作）"):
            if not students.empty:
                del_sid = st.selectbox(
                    "选择要删除的学生学号",
                    students["学号"],
                    key="delete_student_select"
                )

                confirm = st.checkbox(
                    "我确认要删除该学生账号（不可恢复）",
                    key="delete_student_confirm"
                )

                if st.button("删除学生账号", key="delete_student_btn"):
                    if confirm:
                        students = students[students["学号"] != del_sid]
                        save_csv(students, STUDENT_FILE)
                        st.success(f"学生账号 {del_sid} 已删除 ✅")
                    else:
                        st.warning("请先勾选确认框")
        # ===== 作业管理 =====
        st.divider()
        st.markdown("## 📝 作业管理")
        plans = load_csv(PLAN_FILE)

        with st.expander("➕ 新增作业"):
            date = st.date_input("日期", key="plan_date")
            subject = st.selectbox("学科", ["语文","数学","英语","科学"], key="plan_subject")
            content = st.text_input("作业内容", key="plan_content")

            if st.button("布置作业", key="add_plan_btn"):
                plans = pd.concat([plans, pd.DataFrame([{
                    "日期": date.strftime("%Y-%m-%d"),
                    "学科": subject,
                    "作业内容": content
                }])], ignore_index=True)
                save_csv(plans, PLAN_FILE)
                st.success("作业已布置 ✅")

        with st.expander("✏️ 修改作业"):
            if not plans.empty:
                plan_idx = st.selectbox(
                    "选择作业",
                    plans.index,
                    format_func=lambda i:
                        f"{plans.loc[i,'日期']}｜{plans.loc[i,'学科']}｜{plans.loc[i,'作业内容']}",
                    key="edit_plan_select"
                )

                plans.loc[plan_idx, "日期"] = st.text_input(
                    "日期",
                    plans.loc[plan_idx,"日期"],
                    key="edit_plan_date"
                )
                plans.loc[plan_idx, "学科"] = st.text_input(
                    "学科",
                    plans.loc[plan_idx,"学科"],
                    key="edit_plan_subject"
                )
                plans.loc[plan_idx, "作业内容"] = st.text_input(
                    "作业内容",
                    plans.loc[plan_idx,"作业内容"],
                    key="edit_plan_content"
                )

                if st.button("保存修改", key="save_plan_edit"):
                    save_csv(plans, PLAN_FILE)
                    st.success("作业已修改 ✅")

        # ✅ 新增：删除作业
        with st.expander("🗑️ 删除作业（谨慎操作）"):
            if not plans.empty:
                del_idx = st.selectbox(
                    "选择要删除的作业",
                    plans.index,
                    format_func=lambda i:
                        f"{plans.loc[i,'日期']}｜{plans.loc[i,'学科']}｜{plans.loc[i,'作业内容']}",
                    key="delete_plan_select"
                )
                confirm = st.checkbox("确认删除该作业", key="delete_plan_confirm")

                if st.button("删除作业", key="delete_plan_btn"):
                    if confirm:
                        plans = plans.drop(del_idx)
                        save_csv(plans, PLAN_FILE)
                        st.success("作业已删除 ✅")
                    else:
                        st.warning("请先确认删除操作")

        st.dataframe(plans, use_container_width=True)

        # ===== 学生作业完成时间表格 =====
        st.divider()
        st.markdown("## ✅ 学生作业完成时间明细表")
        data = load_csv(DATA_FILE)
        if not data.empty:
            st.dataframe(data, use_container_width=True)

        # ===== 老师完成时间柱状图 =====
        st.divider()
        st.markdown("## 📊 全班完成时间统计（按学科）")
        if not data.empty:
            data["完成时间(分钟)"] = data["完成时间(分钟)"].astype(int)
            st.bar_chart(data.groupby("学科")["完成时间(分钟)"].sum())
