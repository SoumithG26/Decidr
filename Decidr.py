import streamlit as st
import requests
import json
from datetime import datetime

# Configure page
st.set_page_config(
    page_title="Decidr - AI Decision Assistant",
    page_icon="🤔",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_URL = "https://router.huggingface.co/v1/chat/completions"

def get_headers():
    """Get headers for API requests"""
    try:
        hf_token = st.secrets["HF_TOKEN"]
    except KeyError:
        st.error("HF_TOKEN not found in secrets.toml. Please add it to your Streamlit secrets.")
        st.info("Add the following to your .streamlit/secrets.toml file:\n\n```\nHF_TOKEN = \"your_token_here\"\n```")
        st.stop()
    
    return {
        "Authorization": f"Bearer {hf_token}",
        "Content-Type": "application/json"
    }

def query_ai(messages, model="Qwen/Qwen3-VL-8B-Instruct:novita"):
    """accounts/fireworks/models/llama-v3p1-8b-instruct"""
    """Query the AI model with conversation history"""
    payload = {
        "messages": messages,
        "model": model,
        "max_tokens": 500,
        "temperature": 0.7,
        "stream": False
    }
    
    try:
        response = requests.post(API_URL, headers=get_headers(), json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API request failed: {str(e)}")
        return None
    except json.JSONDecodeError as e:
        st.error(f"Failed to parse API response: {str(e)}")
        return None

def initialize_session_state():
    """Initialize session state variables"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "decision_context" not in st.session_state:
        st.session_state.decision_context = ""
    if "current_decision" not in st.session_state:
        st.session_state.current_decision = ""

def create_system_prompt(decision_context=""):
    """Create a system prompt for decision-making assistance"""
    base_prompt = """You are Decidr, an expert decision-making assistant. Your role is to help users make thoughtful, well-informed decisions by:

1. Asking clarifying questions to understand the situation fully
2. Helping identify pros and cons
3. Considering different perspectives and potential outcomes
4. Suggesting decision-making frameworks when appropriate
5. Providing objective analysis while respecting the user's values and preferences

Be conversational, empathetic, and practical. Ask one question at a time to avoid overwhelming the user. Help them think through their decision systematically."""

    if decision_context:
        base_prompt += f"\n\nCurrent decision context: {decision_context}"
    
    return base_prompt

def main():
    initialize_session_state()
    
    # Header
    st.title("🤔 Decidr")
    st.markdown("### Your AI-powered decision-making assistant")
    
    # Sidebar for decision context and controls
    with st.sidebar:
        st.header("Decision Setup")
        
        # Decision context input
        decision_context = st.text_area(
            "What decision are you trying to make?",
            value=st.session_state.decision_context,
            placeholder="e.g., Should I change careers? Which apartment should I rent? What should I study in college?",
            height=100
        )
        
        if decision_context != st.session_state.decision_context:
            st.session_state.decision_context = decision_context
        
        # Start new decision button
        if st.button("🔄 Start New Decision", type="primary"):
            st.session_state.messages = []
            st.session_state.current_decision = decision_context
            if decision_context:
                # Add initial system message
                initial_messages = [
                    {"role": "system", "content": create_system_prompt(decision_context)},
                    {"role": "user", "content": f"I need help deciding: {decision_context}"}
                ]
                
                # Get AI's initial response
                with st.spinner("Getting AI response..."):
                    response = query_ai(initial_messages)
                    if response and "choices" in response:
                        ai_message = response["choices"][0]["message"]["content"]
                        st.session_state.messages = [
                            {"role": "user", "content": f"I need help deciding: {decision_context}"},
                            {"role": "assistant", "content": ai_message}
                        ]
            st.rerun()
        
        # Clear conversation button
        if st.button("🗑️ Clear Conversation"):
            st.session_state.messages = []
            st.rerun()
        
        # Decision-making tips
        st.markdown("---")
        st.header("💡 Decision Tips")
        st.markdown("""
        **Good decisions often involve:**
        - Clearly defining the problem
        - Identifying your values and priorities
        - Considering multiple options
        - Weighing pros and cons
        - Thinking about long-term consequences
        - Getting input from trusted sources
        - Setting a decision deadline
        """)
    
    # Main chat interface
    st.markdown("---")
    
    # Display conversation history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask for help with your decision..."):
        # Add user message to conversation
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Prepare messages for AI (include system prompt)
        ai_messages = [{"role": "system", "content": create_system_prompt(st.session_state.decision_context)}]
        ai_messages.extend(st.session_state.messages)
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = query_ai(ai_messages)
                
                if response and "choices" in response:
                    ai_message = response["choices"][0]["message"]["content"]
                    st.markdown(ai_message)
                    
                    # Add AI response to conversation
                    st.session_state.messages.append({"role": "assistant", "content": ai_message})
                else:
                    st.error("Sorry, I couldn't get a response. Please try again.")
    
    # Show helpful prompts if conversation is empty
    if not st.session_state.messages:
        st.markdown("### 🚀 Get Started")
        st.markdown("To begin, either:")
        st.markdown("1. **Describe your decision** in the sidebar and click 'Start New Decision'")
        st.markdown("2. **Ask a question** directly in the chat below")
        
        # Example decision scenarios
        st.markdown("### 📝 Example Decision Scenarios")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🏠 Moving Decision", use_container_width=True):
                example_prompt = "I'm trying to decide whether to move to a new city for a job opportunity. Can you help me think through this decision?"
                st.session_state.messages.append({"role": "user", "content": example_prompt})
                st.rerun()
        
        with col2:
            if st.button("🎓 Education Choice", use_container_width=True):
                example_prompt = "I'm having trouble choosing between different college majors. How should I approach this decision?"
                st.session_state.messages.append({"role": "user", "content": example_prompt})
                st.rerun()
        
        with col3:
            if st.button("💼 Career Change", use_container_width=True):
                example_prompt = "I'm considering changing careers but I'm not sure if it's the right move. Can you help me evaluate this?"
                st.session_state.messages.append({"role": "user", "content": example_prompt})
                st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666;'>"
        "Decidr helps you make better decisions through AI-powered conversation. "
        "Remember, the final decision is always yours! 🎯"
        "</div>", 
        unsafe_allow_html=True
    )

if __name__ == "__main__":

    main()

