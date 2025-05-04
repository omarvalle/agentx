import subprocess
import sys

def run_q_command():
    try:
        result = subprocess.run(['q', '--version'], capture_output=True, text=True)
        print(f"Success: {result.stdout}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    run_q_command()
