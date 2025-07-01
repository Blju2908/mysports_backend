#!/usr/bin/env python3
"""
Deduplicate Exercise List Script

This script analyzes the sample exercise list and removes duplicates and redundancies.
It creates a cleaned version of the exercise list.

Usage:
    python scripts/deduplicate_exercise_list.py
"""

import re
from typing import List, Set, Dict, Tuple
from collections import defaultdict


def normalize_exercise_name(exercise: str) -> str:
    """
    Normalisiert Übungsnamen für Duplikat-Erkennung.
    
    Args:
        exercise: Übungsname
        
    Returns:
        Normalisierter Name
    """
    # Entferne Klammern und deren Inhalt
    normalized = re.sub(r'\([^)]*\)', '', exercise)
    
    # Entferne häufige Variationen
    normalized = normalized.replace('(Machine)', '')
    normalized = normalized.replace('(Barbell)', '')
    normalized = normalized.replace('(Dumbbell)', '')
    normalized = normalized.replace('(Kettlebell)', '')
    normalized = normalized.replace('(DB)', '')
    normalized = normalized.replace('(KB)', '')
    normalized = normalized.replace('(Band)', '')
    normalized = normalized.replace('(PVC)', '')
    normalized = normalized.replace('(Smith)', '')
    
    # Entferne Extra-Spaces und konvertiere zu lowercase
    normalized = ' '.join(normalized.strip().split()).lower()
    
    return normalized


def parse_exercise_file(file_path: str) -> Dict[str, List[str]]:
    """
    Parst die Exercise-Datei und gruppiert nach Kategorien.
    
    Args:
        file_path: Pfad zur Exercise-Datei
        
    Returns:
        Dict mit Kategorien als Keys und Übungslisten als Values
    """
    categories = {}
    current_category = None
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # Skip leere Zeilen und Kommentare
            if not line or line.startswith('#'):
                # Prüfe ob es eine Kategorie ist
                if line.startswith('# ') and not line.endswith('Generator'):
                    current_category = line[2:].strip()
                    categories[current_category] = []
                continue
            
            # Entferne führende Striche
            if line.startswith('- '):
                exercise = line[2:].strip()
                if current_category and exercise:
                    categories[current_category].append(exercise)
    
    return categories


def find_duplicates(categories: Dict[str, List[str]]) -> Dict[str, List[Tuple[str, str]]]:
    """
    Findet Duplikate in den Übungslisten.
    
    Args:
        categories: Dict mit Kategorien und Übungen
        
    Returns:
        Dict mit normalisierten Namen als Keys und Listen von (category, exercise) Tupeln
    """
    normalized_to_exercises = defaultdict(list)
    
    for category, exercises in categories.items():
        for exercise in exercises:
            normalized = normalize_exercise_name(exercise)
            normalized_to_exercises[normalized].append((category, exercise))
    
    # Nur Duplikate zurückgeben
    duplicates = {
        norm: exercises 
        for norm, exercises in normalized_to_exercises.items() 
        if len(exercises) > 1
    }
    
    return duplicates


def analyze_redundancies(categories: Dict[str, List[str]]) -> List[str]:
    """
    Analysiert potenzielle Redundanzen und sehr ähnliche Übungen.
    
    Args:
        categories: Dict mit Kategorien und Übungen
        
    Returns:
        Liste von Redundanz-Berichten
    """
    redundancies = []
    
    # Bekannte redundante Muster
    redundant_patterns = [
        # Basic vs Advanced Variationen
        (r'(.+) \(Wall\)', r'\1 \(Freestanding\)'),
        (r'(.+) Push-up', r'\1 Push-up \(.*\)'),
        (r'(.+) Stretch', r'(.+) Stretch \(.*\)'),
        
        # Equipment Variationen
        (r'(.+) \(Barbell\)', r'\1 \(Dumbbell\)'),
        (r'(.+) Squat', r'\1 Squat \(.*\)'),
        (r'(.+) Deadlift', r'\1 Deadlift \(.*\)'),
    ]
    
    all_exercises = []
    for exercises in categories.values():
        all_exercises.extend(exercises)
    
    # Finde ähnliche Übungen
    for i, ex1 in enumerate(all_exercises):
        for ex2 in all_exercises[i+1:]:
            # Jaccard Similarity für Wörter
            words1 = set(ex1.lower().split())
            words2 = set(ex2.lower().split())
            
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            
            if len(union) > 0:
                similarity = len(intersection) / len(union)
                
                if similarity > 0.6 and ex1 != ex2:  # 60% Ähnlichkeit
                    redundancies.append(f"Ähnlich: '{ex1}' <-> '{ex2}' (Similarity: {similarity:.2f})")
    
    return redundancies


