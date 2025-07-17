import streamlit as st

# This MUST be the first Streamlit command
st.set_page_config(
    page_title="MWASIQ AI Recruitment Agent",
    page_icon="🚀",
    layout="wide"
)

import ui
from agents import ResumeAnalysisAgent
import atexit

# Role requirements dictionary
ROLE_REQUIREMENTS = {
    "AI/ML Engineer": [
        "Python", "PyTorch", "TensorFlow", "Machine Learning", "Deep Learning",
        "MLOps", "Scikit-Learn", "NLP", "Computer Vision", "Reinforcement Learning",
        "Hugging Face", "Data Engineering", "Feature Engineering", "AutoML"
    ],
    "Frontend Engineer": [
        "React", "Vue", "Angular", "HTML5", "CSS3", "JavaScript", "TypeScript",
        "Next.js", "Svelte", "Bootstrap", "Tailwind CSS", "GraphQL", "Redux",
        "WebAssembly", "Three.js", "Performance Optimization"
    ],
    "Backend Engineer": [
        "Python", "Java", "Node.js", "REST APIs", "Cloud services", "Kubernetes",
        "Docker", "GraphQL", "Microservices", "gRPC", "Spring Boot", "Flask",
        "FastAPI", "SQL & NoSQL Databases", "Redis", "RabbitMQ", "CI/CD"
    ],
    "Data Engineer": [
        "Python", "SQL", "Apache Spark", "Hadoop", "Kafka", "ETL Pipelines",
        "Airflow", "BigQuery", "Redshift", "Data Warehousing", "Snowflake",
        "Azure Data Factory", "GCP", "AWS Glue", "DBT"
    ],
    "DevOps Engineer": [
        "Kubernetes", "Docker", "Terraform", "CI/CD", "AWS", "Azure", "GCP",
        "Jenkins", "Ansible", "Prometheus", "Grafana", "Helm", "Linux Administration",
        "Networking", "Site Reliability Engineering (SRE)"
    ],
    "Full Stack Developer": [
        "JavaScript", "TypeScript", "React", "Node.js", "Express", "MongoDB",
        "SQL", "HTML5", "CSS3", "RESTful APIs", "Git", "CI/CD", "Cloud Services",
        "Responsive Design", "Authentication & Authorization"
    ],
    "Product Manager": [
        "Product Strategy", "User Research", "Agile Methodologies", "Roadmapping",
        "Market Analysis", "Stakeholder Management", "Data Analysis", "User Stories",
        "Product Lifecycle", "A/B Testing", "KPI Definition", "Prioritization",
        "Competitive Analysis", "Customer Journey Mapping"
    ],
    "Data Scientist": [
        "Python", "R", "SQL", "Machine Learning", "Statistics", "Data Visualization",
        "Pandas", "NumPy", "Scikit-learn", "Jupyter", "Hypothesis Testing",
        "Experimental Design", "Feature Engineering", "Model Evaluation"
    ]
}

# Initialize session state variables
if 'resume_agent' not in st.session_state:
    st.session_state.resume_agent = None

if 'resume_analyzed' not in st.session_state:
    st.session_state.resume_analyzed = False

if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None

def setup_agent(config):
    """Set up the resume analysis agent with the provided configuration"""
    if not config["euri_api_key"]:
        st.error("⚠️ Please enter your EURI API KEY in the sidebar.")
        return None

    if st.session_state.resume_agent is None:
        st.session_state.resume_agent = ResumeAnalysisAgent(api_key=config["euri_api_key"])
    else:
        st.session_state.resume_agent.api_key = config["euri_api_key"]

    return st.session_state.resume_agent

def analyze_resume(agent, resume_file, role, custom_jd):
    """Analyze the resume with the agent"""
    if not resume_file:
        st.error("⚠️ Please upload a resume.")
        return None

    try:
        with st.spinner("🔍 Analyzing resume... This may take a minute."):

            result = agent.analyze_resume(
                resume_file,
                custom_jd=custom_jd if custom_jd else None,
                role_requirements=ROLE_REQUIREMENTS.get(role) if not custom_jd else None
            )
            st.session_state.resume_analyzed = True
            st.session_state.analysis_result = result
            return result
    except Exception as e:
        st.error(f"❌ Error analyzing resume: {e}")
        return None

def safe_call(func, *args, **kwargs):
    """Safely call a function and handle AttributeError"""
    try:
        return func(*args, **kwargs)
    except AttributeError:
        st.error("⚠️ This feature is not yet implemented in the backend.")
        return None
    except Exception as e:
        st.error(f"❌ Error: {e}")
        return None

def cleanup():
    """Clean up resources when the app exits"""
    if st.session_state.resume_agent:
        st.session_state.resume_agent.cleanup()

atexit.register(cleanup)

def main():
    ui.setup_page()
    ui.display_header()

    config = ui.setup_sidebar()
    agent = setup_agent(config)
    tabs = ui.create_tabs()

    # Tab 1: Resume Analysis
    with tabs[0]:
        role, custom_jd = ui.role_selection_section(ROLE_REQUIREMENTS)
        uploaded_resume = ui.resume_upload_section()

        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🔍 Analyze Resume", type="primary"):
                if agent and uploaded_resume:
                    analyze_resume(agent, uploaded_resume, role, custom_jd)

        if st.session_state.analysis_result:
            ui.display_analysis_results(st.session_state.analysis_result)

    # Tab 2: Resume Q&A
    with tabs[1]:
        if st.session_state.resume_analyzed and st.session_state.resume_agent:
            ui.resume_qa_section(
                has_resume=True,
                ask_question_func=lambda q: safe_call(st.session_state.resume_agent.ask_question, q)
            )
        else:
            st.warning("Please analyze a resume first in the 'Resume Analysis' tab.")

    # Tab 3: Interview Questions
    with tabs[2]:
        if st.session_state.resume_analyzed and st.session_state.resume_agent:
            ui.interview_questions_section(
                has_resume=True,
                generate_questions_func=lambda t, d, n: safe_call(
                    getattr(st.session_state.resume_agent, "generate_interview_questions", lambda *a, **k: None),
                    t, d, n
                )
            )
        else:
            st.warning("Please analyze a resume first in the 'Resume Analysis' tab.")

    # Tab 4: Resume Improvement
    with tabs[3]:
        if st.session_state.resume_analyzed and st.session_state.resume_agent:
            ui.resume_improvement_section(
                has_resume=True,
                improve_resume_func=lambda areas, role: safe_call(
                    getattr(st.session_state.resume_agent, "improve_resume", lambda *a, **k: None),
                    areas, role
                )
            )
        else:
            st.warning("Please analyze a resume first in the 'Resume Analysis' tab.")

    # Tab 5: Improved Resume
    with tabs[4]:
        if st.session_state.resume_analyzed and st.session_state.resume_agent:
            ui.improved_resume_section(
                has_resume=True,
                get_improved_resume_func=lambda role, skills: safe_call(
                    getattr(st.session_state.resume_agent, "get_improved_resume", lambda *a, **k: "Feature not implemented."),
                    role, skills
                )
            )
        else:
            st.warning("Please analyze a resume first in the 'Resume Analysis' tab.")

if __name__ == "__main__":
    main()
