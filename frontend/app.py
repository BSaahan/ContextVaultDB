import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="ContextVaultDB", layout="wide")

st.title("ContextVaultDB")
st.write("AI Memory Database for documents, memories, and semantic search")

tab1, tab2, tab3 = st.tabs(["Add Memory", "Search Memory", "Chat"])

with tab1:
    title = st.text_input("Title")
    content = st.text_area("Memory Content")
    category = st.text_input("Category", value="general")

    if st.button("Add Memory"):
        response = requests.post(
            f"{API_URL}/memory/add",
            json={
                "title": title,
                "content": content,
                "category": category
            }
        )
        st.json(response.json())

with tab2:
    query = st.text_input("Search Query")
    top_k = st.number_input("Top K", min_value=1, max_value=10, value=3)

    if st.button("Search"):
        response = requests.post(
            f"{API_URL}/memory/search",
            json={
                "query": query,
                "top_k": top_k
            }
        )
        st.json(response.json())

with tab3:
    question = st.text_area("Ask ContextVaultDB")
    chat_top_k = st.number_input("Chat Top K", min_value=1, max_value=10, value=3)

    if st.button("Ask"):
        response = requests.post(
            f"{API_URL}/chat",
            json={
                "question": question,
                "top_k": chat_top_k
            }
        )
        st.json(response.json())