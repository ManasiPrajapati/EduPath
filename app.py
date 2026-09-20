import streamlit as st
from langchain_ollama import ChatOllama
from pypdf import PdfReader
import json

# --- Demo Mode Data ---
DEMO_PROFILE = {
    'current_skills': ['Python', 'SQL', 'Pandas', 'Basic HTML'],
    'experience_level': 'Intermediate',
    'target_role': 'AI Engineer'
}
DEMO_SKILL_GAPS = {
    'skill_gaps': [
        {'skill': 'Deep Learning', 'priority': 'High', 'reason': 'Core requirement for AI roles'},
        {'skill': 'PyTorch', 'priority': 'High', 'reason': 'Industry standard framework'},
        {'skill': 'MLOps', 'priority': 'Medium', 'reason': 'Needed for deploying models'}
    ]
}
DEMO_PLAN = {
    'weekly_plan': [
        {
            'week': 1, 'theme': 'Neural Network Foundations', 
            'objectives': ['Understand Perceptrons', 'Learn Backpropagation'], 
            'topics': ['Activation Functions', 'Loss Functions'], 
            'project': 'Build a Neural Network from scratch in NumPy', 
            'hours': 12, 
            'resources': ['3Blue1Brown Neural Networks', 'Fast.ai Lesson 1']
        },
        {
            'week': 2, 'theme': 'Mastering PyTorch', 
            'objectives': ['Learn PyTorch Tensors', 'Build CNNs'], 
            'topics': ['Autograd', 'DataLoaders'], 
            'project': 'Image Classifier using CIFAR-10', 
            'hours': 15, 
            'resources': ['Official PyTorch Tutorials', 'Sentdex PyTorch Playlist']
        }
    ]
}

# --- Page Configuration ---
st.set_page_config(page_title="EduPath - AI Learning Agent", layout="wide", page_icon="🎓")

