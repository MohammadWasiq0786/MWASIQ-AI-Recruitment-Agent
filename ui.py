import streamlit as st

def setup_page():
    st.title("🚀 MWASIQ AI Recruitment Agent")
    st.caption("Your AI assistant for resume analysis, Q&A, interview preparation, and improvement suggestions.")

def display_header():
    st.header("📄 Resume Analysis Dashboard")

def setup_sidebar():
    st.sidebar.title("⚙️ Configuration")
    euri_api_key = st.sidebar.text_input("🔑 Enter your EURI API Key", type="password")
    return {"euri_api_key": euri_api_key}

def create_tabs():
    return st.tabs([
        "📄 Resume Analysis",
        "💬 Resume Q&A",
        "🎯 Interview Questions",
        "📈 Resume Improvement",
        "📝 Improved Resume"
    ])

def role_selection_section(role_requirements):
    st.subheader("🎯 Select Target Role")
    role = st.selectbox("Select a role for analysis:", list(role_requirements.keys()))
    st.markdown("Or upload a custom Job Description (JD) below:")
    custom_jd = st.file_uploader("Upload custom JD (optional):", type=["pdf", "txt"])
    return role, custom_jd

def resume_upload_section():
    st.subheader("📤 Upload Resume")
    uploaded_resume = st.file_uploader("Upload your resume (PDF or TXT):", type=["pdf", "txt"])
    return uploaded_resume

def display_analysis_results(results):
    st.success("✅ Resume analysis completed successfully!")

    # 📊 Overall Score
    st.markdown(f"### 🌟 Overall Score: **{results['overall_score']}%**")
    st.progress(results["overall_score"] / 100)

    # 🎯 Selection Status
    if results['selected']:
        st.markdown("🎉 **Status: Selected** ✅")
    else:
        st.markdown("⚠️ **Status: Not Selected** ❌")

    # 🏆 Strengths
    st.markdown("### 🏆 Strengths")
    if results['strengths']:
        st.markdown(", ".join([f"✅ **{s}**" for s in results['strengths']]))
    else:
        st.markdown("No strengths identified.")

    # ❌ Missing Skills
    st.markdown("### ❌ Missing Skills")
    if results['missing_skills']:
        st.markdown(", ".join([f"⚠️ **{s}**" for s in results['missing_skills']]))
    else:
        st.markdown("🎉 No missing skills!")

    # 📈 Skill Scores Table
    st.markdown("### 📊 Skill Proficiency")
    skill_data = {
        "Skill": list(results["skill_scores"].keys()),
        "Score (/10)": list(results["skill_scores"].values())
    }
    st.dataframe(skill_data, use_container_width=True)

    # 📝 Skill Reasoning
    with st.expander("🔍 View Detailed Reasoning for Each Skill"):
        for skill, reasoning in results["skill_reasoning"].items():
            st.markdown(f"**{skill}**: {reasoning}")

def resume_qa_section(has_resume, ask_question_func):
    st.subheader("💬 Ask Questions About Your Resume")
    if has_resume:
        question = st.text_input("Enter your question:")
        if st.button("💬 Ask"):
            if question:
                response = ask_question_func(question)
                st.markdown(f"📝 **Answer:** {response}")
            else:
                st.warning("⚠️ Please enter a question.")
    else:
        st.warning("⚠️ Please analyze a resume first.")


def interview_questions_section(has_resume, generate_questions_func):
    st.subheader("🎯 Generate Interview Questions")
    if has_resume:
        question_types = st.multiselect(
            "Select question types:", 
            ["Technical", "Behavioral", "Situational"], 
            default=["Technical"]
        )
        difficulty = st.selectbox("Select difficulty level:", ["Easy", "Medium", "Hard"])
        num_questions = st.slider("Number of questions:", min_value=1, max_value=10, value=5)

        if st.button("🚀 Generate Questions"):
            raw_questions = generate_questions_func(question_types, difficulty, num_questions)
            
            # Split big string response into list
            if isinstance(raw_questions, str):
                questions = [q.strip() for q in raw_questions.split("\n") if q.strip()]
            else:
                questions = raw_questions

            if questions:
                st.markdown("### 📑 Generated Interview Questions")
                for idx, q in enumerate(questions, 1):
                    with st.expander(f"❓ Question {idx}"):
                        st.markdown(q)
                        st.code(q, language="markdown")
            else:
                st.error("⚠️ No questions generated. Try again.")
    else:
        st.warning("⚠️ Please analyze a resume first.")


def resume_improvement_section(has_resume, improve_resume_func):
    st.subheader("📈 Get Resume Improvement Suggestions")
    if has_resume:
        improvement_areas = st.multiselect(
            "Select areas for improvement:",
            ["Grammar", "Clarity", "Keyword Optimization", "Formatting", "Achievements Highlight"]
        )
        target_role = st.text_input("Target Role (optional):")

        if st.button("✨ Get Suggestions"):
            suggestions = improve_resume_func(improvement_areas, target_role)
            if suggestions:
                st.markdown("### 📝 Suggestions")
                for area, suggestion in suggestions.items():
                    st.markdown(f"**{area}:** {suggestion}")
            else:
                st.error("⚠️ No improvement suggestions found.")
    else:
        st.warning("⚠️ Please analyze a resume first.")

def improved_resume_section(has_resume, get_improved_resume_func):
    st.subheader("📝 Get an Improved Resume")
    if has_resume:
        target_role = st.text_input("Enter Target Role:")
        highlight_skills = st.multiselect("Select skills to highlight:", [])

        if st.button("🚀 Generate Improved Resume"):
            improved_resume = get_improved_resume_func(target_role, highlight_skills)
            st.markdown("### 📄 Preview of Improved Resume")
            st.text_area("Improved Resume", improved_resume, height=300)

            st.download_button(
                label="💾 Download Improved Resume",
                data=improved_resume,
                file_name="improved_resume.txt",
                mime="text/plain"
            )
    else:
        st.warning("⚠️ Please analyze a resume first.")
