import os
import streamlit as st
import requests

API_URL = os.getenv("API_URL") or st.secrets.get("API_URL", "")

if not API_URL:
    st.error("API_URL is not configured. Set it as an environment variable or Streamlit secret.")
    st.stop()

st.title("📘 RAG Demo (AWS SageMaker + Bedrock)")
st.write("Ask a question about your documents:")

question = st.text_input("Enter your question")
top_k = st.slider("Top K results", min_value=1, max_value=10, value=3)

if st.button("Ask"):
    if not question.strip():
        st.warning("Please enter a question.")
    else:
        try:
            payload = {"question": question, "top_k": top_k}
            resp = requests.post(API_URL, json=payload, timeout=60)

            if resp.status_code == 200:
                data = resp.json()
                st.subheader("Answer")
                st.write(data.get("answer", "No answer returned."))

                if "citations" in data:
                    st.subheader("Citations")
                    for c in data["citations"]:
                        st.markdown(f"- **{c['source']}** (chunk {c['chunk']})")

                if "steps" in data:
                    st.subheader("Pipeline Steps")
                    st.write(" → ".join(data["steps"]))
            else:
                st.error(f"API error: {resp.status_code}")
                st.text(resp.text)

        except Exception as e:
            st.error(f"Request failed: {e}")
