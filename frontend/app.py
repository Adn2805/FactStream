import streamlit as st
import requests
import os
import base64
from PIL import Image
import io

st.set_page_config(page_title="FactStream", page_icon="⚖️", layout="wide", initial_sidebar_state="collapsed")

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:8000")

# Premium Midnight Green Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;800&display=swap');

    /* Global Typography and Background */
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, #020b08 0%, #05261b 100%);
        color: #f8fafc;
    }

    /* Premium Header */
    .premium-header {
        font-size: clamp(2.5rem, 5vw, 4rem);
        font-weight: 800;
        background: -webkit-linear-gradient(45deg, #34d399, #10b981, #059669);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
        padding-bottom: 0px;
        line-height: 1.2;
    }
    .subtitle {
        color: #94a3b8;
        font-size: clamp(1rem, 2vw, 1.2rem);
        margin-top: -5px;
        margin-bottom: 30px;
        font-weight: 300;
    }

    /* Glassmorphism Cards */
    .metric-card {
        background: rgba(10, 40, 25, 0.4);
        border-radius: 16px;
        padding: 24px;
        border: 1px solid rgba(52, 211, 153, 0.15);
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        transition: transform 0.3s ease, box-shadow 0.3s ease, border-color 0.3s ease;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 40px rgba(16, 185, 129, 0.15);
        border-color: rgba(16, 185, 129, 0.5);
    }

    .metric-card h4 {
        color: #cbd5e1;
        font-size: 0.95rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 8px;
        font-weight: 500;
    }
    
    .metric-value {
        font-size: clamp(1.5rem, 3vw, 2rem);
        font-weight: 600;
        color: #ffffff;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 10px;
    }

    /* Verdict Colors */
    .verdict-true { color: #10b981; text-shadow: 0 0 15px rgba(16, 185, 129, 0.4); }
    .verdict-false { color: #ef4444; text-shadow: 0 0 15px rgba(239, 68, 68, 0.4); }
    .verdict-unverified { color: #fbbf24; text-shadow: 0 0 15px rgba(251, 191, 36, 0.4); }

    /* Customizing Streamlit Elements */
    .stTextArea textarea {
        background: rgba(4, 25, 15, 0.6) !important;
        border: 1px solid rgba(16, 185, 129, 0.2) !important;
        color: #f1f5f9 !important;
        border-radius: 12px !important;
        font-size: 1.05rem !important;
        padding: 16px !important;
        transition: all 0.3s ease !important;
    }
    .stTextArea textarea:focus {
        border-color: #10b981 !important;
        box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.3) !important;
    }
    
    .stTextInput input {
        background: rgba(4, 25, 15, 0.6) !important;
        border: 1px solid rgba(16, 185, 129, 0.2) !important;
        color: #f1f5f9 !important;
        border-radius: 12px !important;
        font-size: 1rem !important;
    }
    
    .stButton>button {
        background: linear-gradient(90deg, #059669, #10b981) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.85rem 2rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px !important;
        transition: all 0.3s ease !important;
        text-transform: uppercase !important;
        width: 100% !important;
        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3) !important;
    }
    .stButton>button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(16, 185, 129, 0.5) !important;
        background: linear-gradient(90deg, #10b981, #34d399) !important;
        border: none !important;
    }
    
    /* Rebuttal Box */
    .rebuttal-box {
        background: linear-gradient(145deg, rgba(6, 40, 25, 0.8), rgba(2, 20, 12, 0.95)); 
        border-left: 5px solid #10b981;
        border-radius: 12px;
        padding: 25px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        margin-top: 20px;
    }
    
    /* Empty State */
    .empty-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 300px;
        opacity: 0.6;
        border: 2px dashed rgba(16, 185, 129, 0.2);
        border-radius: 16px;
        background: rgba(0,0,0,0.1);
    }
    .empty-state i {
        font-size: 3.5rem;
        margin-bottom: 1rem;
        color: #34d399;
    }

    /* Mobile Responsiveness Rules */
    @media (max-width: 768px) {
        .metric-card {
            margin-bottom: 15px;
        }
        .stColumn {
            width: 100% !important;
        }
        .premium-header {
            text-align: center;
        }
        .subtitle {
            text-align: center;
            margin-bottom: 20px;
        }
        .empty-state {
            height: 200px;
        }
    }

</style>
<!-- Include FontAwesome -->
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="premium-header">FactStream</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">AI-Powered Multimodal Fact-Checking & Argument Analysis</div>', unsafe_allow_html=True)

st.write("---")

col1, col2 = st.columns([1.2, 2.5], gap="large")

with col1:
    st.markdown("### <i class='fa-solid fa-satellite-dish' style='color: #10b981;'></i> Input Stream", unsafe_allow_html=True)
    
    st.markdown("<p style='color: #94a3b8; font-size: 0.95rem; margin-bottom: -10px;'><i class='fa-brands fa-youtube'></i> Auto-Transcribe URL</p>", unsafe_allow_html=True)
    video_url = st.text_input("", placeholder="Paste a YouTube URL here...", label_visibility="collapsed")
    
    st.markdown("<div style='text-align: center; margin: 10px 0; color: #64748b; font-size: 0.9rem;'>— OR —</div>", unsafe_allow_html=True)
    
    st.markdown("<p style='color: #94a3b8; font-size: 0.95rem; margin-bottom: -10px;'><i class='fa-solid fa-microphone-lines'></i> Live Transcript</p>", unsafe_allow_html=True)
    transcript = st.text_area("", height=150, placeholder="Paste or type the speaker's argument here...", label_visibility="collapsed")
    
    st.write("")
    video_file = st.file_uploader("Upload Video Feed", type=["mp4", "mov", "avi"], help="Optional: Upload video to analyze gaze and micro-expressions.")
    
    st.write("")
    analyze_btn = st.button("Initialize Analysis \uf0e7") # FontAwesome lightning icon inside button

with col2:
    st.markdown("### <i class='fa-solid fa-network-wired' style='color: #10b981;'></i> Neural Analysis Engine", unsafe_allow_html=True)
    
    if not analyze_btn:
        st.markdown("""
        <div class="empty-state">
            <i class="fa-solid fa-satellite-dish fa-fade"></i>
            <p style="font-size: 1.1rem; letter-spacing: 1px; color: #94a3b8;">Awaiting Input Stream...</p>
        </div>
        """, unsafe_allow_html=True)
        
    if analyze_btn and (transcript or video_url):
        with st.spinner("Quantum processing across 5 neural models..."):
            try:
                # Send to Gateway
                files = {"video": video_file} if video_file else None
                data = {
                    "transcript": transcript,
                    "video_url": video_url
                }
                res = requests.post(f"{GATEWAY_URL}/analyze", data=data, files=files)
                
                if res.status_code == 200:
                    result = res.json()
                    
                    # Top Metrics
                    m1, m2, m3 = st.columns(3)
                    with m1:
                        st.markdown(f"""
                        <div class='metric-card'>
                            <h4><i class="fa-solid fa-brain" style="color: #10b981;"></i> Detected Fallacy</h4>
                            <p class="metric-value">{result['nlu_fallacy']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    with m2:
                        verdict_class = f"verdict-{result['fact_check_verdict'].lower()}"
                        icon = "fa-check-circle" if result['fact_check_verdict'].lower() == 'true' else "fa-times-circle" if result['fact_check_verdict'].lower() == 'false' else "fa-circle-question"
                        st.markdown(f"""
                        <div class='metric-card'>
                            <h4><i class="fa-solid fa-magnifying-glass" style="color: #34d399;"></i> Fact-Check</h4>
                            <p class='metric-value {verdict_class}'><i class="fa-solid {icon}"></i> {result['fact_check_verdict'].upper()}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    with m3:
                        score = result['scoring_data'].get('credibility_score', 0)
                        trend = result['scoring_data'].get('trend', 'stable')
                        trend_icon = "fa-arrow-trend-up" if "up" in trend.lower() else ("fa-arrow-trend-down" if "down" in trend.lower() or "declin" in trend.lower() else "fa-minus")
                        st.markdown(f"""
                        <div class='metric-card'>
                            <h4><i class="fa-solid fa-shield-halved" style="color: #059669;"></i> Credibility</h4>
                            <p class='metric-value'>{score:.1f} <span style="font-size: 1rem; color: #94a3b8;"><i class="fa-solid {trend_icon}"></i> {trend}</span></p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    st.write("")
                    
                    # Rebuttal
                    st.markdown(f"""
                    <div class='rebuttal-box'>
                        <h4 style="color: #34d399; font-size: 1.15rem; margin-top:0;"><i class="fa-solid fa-robot"></i> AI Counter-Argument</h4>
                        <p style="font-size: 1.15rem; line-height: 1.7; color: #f8fafc; font-weight: 300; margin-bottom:0;">{result['rebuttal']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.write("")
                    
                    # Time Series Chart
                    chart_b64 = result['scoring_data'].get('chart_base64', "")
                    if chart_b64:
                        image_bytes = base64.b64decode(chart_b64)
                        image = Image.open(io.BytesIO(image_bytes))
                        st.markdown("<h4 style='margin-top: 15px;'><i class='fa-solid fa-chart-line' style='color:#10b981;'></i> Behavior & Credibility Timeline</h4>", unsafe_allow_html=True)
                        st.image(image, use_column_width=True)
                        
                else:
                    st.error(f"Error {res.status_code}: {res.text}")
            except Exception as e:
                st.error(f"Failed to connect to Neural API Gateway: {e}")
