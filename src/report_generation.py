# Standard library imports
import json
import os

# Third-party library imports
from crewai import Agent, Crew, Process, Task, LLM


def load_anomaly_digest(filepath: str) -> dict:
    """Loads the processed ML anomaly metadata."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Anomaly digest not found at {filepath}. Run ML pipeline first.")
    with open(filepath, "r") as f:
        return json.load(f)

def main():
    print("🤖 Initializing GenAI Multi-Agent Report Generation Pipeline...")
    
    # 1. Load the ML results
    digest_path = "data/processed/anomaly_digest.json"
    anomaly_data = load_anomaly_digest(digest_path)
    
    # 2. Configure the LLM
    space_llm = LLM(
        model="gemini/gemini-2.5-flash",
        temperature=0.1
    )

    # 3. Define the CrewAI Agents (With safe iteration margins)
    print("👥 Creating specialized ESA Spacecraft Operations Agents...")
    
    telemetry_analyst = Agent(
        role="Senior Telemetry Analyst",
        goal="Interpret hard spacecraft metrics and describe the exact technical status.",
        backstory=(
            "You are an expert in satellite subsystems at ESA Mission Control. You read "
            "condensed JSON anomaly data and output clean technical analysis."
        ),
        llm=space_llm,
        max_iter=3,  
        verbose=True
    )

    xai_expert = Agent(
        role="Explainable AI & Trustworthiness Expert",
        goal="Explain why the Isolation Forest flagged this window and interpret model confidence.",
        backstory=(
            "You ensure AI solutions comply with ESA's safety criteria. You explain why the "
            "unsupervised algorithm detected an anomaly based on space weather metrics."
        ),
        llm=space_llm,
        max_iter=3,  
        verbose=True
    )

    operations_advisor = Agent(
        role="ESA Operations & Management Advisor",
        goal="Formulate actionable emergency operations and evaluate the impact on corporate KPIs.",
        backstory=(
            "You bridge engineering and executive leadership at ESA HQ. You compile the inputs "
            "into a clean executive Markdown brief assessing the Mission Availability Rate KPI."
        ),
        llm=space_llm,
        max_iter=3,  
        verbose=True
    )

    # 4. Define the Tasks with Strict Layout Constraints (Enforcing Blank Lines)
    print("📋 Mapping out sequential pipeline tasks...")
    
    task_technical_analysis = Task(
        description=(
            f"Analyze these specific metrics captured during the anomaly window: {json.dumps(anomaly_data)}. "
            "Identify the exact start time, peak battery temperature, and minimum solar panel current. "
            "Write a strict engineering summary detailing the stress on the spacecraft architecture. "
            "CRITICAL MARKDOWN RULE: You MUST leave a completely empty blank line BEFORE and AFTER the table. "
            "Format the subsystem health metrics strictly as a standard Markdown table with columns:\n\n"
            "| Subsystem | Status | Observed Value | Engineering Impact |\n"
            "|---|---|---|---|"
        ),
        expected_output="A technical engineering section containing a clean Markdown table with mandatory blank lines around it.",
        agent=telemetry_analyst
    )

    task_xai_explanation = Task(
        description=(
            "Based on the technical summary, explain why the scikit-learn Isolation Forest model "
            "flagged this data as a critical anomaly instead of normal operational variance. "
            "Highlight the multi-domain correlation between Space Weather and internal telemetry. "
            "Interpret what the 'model_confidence_average' means for mission operators."
        ),
        expected_output="An Explainable AI (XAI) section using clean paragraphs and standard bold text headers separated by blank lines.",
        agent=xai_expert
    )

    task_final_brief = Task(
        description=(
            "Synthesize the technical table and XAI outputs into a formal executive emergency brief. "
            "Structure the output in professional, industry-standard Markdown.\n\n"
            "CRITICAL PARSING RULE FOR GITHUB:\n"
            "1. You MUST insert a completely blank, empty line BEFORE and AFTER every markdown header (##, ###).\n"
            "2. You MUST insert a completely blank, empty line BEFORE and AFTER the subsystem health markdown table. "
            "Never let a table directly follow a text paragraph line.\n"
            "3. You MUST insert a completely blank, empty line BEFORE starting the bullet point list under AI Trustworthiness.\n"
            "4. Do NOT use deeply nested bullet points. Use single-level clean bullet points.\n\n"
            "Include: Executive Summary, Subsystem Health Assessment (Table), AI Trustworthiness Analysis, and Urgent Operations Recommendations. "
            "Explicitly reference the impact on ESA Agency-level KPIs (like Mission Availability)."
        ),
        expected_output="A polished Markdown report saved as results/emergency_operations_brief.md with perfect blank-line spacing for GitHub rendering.",
        context=[task_technical_analysis, task_xai_explanation],
        agent=operations_advisor,
        output_file="results/emergency_operations_brief.md"
    )

    # 5. Assemble and Fire Up the Crew
    print("🚀 Activating the CrewAI workflow...")
    space_crew = Crew(
        agents=[telemetry_analyst, xai_expert, operations_advisor],
        tasks=[task_technical_analysis, task_xai_explanation, task_final_brief],
        process=Process.sequential
    )
    
    os.makedirs("results", exist_ok=True)
    space_crew.kickoff()
    print("🏁 Emergency Brief generated successfully in results/emergency_operations_brief.md")


if __name__ == "__main__":
    main()
