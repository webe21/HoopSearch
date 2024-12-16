import os
import subprocess
import sys
import time

def run_training_indobert():
    print("Running Training Indobert using sentences.py...")
    subprocess.run(["python", "Training data/Training Indobert using sentences.py"], check=True)

def run_training_bart():
    print("Running Training BART Finetuning.py...")
    subprocess.run(["python", "Training data/BART Finetuning.py"], check=True)

def run_frontend():
    print("Starting frontend with 'npm start'...")
    subprocess.Popen("npm run start", shell = True, cwd="./Frontend")  # Menjalankan npm start di terminal frontend

def run_backend():
    print("Starting backend with 'py manage.py runserver'...")
    subprocess.Popen("py manage.py runserver", shell = True, cwd="./Backend")  # Menjalankan server di backend

def main():
    try:
        run_training_indobert()
        run_training_bart()
        run_frontend()
        run_backend()
        print("Both frontend and backend are running. Press Ctrl+C to stop.")
        # Keep the Python script running so both processes continue
        while True:
            pass  # This prevents the script from exiting immediately
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
