from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from app.core.config import get_config
from datetime import datetime
from typing import Optional
from pathlib import Path

PROMPT_FILE = "workout_rationale_prompt.md"

def clean_text_for_prompt(text: str | None) -> str:
    """
    Bereinigt Text für die Verwendung in Prompts.
    Entfernt problematische Zeichen wie Null-Bytes, Steuerzeichen etc.
    """
    if text is None:
        return ""
    
    # Entferne Null-Bytes und andere problematische Zeichen
    cleaned = text.replace('\x00', '').replace('\r', '').strip()
    
    # Entferne andere Steuerzeichen (außer normalen Zeilenumbrüchen und Tabs)
    cleaned = ''.join(char for char in cleaned if ord(char) >= 32 or char in ['\n', '\t'])
    
    return cleaned

def create_anthropic_llm():
    """Erstellt eine Anthropic LLM-Instanz"""
    config = get_config()
    
    if not config.ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY is not configured but required for Anthropic LLM")
    
    llm = ChatAnthropic(
        model="claude-sonnet-4-20250514",
        api_key=config.ANTHROPIC_API_KEY,
        max_retries=2,
        temperature=0.7  # Etwas Kreativität für TikTok-Content
    )
    return llm

def create_openai_llm():
    """Erstellt eine OpenAI LLM-Instanz"""
    config = get_config()
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        api_key=config.OPENAI_API_KEY2,
        temperature=0.3  # Niedrigere Temperatur für sachlichere, wissenschaftlichere Antworten
    )   
    return llm

def save_prompt_to_output(prompt_content: str, user_id: str, workout_id: int) -> str:
    """
    Speichert den vollständigen Prompt im output-Ordner.
    
    Args:
        prompt_content: Der formatierte Prompt
        user_id: User-ID für Dateinamen
        workout_id: Workout-ID für Dateinamen
        
    Returns:
        Der Pfad zur gespeicherten Datei
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    filename = f"prompt_user_{user_id}_workout_{workout_id}_{timestamp}.md"
    file_path = output_dir / filename
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(prompt_content)
    
    print(f"📄 Prompt gespeichert: {file_path}")
    return str(file_path)

def save_rationale_to_output(rationale_text: str, user_id: str, workout_id: int) -> str:
    """
    Speichert die generierte Rationale im output-Ordner.
    
    Args:
        rationale_text: Die generierte sportwissenschaftliche Begründung
        user_id: User-ID für Dateinamen
        workout_id: Workout-ID für Dateinamen
        
    Returns:
        Der Pfad zur gespeicherten Datei
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    filename = f"rationale_user_{user_id}_workout_{workout_id}_{timestamp}.txt"
    file_path = output_dir / filename
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(rationale_text)
    
    print(f"📁 Rationale gespeichert: {file_path}")
    return str(file_path)

async def generate_workout_rationale_llm(
    current_workout: str,
    training_plan: Optional[str] = None,
    training_history: Optional[str] = None,
    user_id: Optional[str] = None,
    workout_id: Optional[int] = None
) -> str:
    """
    Generiert eine sportwissenschaftliche Begründung für ein Workout.
    
    Args:
        current_workout: Das aktuelle Workout als formatierter String
        training_plan: Die Trainingsziele und Nutzerkontext als formatierter String
        training_history: Die Trainingshistorie als formatierter String
        user_id: User-ID für Output-Speicherung
        workout_id: Workout-ID für Output-Speicherung
        
    Returns:
        Eine sportwissenschaftliche Begründung als Text
    """
    try:
        # Bereinige die Input-Texte
        cleaned_workout = clean_text_for_prompt(current_workout)
        cleaned_training_plan = clean_text_for_prompt(training_plan) if training_plan else "Keine Trainingsziele verfügbar."
        cleaned_history = clean_text_for_prompt(training_history) if training_history else "Keine Trainingshistorie verfügbar."
        
        # Lade das Prompt-Template
        prompt_path = Path(__file__).parent / PROMPT_FILE
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template_content = f.read()
        
        # Formatiere den Prompt
        formatted_prompt = prompt_template_content.format(
            current_workout=cleaned_workout,
            training_plan=cleaned_training_plan,
            training_history=cleaned_history,
            current_date=datetime.now().strftime("%d.%m.%Y")
        )
        
        # Speichere den vollständigen Prompt im output-Ordner
        if user_id and workout_id:
            save_prompt_to_output(formatted_prompt, str(user_id), workout_id)
        
        # Erstelle LLM-Instanz
        llm = create_openai_llm()
        
        print("Sende Anfrage an OpenAI API für sportwissenschaftliche Workout-Analyse...")
        response = await llm.ainvoke(formatted_prompt)
        print("Antwort von OpenAI API erhalten")
        
        # Extrahiere den Text-Inhalt
        if hasattr(response, 'content'):
            if isinstance(response.content, list):
                # Handle list content
                rationale_text = ""
                for item in response.content:
                    if hasattr(item, 'text'):
                        rationale_text += item.text
                    elif isinstance(item, dict) and 'text' in item:
                        rationale_text += item['text']
                    else:
                        rationale_text += str(item)
            else:
                rationale_text = response.content
        else:
            rationale_text = str(response)
        
        # Bereinige den Response-Text
        rationale_text = clean_text_for_prompt(rationale_text)
        
        if not rationale_text.strip():
            raise ValueError("LLM hat keine gültige Antwort zurückgegeben")
        
        # Speichere die Rationale im output-Ordner
        if user_id and workout_id:
            save_rationale_to_output(rationale_text, str(user_id), workout_id)
        
        return rationale_text
        
    except Exception as e:
        print(f"Error in generate_workout_rationale_llm: {e}")
        import traceback
        traceback.print_exc()
        raise 