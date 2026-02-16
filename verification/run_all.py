import subprocess
import sys
import os

def run_script(script_path):
    """Runs a Python script and prints its output."""
    print(f"--- Running {script_path} ---")
    try:
        # We run from the project root to ensure imports work correctly
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env = os.environ.copy()
        env["PYTHONPATH"] = project_root + os.pathsep + env.get("PYTHONPATH", "")
        
        result = subprocess.run(
            [sys.executable, script_path],
            cwd=project_root, # Run in project root
            env=env,
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        print(f"--- {script_path} PASSED ---\n")
        return True
    except subprocess.CalledProcessError as e:
        print(e.stdout)
        print(e.stderr)
        print(f"--- {script_path} FAILED ---\n")
        return False

def main():
    scripts = [
        "verification/verify_tools.py",
        "verification/verify_personalized_cost.py",
        "verification/verify_orchestrator.py"
    ]
    
    passed = 0
    for script in scripts:
        if run_script(script):
            passed += 1
            
    if passed == len(scripts):
        print("All verification scripts passed!")
        sys.exit(0)
    else:
        print(f"{len(scripts) - passed} script(s) failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
