import ollama
import time

def summarize_jd(jd_text):
    prompt = f"Summarize the following job description in 4–5 concise bullet points:\n\n{jd_text.strip()}"
    print("📨 Sending prompt to Mistral...")

    try:
        start = time.time()

        response = ollama.chat(
            model="mistral",
            messages=[
                {"role": "system", "content": "You are an expert technical recruiter. Return only the summary."},
                {"role": "user", "content": prompt}
            ]
        )

        duration = round(time.time() - start, 2)
        print(f"✅ Got response in {duration} seconds")
        return response['message']['content'].strip()

    except Exception as e:
        print(f"❌ Error from Ollama: {e}")
        return f"⚠️ Error summarizing JD: {e}"