def create_cleaned_exercise_list(
    categories: Dict[str, List[str]], 
    duplicates: Dict[str, List[Tuple[str, str]]]
) -> Dict[str, List[str]]:
    """
    Erstellt eine bereinigte Übungsliste ohne Duplikate.
    
    Args:
        categories: Original Kategorien
        duplicates: Gefundene Duplikate
        
    Returns:
        Bereinigte Kategorien
    """
    cleaned_categories = {}
    processed_exercises = set()
    
    for category, exercises in categories.items():
        cleaned_exercises = []
        
        for exercise in exercises:
            normalized = normalize_exercise_name(exercise)
            
            # Skip wenn bereits verarbeitet
            if normalized in processed_exercises:
                continue
            
            # Wenn es ein Duplikat ist, wähle die beste Version
            if normalized in duplicates:
                duplicate_group = duplicates[normalized]
                best_exercise = choose_best_exercise([ex[1] for ex in duplicate_group])
                
                # Nur hinzufügen wenn es das beste Exercise ist
                if exercise == best_exercise:
                    cleaned_exercises.append(exercise)
                    processed_exercises.add(normalized)
            else:
                cleaned_exercises.append(exercise)
                processed_exercises.add(normalized)
        
        if cleaned_exercises:
            cleaned_categories[category] = cleaned_exercises
    
    return cleaned_categories


def choose_best_exercise(exercises: List[str]) -> str:
    """
    Wählt die beste Version einer Übung aus mehreren Duplikaten.
    
    Args:
        exercises: Liste von duplizierten Übungen
        
    Returns:
        Beste Übung
    """
    # Priorität: 
    # 1. Einfachste Form (ohne Klammern)
    # 2. Mit Equipment-Spezifikation
    # 3. Kürzester Name
    
    # Sortiere nach Priorität
    def priority_score(exercise: str) -> Tuple[int, int, int]:
        has_parentheses = 1 if '(' in exercise else 0
        has_equipment = 1 if any(eq in exercise.lower() for eq in 
                               ['barbell', 'dumbbell', 'kettlebell', 'machine', 'smith']) else 0
        length = len(exercise)
        
        return (has_parentheses, -has_equipment, length)
    
    return min(exercises, key=priority_score)


def write_cleaned_file(categories: Dict[str, List[str]], output_path: str):
    """
    Schreibt die bereinigte Übungsliste in eine neue Datei.
    
    Args:
        categories: Bereinigte Kategorien
        output_path: Pfad für die Ausgabedatei
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Bereinigte Übungsliste für Exercise Description Generator\n")
        f.write("# Duplikate und Redundanzen wurden entfernt\n\n")
        
        for category, exercises in categories.items():
            f.write(f"# {category}\n")
            for exercise in sorted(exercises):
                f.write(f"- {exercise}\n")
            f.write("\n")


def main():
    """Hauptfunktion für das Deduplicate Script."""
    input_file = "app/llm/exercise_description/sample_exercises.txt"
    output_file = "app/llm/exercise_description/sample_exercises_cleaned.txt"
    
    print("🧹 Exercise List Deduplication Script")
    print("="*50)
    
    # Parse die Original-Datei
    print(f"📋 Lade Exercise Liste aus {input_file}...")
    categories = parse_exercise_file(input_file)
    
    total_exercises = sum(len(exercises) for exercises in categories.values())
    print(f"✅ {len(categories)} Kategorien mit {total_exercises} Übungen geladen")
    
    # Finde Duplikate
    print("\n🔍 Suche nach Duplikaten...")
    duplicates = find_duplicates(categories)
    
    if duplicates:
        print(f"❌ {len(duplicates)} Duplikat-Gruppen gefunden:")
        for norm, exercises in duplicates.items():
            print(f"   '{norm}':")
            for category, exercise in exercises:
                print(f"     - {exercise} ({category})")
    else:
        print("✅ Keine exakten Duplikate gefunden")
    
    # Analysiere Redundanzen
    print("\n🔍 Suche nach Redundanzen...")
    redundancies = analyze_redundancies(categories)
    
    if redundancies:
        print(f"⚠️  {len(redundancies)} potenzielle Redundanzen gefunden:")
        for redundancy in redundancies[:10]:  # Zeige nur erste 10
            print(f"   {redundancy}")
        if len(redundancies) > 10:
            print(f"   ... und {len(redundancies) - 10} weitere")
    
    # Erstelle bereinigte Liste
    print(f"\n🧹 Erstelle bereinigte Liste...")
    cleaned_categories = create_cleaned_exercise_list(categories, duplicates)
    
    cleaned_total = sum(len(exercises) for exercises in cleaned_categories.values())
    removed_count = total_exercises - cleaned_total
    
    print(f"✅ Bereinigte Liste erstellt:")
    print(f"   Original: {total_exercises} Übungen")
    print(f"   Bereinigt: {cleaned_total} Übungen")
    print(f"   Entfernt: {removed_count} Duplikate")
    
    # Schreibe bereinigte Datei
    write_cleaned_file(cleaned_categories, output_file)
    print(f"💾 Bereinigte Liste gespeichert in {output_file}")
    
    # Zusammenfassung pro Kategorie
    print(f"\n📊 Zusammenfassung pro Kategorie:")
    for category in categories.keys():
        original_count = len(categories[category])
        cleaned_count = len(cleaned_categories.get(category, []))
        removed = original_count - cleaned_count
        print(f"   {category}: {original_count} → {cleaned_count} (-{removed})")


if __name__ == "__main__":
    main() 