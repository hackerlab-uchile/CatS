from app import init_db
from fastapi import FastAPI
from multiprocessing import Process
import argparse
import subprocess

app = FastAPI() # instance of FastAPI

app.title = "CatS"
app.version = "1.2.0"

def run_backend():
    """
    Function that add the comand to run the backend
    """
    subprocess.run(["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"])

def run_bot():
    """
    Function that add the comand to run the bot
    """
    subprocess.run(["python", "-u", "-m", "app.bot.bot_conn"])

def run_both_services():
    p1 = Process(target=run_backend)
    p2 = Process(target=run_bot)
    p1.start()
    p2.start()
    p1.join()
    p2.join()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Launch CatS services")
    parser.add_argument(
        "service", 
        choices=["backend", "bot", "both"], 
        help="Choose which service to run"
    )
    args = parser.parse_args()

    if args.service == "backend":
        run_backend()
    elif args.service == "bot":
        run_bot()
    elif args.service == "both":
        run_both_services()