"""
AI Resume Feedback Tool - Improved Personal Dashboard
One-time processing with cached data and simple selection interface
"""

import streamlit as st
import time
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Import our modules
from src.data_manager import DataManager
from src.latex_parser import LaTeXProjectParser
from src.llm_pipeline import LLMPipeline
from src.utils import extract_keywords_from_text, format_score
from config.settings import PAGE_TITLE, PAGE_ICON, LAYOUT

# Configure Streamlit
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout=LAYOUT,
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'data_manager' not in st.session_state:
    st.session_state.data_manager = None
if 'llm_pipeline' not in st.session_state:
    st.session_state.llm_pipeline = None
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None

def initialize_system():
    """Initialize the system components"""
    if st.session_state.data_manager is None:
        try:
            with st.spinner("🚀 Initializing system..."):
                st.session_state.data_manager = DataManager()
                st.session_state.llm_pipeline = LLMPipeline()
                
                # Test LLM connection
                if not st.session_state.llm_pipeline.test_connection():
                    st.error("❌ LLM connection failed. Please check Ollama is running.")
                    return False
                
                st.success("✅ System initialized successfully!")
                return True
        except Exception as e:
            st.error(f"❌ System initialization failed: {str(e)}")
            return False
    return True

def create_score_gauge(score, title, key_suffix=""):
    """Create a gauge chart for scores"""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': title},
        delta = {'reference': 80},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 50], 'color': "lightgray"},
                {'range': [50, 80], 'color': "yellow"},
                {'range': [80, 100], 'color': "green"}],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90}
        }))
    
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))
    return fig

