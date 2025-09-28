from openai import OpenAI
import os
import json

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def generate_store_payload(type, git_diff, repo, branch):
    prompt = f"""
        You are an AI that converts raw bug-fix data into a structured payload for a database.
        Format the output as JSON matching the following schema:
        - type: "solution" | "bug" | "doc"
        - title: string
        - body: string
        - code: string (git diff of applied fix)

        Here is the input:
        type: {type}

        Git diff:
        {git_diff}

        Repo: {repo}, Branch: {branch}

        Return ONLY the JSON object.
        """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )

    content = response.choices[0].message.content.strip()
    if content.startswith("```") and content.endswith("```"):
        content = "\n".join(content.split("\n")[1:-1]).strip()

    try:
        payload = json.loads(content)
    except json.JSONDecodeError:
        raise ValueError(f"LLM returned invalid JSON:\n{content}")
    
    return payload

