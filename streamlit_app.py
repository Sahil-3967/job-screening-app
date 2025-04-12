import streamlit as st
import pandas as pd
import io
import re
from concurrent.futures import ThreadPoolExecutor
from agents import jd_summarizer, cv_parser, matcher, shortlister, interview_scheduler
from database import db
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Initialize DB
db.init_db()

st.set_page_config(page_title="AI Job Screening System", layout="wide")
st.title("🤖 AI-Powered Job Screening System")

# Step 1: Upload JD
st.subheader("1️⃣ Choose or Upload a Job Description")
option = st.radio("Select JD source:", ["📄 Upload CSV", "📌 Upload your own .txt"], index=0)

jd_text = ""
jd_df = None
jd_summary_cache = {}

if option == "📄 Upload CSV":
    csv_file = st.file_uploader("Upload job_description.csv", type=["csv"])
    if csv_file:
        try:
            jd_df = pd.read_csv(io.StringIO(csv_file.getvalue().decode("utf-8")))
        except UnicodeDecodeError:
            jd_df = pd.read_csv(io.StringIO(csv_file.getvalue().decode("ISO-8859-1")))

        if "Job Title" not in jd_df.columns or "Job Description" not in jd_df.columns:
            st.error("⚠️ CSV must contain 'Job Title' and 'Job Description' columns.")
            st.stop()

        selected_title = st.selectbox("Select a Job Title", jd_df["Job Title"])
        jd_text = jd_df[jd_df["Job Title"] == selected_title]["Job Description"].values[0]
        st.text_area("📄 Selected Job Description", jd_text, height=200)

elif option == "📌 Upload your own .txt":
    jd_file = st.file_uploader("Upload a JD (.txt file)", type=["txt"])
    if jd_file:
        jd_text = jd_file.read().decode("utf-8")
        st.text_area("📄 Uploaded Job Description", jd_text, height=200)

# Step 2: Summarize JD(s)
if jd_text:
    if option == "📄 Upload CSV" and jd_df is not None:
        if "jd_summary_cache" not in st.session_state:
            def summarize_jd(row):
                jd_title = row["Job Title"]
                jd_text = row["Job Description"]
                summary = jd_summarizer.summarize_jd(jd_text)
                return jd_title, summary

            with st.spinner("Summarizing all job descriptions using Ollama..."):
                with ThreadPoolExecutor() as executor:
                    summaries = list(executor.map(summarize_jd, [row for _, row in jd_df.iterrows()]))

                jd_summary_cache = {title: summary for title, summary in summaries}
                st.session_state["jd_summary_cache"] = jd_summary_cache
        else:
            jd_summary_cache = st.session_state["jd_summary_cache"]

        st.success("✅ All JDs summarized!")
        for jd_title, jd_summary in jd_summary_cache.items():
            st.write(f"📌 **{jd_title}** — {jd_summary[:100]}...")

    else:
        if "jd_summary" not in st.session_state or st.session_state.get("jd_text") != jd_text:
            with st.spinner("Summarizing JD using Ollama..."):
                jd_summary = jd_summarizer.summarize_jd(jd_text)
                st.session_state["jd_summary"] = jd_summary
                st.session_state["jd_text"] = jd_text
        else:
            jd_summary = st.session_state["jd_summary"]

        st.success("✅ JD Summarized!")
        st.text_area("🧐 JD Summary", jd_summary, height=200)

# Step 3: Upload Resumes
st.subheader("2️⃣ Upload Candidate Resumes (PDFs)")
max_files = st.slider("Max resumes to process", 10, 200, 50)
resume_files = st.file_uploader("Upload Resume PDFs", type=["pdf"], accept_multiple_files=True)

threshold = st.slider("🔢 Select shortlisting threshold (%)", min_value=0, max_value=100, value=50, step=1)
max_shortlist = st.slider("📌 Maximum candidates to shortlist", min_value=1, max_value=100, value=10, step=1)

with st.expander("📧 Email Settings"):
    sender_email = st.text_input("Your Gmail Address")
    sender_password = st.text_input("App Password", type="password")
    enable_email = st.checkbox("Enable email sending to shortlisted candidates")