def analyze_resume_with_projects(resume_data, selected_projects, job_description):
    """Analyze resume against job with selected projects"""
    try:
        # Reconstruct LaTeX format for analysis
        latex_content = ""
        parser = LaTeXProjectParser()
        
        for project in selected_projects:
            # Reconstruct LaTeX format for analysis
            tech_stack_str = ', '.join(project['tech_stack'])
            latex_project = f"""\\resumeProjectHeading
  {{\\textbf{{{project['name']}}} $|$ \\emph{{{tech_stack_str}}}}}{{{project['date_range']}}}
  \\resumeItemListStart"""
            
            for desc_point in project['description_points']:
                latex_project += f"\n    \\resumeItem{{{desc_point}}}"
            
            latex_project += "\n  \\resumeItemListEnd\n\n"
            latex_content += latex_project
        
        # Parse the reconstructed LaTeX
        parsed_projects = parser.parse_projects_from_latex(latex_content)
        
        if not parsed_projects:
            st.error("Failed to parse selected projects")
            return None
        
        # Rank projects by job relevance
        ranked_projects = parser.rank_projects_for_job(parsed_projects, job_description, top_k=len(parsed_projects))
        
        # Analyze resume content if available
        resume_content = resume_data.get('full_text', '')
        resume_analysis = {}
        
        if resume_content and len(resume_content) > 100:
            try:
                resume_analysis = st.session_state.llm_pipeline.analyze_resume(resume_content, job_description)
            except Exception as e:
                st.warning(f"Resume analysis failed: {e}")
                resume_analysis = {
                    'overall_score': 75,
                    'clarity': {'score': 75, 'feedback': 'Analysis focused on project matching', 'suggestions': []},
                    'role_alignment': {'score': 70, 'feedback': 'See project rankings below', 'suggestions': []},
                    'tone': {'score': 75, 'feedback': 'Professional presentation', 'suggestions': []}
                }
        
        # Project recommendations (all selected projects with scores)
        project_recommendations = []
        for ranked_project in ranked_projects:
            relevance_emoji = "🏆" if ranked_project['overall_score'] >= 80 else "⭐" if ranked_project['overall_score'] >= 60 else "💡"
            
            project_recommendations.append({
                'project_name': ranked_project['project_name'],
                'relevance_score': ranked_project['overall_score'],
                'why_better': f"{relevance_emoji} {ranked_project['overall_score']:.1f}% relevance | Key matches: {', '.join(ranked_project['matched_keywords'][:3])}",
                'key_skills': ranked_project['matched_keywords'],
                'tech_stack': ranked_project['tech_stack']
            })
        
        # Get missing keywords
        job_keywords = extract_keywords_from_text(job_description)
        project_keywords = []
        for proj in parsed_projects:
            project_keywords.extend(parser.extract_keywords_from_project(proj))
        
        missing = list(set(job_keywords) - set(project_keywords))[:10]
        missing_keywords = [
            {
                'keyword': kw,
                'category': 'Technical',
                'importance': 'high' if kw in job_keywords[:5] else 'medium'
            }
            for kw in missing
        ]
        
        # Improve top 3 project descriptions
        improved_projects = []
        if len(ranked_projects) >= 1:
            try:
                top_descriptions = []
                for ranked_proj in ranked_projects[:3]:
                    for parsed_proj in parsed_projects:
                        if parsed_proj.name == ranked_proj['project_name']:
                            top_descriptions.append(f"{parsed_proj.name}: {parsed_proj.get_full_description()}")
                            break
                
                if top_descriptions:
                    phrasing_result = st.session_state.llm_pipeline.improve_project_phrasing(
                        top_descriptions,
                        job_keywords[:10],
                        job_description
                    )
                    
                    # Handle both successful JSON and failed JSON responses
                    if phrasing_result and 'improved_projects' in phrasing_result:
                        improved_projects = phrasing_result['improved_projects']
                    elif phrasing_result and 'raw_response' in phrasing_result:
                        # Try to extract improved projects from raw response
                        raw_text = phrasing_result['raw_response']
                        if 'improved' in raw_text.lower():
                            # Create basic improved projects structure
                            improved_projects = [
                                {
                                    'original': f"Project {i+1} description",
                                    'improved': f"Enhanced version available in logs (JSON parsing failed)",
                                    'added_keywords': job_keywords[:3],
                                    'note': 'Check terminal logs for full improved descriptions'
                                }
                                for i in range(min(3, len(top_descriptions)))
                            ]
            except Exception as e:
                st.warning(f"Project phrasing improvement failed: {e}")
                logger.error(f"Detailed error: {e}")
                # Add debug info
                improved_projects = [
                    {
                        'original': 'Project improvement attempted',
                        'improved': f'Error occurred: {str(e)}',
                        'added_keywords': [],
                        'note': 'Check terminal logs for debugging info'
                    }
                ]
        
        # Calculate overall score
        if ranked_projects:
            top_scores = [p['overall_score'] for p in ranked_projects[:3]]
            project_avg = int(sum(top_scores) / len(top_scores))
            
            # If we have resume analysis, combine scores
            if resume_analysis and 'overall_score' in resume_analysis:
                resume_score = format_score(resume_analysis['overall_score'])
                # Weight: 60% project relevance, 40% resume analysis
                overall_score = int(project_avg * 0.6 + resume_score * 0.4)
            else:
                overall_score = project_avg
        else:
            # Fallback to resume analysis score or default
            if resume_analysis and 'overall_score' in resume_analysis:
                overall_score = format_score(resume_analysis['overall_score'])
            else:
                overall_score = 70
        
        return {
            'overall_score': overall_score,
            'resume_analysis': resume_analysis,
            'project_recommendations': project_recommendations,
            'missing_keywords': missing_keywords,
            'improved_projects': improved_projects,
            'processing_time': 0  # Not tracking time for cached analysis
        }
        
    except Exception as e:
        st.error(f"Analysis failed: {str(e)}")
        return None

