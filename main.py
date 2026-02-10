import sys
import os

# Get current directory and add to sys.path immediately
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def is_running_in_streamlit():
    """Check if the code is being executed by Streamlit"""
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        return get_script_run_ctx() is not None
    except ImportError:
        return False

if __name__ == "__main__":
    if is_running_in_streamlit():
        # We are inside a Streamlit process (e.g., Streamlit Cloud or local 'streamlit run')
        from ui.streamlit_app import main
        main()
    else:
        # We are launching via 'python main.py'
        import subprocess
        print("Launching Document Search application...")
        
        # Prepare environment with PYTHONPATH
        env = os.environ.copy()
        env["PYTHONPATH"] = current_dir + (os.pathsep + env.get("PYTHONPATH", "") if env.get("PYTHONPATH") else "")
        
        # Run streamlit via 'python -m streamlit run' to ensure same interpreter
        cmd = [sys.executable, "-m", "streamlit", "run", __file__]
        
        try:
            subprocess.run(cmd, env=env, check=True)
        except KeyboardInterrupt:
            print("\nStopping application...")
        except Exception as e:
            print(f"Error starting application: {e}")
            sys.exit(1)
else:
    # This block handles importing 'main.py' as a module, which Streamlit might do
    # In some Streamlit versions, the script is imported/executed.
    # To be safe for all environments, we import the logic here too.
    if is_running_in_streamlit():
        from ui.streamlit_app import main
        main()