def send_email(to_email, subject, message, sender_email, sender_password):
    msg = MIMEMultipart()
    msg["From"] = f"HR Team <{sender_email}>"
    msg["To"] = to_email
    msg["Reply-To"] = sender_email
    msg["Subject"] = subject
    msg.attach(MIMEText(message, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        return "✅ Email sent"
    except Exception as e:
        return f"❌ Error: {e}"

def process_resume(file):
    text = cv_parser.parse_pdf(file)
    name = file.name.replace(".pdf", "")
    email_match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
    if email_match:
        email = email_match.group(0)
        st.write(f"✅ Found email for {name}: {email}")
    else:
        email = f"{name.lower()}@example.com"
        st.warning(f"⚠️ Email not found for {name}, using fallback: {email}")
    return {"name": name, "resume": text, "email": email}

if resume_files:
    with st.spinner("Processing resumes in parallel..."):
        with ThreadPoolExecutor() as executor:
            candidates = list(executor.map(process_resume, resume_files[:max_files]))

    st.success("✅ All candidates processed.")
    st.subheader(f"3️⃣ Shortlisted Candidates (Score ≥ {threshold}%)")

    if option == "📄 Upload CSV":
        jd_summary = jd_summary_cache.get(selected_title, "")
    else:
        jd_summary = st.session_state["jd_summary"]

    match_results = []
    for candidate in candidates:
        score = matcher.calculate_match(jd_summary, candidate["resume"])
        db.save_candidate(candidate["name"], score, candidate["resume"])
        match_results.append({**candidate, "score": score})

    shortlisted = shortlister.shortlist(match_results, threshold=threshold)
    shortlisted = sorted(shortlisted, key=lambda x: x["score"], reverse=True)[:max_shortlist]

    if shortlisted:
        st.success(f"✅ {len(shortlisted)} candidate(s) shortlisted!")
        for c in shortlisted:
            with st.expander(f"🎯 {c['name']} — Score: {c['score']}%"):
                st.text_area("📄 Resume Preview", c["resume"][:1000], height=200)
                st.write(interview_scheduler.schedule_interview(c))

        if enable_email and sender_email and sender_password:
            if st.button("📤 Send Emails to Shortlisted Candidates"):
                for c in shortlisted:
                    subject = "Interview Invitation: You're Shortlisted"
                    message = f"""Hi {c['name']},

We're pleased to inform you that you've been shortlisted based on your profile match.

Please reply to this email to confirm your availability for the next steps.

Best regards,
HR Team"""
                    result = send_email(c["email"], subject, message, sender_email, sender_password)
                    st.write(f"📧 {c['email']}: {result}")
                st.info("📬 Email sent! If it doesn't appear in the inbox, please check the Spam or Promotions tab.")
    else:
        st.warning("⚠️ No candidates passed the threshold.")

    if option == "📄 Upload CSV":
        st.divider()
        st.subheader("📊 Batch Matching: All Resumes vs All Job Descriptions")

        if st.button("Run Batch Matching"):
            match_tasks = []
            parsed_resumes = {c["name"]: c["resume"] for c in candidates}

            for jd_title, jd_summary in jd_summary_cache.items():
                for name, resume_text in parsed_resumes.items():
                    match_tasks.append((name, resume_text, jd_title, jd_summary))

            def match_pair(args):
                name, resume_text, jd_title, jd_summary = args
                score = matcher.calculate_match(jd_summary, resume_text)
                return (name, jd_title, score)

            with st.spinner("Running batch match in parallel..."):
                with ThreadPoolExecutor() as executor:
                    results = list(executor.map(match_pair, match_tasks))

            batch_results = [(name, role, score) for name, role, score in results if score >= threshold]
            batch_results = sorted(batch_results, key=lambda x: x[2], reverse=True)[:max_shortlist]

            if batch_results:
                st.success("✅ Batch Matching Complete")
                for name, role, score in batch_results:
                    st.write(f"🎯 {name} matched for {role} — Score: {score}%")
            else:
                st.warning("⚠️ No candidates matched any job description.")