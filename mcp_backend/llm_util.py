import openai
import json

OPENAI_API_KEY = ""

def generate_store_payload(title, stack_trace, git_diff, repo, branch, language):
    prompt = f"""
        You are an AI that converts raw bug-fix data into a structured payload for a database.
        Format the output as JSON matching the following schema:
        - type: "solution" | "bug" | "doc"
        - title: string
        - body: string
        - stack_trace: string
        - code: string (git diff of applied fix)
        - repro_steps: string
        - resolution: string
        - metadata: object with keys repo, branch, language

        Here is the input:

        Title: {title}
        Stack trace:
        {stack_trace}

        Git diff:
        {git_diff}

        Repo: {repo}, Branch: {branch}, Language: {language}

        User notes (optional):
        {user_notes if user_notes else "None"}

        Return ONLY the JSON object.
        """
    
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )

    content = response.choices[0].message.content.strip()
    try:
        payload = json.loads(content)
    except json.JSONDecodeError:
        raise ValueError(f"LLM returned invalid JSON:\n{content}")
    
    return payload

