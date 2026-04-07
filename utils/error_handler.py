import logging
import streamlit as st
import traceback
from datetime import datetime

# Configure logging
logging.basicConfig(
    filename='errors.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s',
    level=logging.ERROR
)
logger = logging.getLogger('TransitFlow')

class ErrorType:
    DATABASE_ERROR = "Database Error"
    ML_ERROR = "Machine Learning Error"
    PERMISSION_ERROR = "Permission Error"
    DATA_ERROR = "Data Processing Error"
    FILE_ERROR = "File System Error"
    UNKNOWN_ERROR = "Unknown System Error"

def log_error(error: Exception, error_type: str = ErrorType.UNKNOWN_ERROR, context: str = ""):
    """Logs the error to errors.log with full stack trace."""
    error_msg = f"[{error_type}] {context} - {str(error)}"
    logger.error(error_msg)
    logger.error(traceback.format_exc())

def show_user_friendly_error(error_type: str, custom_message: str = None):
    """Displays a safe, friendly error state in the Streamlit UI."""
    messages = {
        ErrorType.DATABASE_ERROR: "Unable to connect to the database. Please check your connection or contact IT.",
        ErrorType.ML_ERROR: "The AI Prediction Engine encountered an issue generating forecasts.",
        ErrorType.PERMISSION_ERROR: "You do not have the required permissions to perform this action.",
        ErrorType.DATA_ERROR: "We encountered invalid or missing data while processing this request.",
        ErrorType.FILE_ERROR: "There was a problem accessing or generating the requested file.",
        ErrorType.UNKNOWN_ERROR: "An unexpected error occurred."
    }
    
    msg = custom_message if custom_message else messages.get(error_type, messages[ErrorType.UNKNOWN_ERROR])
    st.error(f"🚨 **{error_type}**: {msg}")
    with st.expander("Need Help?"):
        st.write("If this issue persists, please contact the HMRL System Administrator at support@transitflow.hmrl.gov.in")

def safe_execute(error_type: str, fallback_return=None):
    """Decorator for safe execution of functions with centralized error handling."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                log_error(e, error_type, func.__name__)
                if st._is_running_with_streamlit:
                    show_user_friendly_error(error_type)
                return fallback_return
        return wrapper
    return decorator