st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        .stAppDeployButton {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        [data-testid="stToolbar"] {visibility: hidden;}
        .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    </style>
""", unsafe_allow_html=True)

st.title(" EduPath: Personalized Learning & Skill Gap Agent")
st.markdown("### Upload your resume, and let the AI build your career roadmap.")

# --- Initialize LLM ---
@st.cache_resource
def get_llm():
    return ChatOllama(model="qwen2.5:7b", temperature=0.3)

llm = get_llm()

# --- Sidebar ---
st.sidebar.header("⚡ Quick Actions")
if st.sidebar.button("🎬 Load Demo Data (For Video)"):
    st.session_state['user_profile'] = DEMO_PROFILE
    st.session_state['skill_gaps'] = DEMO_SKILL_GAPS
    st.session_state['learning_plan'] = DEMO_PLAN
    st.session_state['progress'] = {"week_1": "Completed", "week_2": "In Progress"}
    st.rerun()

# --- SECTION 1: Resume Upload ---
st.header("1️⃣ Profile Ingestion")
uploaded_file = st.file_uploader("Upload your Resume (PDF)", type=["pdf"])

if uploaded_file:
    with st.spinner("🤖 AI is reading your resume..."):
        pdf_reader = PdfReader(uploaded_file)
        resume_text = ""
        for page in pdf_reader.pages:
            resume_text += page.extract_text()
        
        extraction_prompt = f"""
        Analyze the following resume text and extract the user's profile.
        Resume Text: {resume_text}
        Return ONLY a valid JSON object with keys: "current_skills" (list), "experience_level", "target_role".
        Do not include markdown. Just return raw JSON.
        """
        
        response = llm.invoke(extraction_prompt)
        raw_json = response.content.replace("```json", "").replace("```", "").strip()
        
        try:
            user_profile = json.loads(raw_json)
            st.success("✅ Resume parsed successfully!")
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("👤 Extracted Profile")
                st.write(f"**Experience Level:** {user_profile['experience_level']}")
                st.write(f"**Target Role:** {user_profile['target_role']}")
            with col2:
                st.subheader("️ Current Skills")
                for skill in user_profile['current_skills']:
                    st.markdown(f"- {skill}")
            
            st.session_state['user_profile'] = user_profile
            
        except json.JSONDecodeError:
            st.error("⚠️ AI failed to parse the resume. Try a different PDF.")

# --- SECTION 2: Skill Gap & Plan ---
st.header("2️⃣ Skill Gap Analysis & Learning Plan")

if 'user_profile' in st.session_state:
    profile = st.session_state['user_profile']
    target_role_input = st.text_input("Target Role:", value=profile['target_role'])
    
    if st.button("🚀 Generate Personalized Learning Plan", type="primary"):
        with st.spinner("🧠 AI is analyzing skill gaps and building your 4-week curriculum..."):
            gap_analysis_prompt = f"""
            Analyze skill gaps. Current Skills: {', '.join(profile['current_skills'])}. Target Role: {target_role_input}.
            Identify 3-5 specific skill gaps.
            Return ONLY JSON: {{"skill_gaps": [{{"skill": "name", "priority": "High/Medium/Low", "reason": "why"}}]}}
            """
            gap_response = llm.invoke(gap_analysis_prompt)
            gap_json = gap_response.content.replace("```json", "").replace("```", "").strip()
            skill_gaps = json.loads(gap_json)
            
            plan_prompt = f"""
            Create a 4-week learning plan.
            Current Skills: {', '.join(profile['current_skills'])}
            Target Role: {target_role_input}
            Skill Gaps: {[gap['skill'] for gap in skill_gaps['skill_gaps']]}
            
            For EACH week, include objectives, topics, a practice project, and specific recommended resources.
            Return ONLY JSON:
            {{
                "weekly_plan": [
                    {{
                        "week": 1, "theme": "Theme", "objectives": ["obj1"], 
                        "topics": ["topic1"], "project": "Project desc", "hours": 10,
                        "resources": ["Resource 1", "Resource 2"]
                    }}
                ]
            }}
            """
            plan_response = llm.invoke(plan_prompt)
            plan_json = plan_response.content.replace("```json", "").replace("```", "").strip()
            learning_plan = json.loads(plan_json)
            
            st.session_state['learning_plan'] = learning_plan
            st.session_state['skill_gaps'] = skill_gaps
            st.rerun()

    if 'learning_plan' in st.session_state:
        st.success("✅ Personalized Learning Plan Generated!")
        
        st.subheader("🎯 Identified Skill Gaps")
        cols = st.columns(len(st.session_state['skill_gaps']['skill_gaps']))
        for idx, gap in enumerate(st.session_state['skill_gaps']['skill_gaps']):
            with cols[idx]:
                priority_color = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}
                st.markdown(f"**{priority_color.get(gap['priority'], '')} {gap['skill']}**")
                st.caption(f"{gap['reason']}")
        
        st.subheader("📅 Your 4-Week Learning Roadmap")
        for week in st.session_state['learning_plan']['weekly_plan']:
            with st.expander(f"**Week {week['week']}: {week['theme']}** ({week['hours']} hours)", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**📚 Objectives:**")
                    for obj in week['objectives']: st.markdown(f"- {obj}")
                    st.markdown("**📖 Topics:**")
                    for topic in week['topics']: st.markdown(f"  - {topic}")
                with col2:
                    st.markdown("**🛠️ Practice Project:**")
                    st.info(week['project'])
                    st.markdown("**🔗 Recommended Resources:**")
                    for res in week['resources']: st.markdown(f"- {res}")
else:
    st.warning(" Please upload a resume first.")

# --- SECTION 3: Progress Tracker & Report ---

st.header("3️⃣ Progress Tracker & Report")

if 'learning_plan' in st.session_state:
    st.subheader("Track Your Weekly Progress")
    
    # 1. Initialize progress tracking safely
    if 'progress' not in st.session_state:
        st.session_state['progress'] = {f"week_{week['week']}": "Not Started" for week in st.session_state['learning_plan']['weekly_plan']}

    # 2. Display Selectors
    for week in st.session_state['learning_plan']['weekly_plan']:
        week_key = f"week_{week['week']}"
        
        # Safety check to ensure key exists
        if week_key not in st.session_state['progress']:
            st.session_state['progress'][week_key] = "Not Started"

        current_status = st.session_state['progress'][week_key]
        options = ["Not Started", "In Progress", "Completed"]

        st.markdown(f"**Week {week['week']}: {week['theme']}**")
        selected_status = st.selectbox(
            f"Status for Week {week['week']}", 
            options,
            index=options.index(current_status),
            key=f"select_{week['week']}"
        )

        # Update state and force refresh if user changes status
        if selected_status != current_status:
            st.session_state['progress'][week_key] = selected_status
            st.rerun() 

        st.markdown("---")

    # 3. Generate Report with Error Handling
    if st.button("📊 Generate Progress Report", type="primary"):
        with st.spinner("🤖 AI is writing your progress report..."):
            try:
                report_prompt = f"""
                Learner Progress: {st.session_state['progress']}
                Learning Plan: {st.session_state['learning_plan']}
                
                Generate a short, motivational progress report. Highlight completed weeks, what's in progress, and what to focus on next. Keep it under 150 words.
                """
                report = llm.invoke(report_prompt)
                st.session_state['report'] = report.content
                st.rerun() # Force UI to update immediately with the new report
                
            except Exception as e:
                st.error(f"⚠️ AI failed to generate report. Make sure Ollama is running! Error: {e}")

    # 4. Display the Report
    if 'report' in st.session_state:
        st.subheader("📝 Your Progress Report")
        st.success(st.session_state['report'])
        st.markdown("---")
        st.info("💡 **Note:** PDF export feature will be available in the production version!")
        
else:
    st.info("Generate a learning plan to start tracking progress.")