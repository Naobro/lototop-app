# auth.py
import streamlit as st
import datetime
import hashlib

def generate_password():
    """年月を元に毎月自動で変わるパスワードを生成（10文字）"""
    now = datetime.datetime.now()
    base = f"NAOsecure-{now.year}{now.month:02d}"
    hashed = hashlib.sha256(base.encode()).hexdigest()
    return hashed[:10]

def check_password():
    return
