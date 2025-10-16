"""OpenAI integration for generating explanations."""

from typing import List

import openai

from .models import IAMStatement


class OpenAIAnalyzer:
    """OpenAI-powered analysis for IAM statements."""

    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)

    def enhance_statements(self, statements: List[IAMStatement]) -> List[IAMStatement]:
        """Enhance statements with AI-generated explanations."""
        enhanced_statements = []

        for statement in statements:
            try:
                explanation = self._generate_explanation(statement)
                enhanced_statement = IAMStatement(
                    sid=statement.sid,
                    effect=statement.effect,
                    action=statement.action,
                    resource=statement.resource,
                    explanation=explanation,
                )
                enhanced_statements.append(enhanced_statement)
            except Exception as e:
                print(f"Warning: Could not generate AI explanation for {statement.sid}: {e}")
                # Use original statement with default explanation
                enhanced_statements.append(statement)

        return enhanced_statements

    def _generate_explanation(self, statement: IAMStatement) -> str:
        """Generate AI explanation for a statement."""
        prompt = f"""
        Explain the purpose and security implications of this IAM policy statement:

        Statement ID: {statement.sid}
        Effect: {statement.effect}
        Actions: {', '.join(statement.action)}
        Resources: {statement.resource}

        Provide a concise explanation of:
        1. What this statement allows
        2. Why these permissions might be needed
        3. Any security considerations

        Keep the explanation under 100 words.
        """

        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are an AWS security expert explaining IAM policy statements.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=150,
            temperature=0.3,
        )

        return response.choices[0].message.content.strip()
