import streamlit as st

def register_shortcuts():
    """Injects JavaScript to handle keyboard bindings globally natively in the Streamlit DOM"""
    js = """
    <script>
    const userAgent = navigator.userAgent.toLowerCase();
    const isMac = userAgent.includes("mac");
    
    document.addEventListener('keydown', function(event) {
        // [Ctrl/Cmd + S] Save/Generate
        if ((event.ctrlKey || event.metaKey) && event.key === 's') {
            event.preventDefault();
            // Simulate clicking the first primary submit button on the screen
            let btns = Array.from(window.parent.document.querySelectorAll('button[kind="primary"]'));
            if(btns.length > 0) btns[0].click();
        }
    });
    </script>
    """
    st.markdown(js, unsafe_allow_html=True)
