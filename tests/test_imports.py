import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_import_main():
    import main

def test_import_run():
    import run

def test_import_core_dependencies():
    from core import dependencies

def test_import_core_security():
    from core import security

def test_import_src_chat_agent():
    from src.agents import chat_agent