def main():
    """Main application"""
    
    # Header
    st.title("🤖 AI Resume Feedback Tool")
    st.markdown("*Personal Dashboard - Cached Resume & Project Analysis*")
    
    # Initialize system
    if not initialize_system():
        st.stop()
    
    # Sidebar for data management
    with st.sidebar:
        st.header("📁 Data Management")
        
        # Show system stats
        try:
            stats = st.session_state.data_manager.get_system_stats()
            st.metric("📄 Resumes", stats['resumes_cached'])
            st.metric("🏗️ Projects", stats['total_projects'])
            st.metric("💾 Cache Size", f"{stats['cache_size_mb']:.1f} MB")
        except Exception as e:
            st.error(f"Stats error: {e}")
        
        # Refresh data button
        if st.button("🔄 Refresh Data", help="Scan for new/changed files"):
            with st.spinner("🔄 Refreshing data..."):
                try:
                    results = st.session_state.data_manager.refresh_all_data()
                    
                    st.success("✅ Data refreshed!")
                    st.json({
                        "Resumes": f"{results['resumes']['processed']} processed, {results['resumes']['cached']} cached",
                        "Projects": f"{results['projects']['processed']} processed, {results['projects']['cached']} cached"
                    })
                except Exception as e:
                    st.error(f"Refresh failed: {e}")
    
    # Main interface
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("📄 Select Resume")
        
        # Get available resumes
        try:
            available_resumes = st.session_state.data_manager.get_available_resumes()
            
            if not available_resumes:
                st.warning("No resumes found. Add PDF/DOCX files to data/resumes/ folder and refresh.")
                st.stop()
            
            # Resume selection
            resume_options = {f"{r['filename']} ({r['character_count']} chars)": r['key'] for r in available_resumes}
            
            selected_resume_display = st.selectbox(
                "Choose your resume:",
                options=list(resume_options.keys()),
                help="Select which resume to analyze"
            )
            
            selected_resume_key = resume_options[selected_resume_display]
            
            # Show resume details
            resume_data = st.session_state.data_manager.get_resume_content(selected_resume_key)
            if resume_data:
                with st.expander("📋 Resume Details"):
                    st.write(f"**Sections found:** {', '.join(resume_data.get('sections_found', []))}")
                    st.write(f"**Processed:** {resume_data.get('processed_date', 'Unknown')}")
                    st.write(f"**Character count:** {resume_data.get('character_count', 0):,}")
            
        except Exception as e:
            st.error(f"Error loading resumes: {e}")
            st.stop()
    
    with col2:
        st.header("🏗️ Select Projects")
        
        # Get available projects
        try:
            available_projects = st.session_state.data_manager.get_available_projects()
            
            if not available_projects:
                st.warning("No projects found. Add .tex files to data/projects/ folder and refresh.")
                selected_projects = []
            else:
                # Project selection with multiselect
                project_options = {}
                for proj in available_projects:
                    display_name = f"{proj['name']} | {', '.join(proj['tech_stack'][:3])}"
                    project_options[display_name] = f"{proj['file_key']}_{proj['name']}"
                
                selected_project_keys = st.multiselect(
                    "Choose projects to include:",
                    options=list(project_options.keys()),
                    default=list(project_options.keys())[:3],  # Select first 3 by default
                    help="Select which projects to analyze against the job"
                )
                
                # Get selected project data
                selected_project_ids = [project_options[key] for key in selected_project_keys]
                selected_projects = st.session_state.data_manager.get_selected_projects(selected_project_ids)
                
                # Show selected projects
                if selected_projects:
                    with st.expander(f"📋 Selected Projects ({len(selected_projects)})"):
                        for proj in selected_projects:
                            st.write(f"**{proj['name']}** - {', '.join(proj['tech_stack'])}")
        
        except Exception as e:
            st.error(f"Error loading projects: {e}")
            selected_projects = []
    
    # Job Description Input
    st.header("💼 Job Description")
    job_description = st.text_area(
        "Paste the job description:",
        height=200,
        placeholder="Enter the complete job description including requirements, responsibilities, and desired skills...",
        help="The more detailed the job description, the better the analysis"
    )
    
    # Analysis Section
    st.header("🚀 Analysis")
    
    if st.button("🎯 Analyze Resume vs Job", type="primary", use_container_width=True):
        if not job_description.strip():
            st.error("Please enter a job description.")
        elif not selected_projects:
            st.error("Please select at least one project.")
        else:
            with st.spinner("🤖 Running analysis..."):
                results = analyze_resume_with_projects(resume_data, selected_projects, job_description)
                
                if results:
                    st.session_state.analysis_results = results
    
    # Display Results
    if st.session_state.analysis_results:
        results = st.session_state.analysis_results
        
        st.markdown("---")
        st.header("📊 Analysis Results")
        
        # Score gauges
        col1, col2, col3 = st.columns(3)
        
        with col1:
            fig = create_score_gauge(results['overall_score'], "Overall Score")
            st.plotly_chart(fig, use_container_width=True, key="gauge_overall")
        
        with col2:
            if results['resume_analysis'] and 'clarity' in results['resume_analysis']:
                clarity_score = results['resume_analysis']['clarity'].get('score', 70)
                fig = create_score_gauge(clarity_score, "Clarity")
                st.plotly_chart(fig, use_container_width=True, key="gauge_clarity")
        
        with col3:
            if results['resume_analysis'] and 'role_alignment' in results['resume_analysis']:
                alignment_score = results['resume_analysis']['role_alignment'].get('score', 70)
                fig = create_score_gauge(alignment_score, "Role Alignment")
                st.plotly_chart(fig, use_container_width=True, key="gauge_alignment")
        
        # Detailed results in tabs
        tab1, tab2, tab3, tab4 = st.tabs(["🏆 Project Rankings", "🔍 Missing Keywords", "✨ Improved Phrasing", "📝 Resume Feedback"])
        
        with tab1:
            st.subheader("🏆 Your Projects Ranked by Relevance")
            
            for i, proj in enumerate(results['project_recommendations'], 1):
                score = proj['relevance_score']
                
                if score >= 80:
                    color = "🟢"
                elif score >= 60:
                    color = "🟡"
                else:
                    color = "🔴"
                
                with st.expander(f"{color} #{i}: {proj['project_name']} ({score:.1f}%)"):
                    st.markdown(proj['why_better'])
                    st.markdown(f"**Matching skills:** {', '.join(proj['key_skills'][:8])}")
                    st.markdown(f"**Tech stack:** {', '.join(proj['tech_stack'])}")
        
        with tab2:
            st.subheader("🔍 Keywords to Add")
            
            if results['missing_keywords']:
                # Group keywords by importance
                high_keywords = [kw for kw in results['missing_keywords'] if kw.get('importance') == 'high']
                medium_keywords = [kw for kw in results['missing_keywords'] if kw.get('importance') == 'medium']
                
                if high_keywords:
                    st.markdown("**High Priority:**")
                    for kw in high_keywords:
                        st.markdown(f"• **{kw['keyword']}**")
                
                if medium_keywords:
                    st.markdown("**Medium Priority:**")
                    for kw in medium_keywords:
                        st.markdown(f"• {kw['keyword']}")
            else:
                st.success("Great! No critical keywords missing.")
        
        with tab3:
            st.subheader("✨ Improved Project Descriptions")
            
            if results['improved_projects']:
                for i, proj in enumerate(results['improved_projects'], 1):
                    st.markdown(f"**Project {i}:**")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("**Original:**")
                        st.text_area(
                            "Original Description", 
                            proj.get('original', ''), 
                            height=150, 
                            key=f"orig_{i}", 
                            disabled=True,
                            label_visibility="collapsed"
                        )
                    
                    with col2:
                        st.markdown("**Improved:**")
                        st.text_area(
                            "Improved Description", 
                            proj.get('improved', ''), 
                            height=150, 
                            key=f"impr_{i}", 
                            disabled=True,
                            label_visibility="collapsed"
                        )
                    
                    if proj.get('added_keywords'):
                        st.markdown(f"**Added keywords:** {', '.join(proj['added_keywords'])}")
                    
                    if proj.get('note'):
                        st.info(proj['note'])
                    
                    st.markdown("---")
            else:
                st.info("Select projects and run analysis to see improvements.")
        
        with tab4:
            st.subheader("📝 Resume Analysis")
            
            if results['resume_analysis']:
                analysis = results['resume_analysis']
                
                for section in ['clarity', 'role_alignment', 'tone']:
                    if section in analysis:
                        data = analysis[section]
                        st.markdown(f"**{section.replace('_', ' ').title()}: {data.get('score', 0)}/100**")
                        st.write(data.get('feedback', 'No feedback available'))
                        
                        if data.get('suggestions'):
                            for suggestion in data['suggestions']:
                                st.markdown(f"• {suggestion}")
                        st.markdown("---")

if __name__ == "__main__":
    main()