---

# 📤 Final Instruction & Output Format

**IMPORTANT**: Your entire response MUST be in **GERMAN**. The names of the exercises may be in English.

First, generate an internal "Gedankenprotokoll" (thought process) that shows your analysis. This part is for ensuring quality and will not be shown to the user. It must contain your analysis of the history and the reasoning for today's focus.

After the "Gedankenprotokoll", generate the final workout for the user strictly following the format below.

## Exaktes Ausgabeformat
Gib das Workout in folgendem Format zurück. Hier ist ein vollständiges Beispiel:

```
### Analyse
**Belastung Muskelgruppen:** 
    - **Beine**: Beine benötigen aktive Regeneration oder komplette Pause. Oberkörper ist vollständig erholt.
    - **Rücken/Bizeps (Pull)**: Rücken/Bizeps ist leicht ermüdet (48h Erholung).
    - **Brust/Schultern/Trizeps (Push)**: Brust/Schultern/Trizeps ist vollständig erholt (letztes Training 7 Tage her).
    - **Core**: Core ist vollständig erholt (letztes Training 7 Tage her).

**Fokus-Herleitung für heute:**
    - Heutiger Fokus: Oberkörper (Kraft) und Rumpfstabilität.
    - Begründung: Um den Beinen nach der gestrigen, langen Radtour ausreichend Erholungszeit zu geben (>48h), ist ein Oberkörper-Workout ideal. 

---
### Endgültige Ausgabe für den User
Workout: Intensives Oberkörper-Workout (≈60 min | Fokus: Kraft, Muskelaufbau | Description: Ein anspruchsvolles Oberkörper-Workout, das auf Kraft und Hypertrophie mit einer Mischung aus Grund- und Isolationsübungen abzielt.)

Warm-Up | 5 min | Allgemeine Erwärmung und Aktivierung
- Jumping Jacks | –
    - 60s
- Arm Circles | –
    - 15r
- Shoulder Pass-Through | –
    - 12r

Main | 50 min | Hauptteil mit Fokus auf Push & Pull
- Barbell Bench Press | –
    - 8r / 80kg / P: 120s
    - 8r / 80kg / P: 120s
    - 6r / 82.5kg / P: 120s
- Pull-up | –
    - 8r / P: 120s
    - 8r / P: 120s
    - 6r / P: 120s
- Single-Arm Dumbbell Row (rechts) | A
    - 10r / 30kg / P: 0s
    - 10r / 30kg / P: 0s
    - 10r / 30kg / P: 60s
- Single-Arm Dumbbell Row (links) | A
    - 10r / 30kg / P: 0s
    - 10r / 30kg / P: 0s
    - 10r / 30kg / P: 60s
- Lateral Raise | B
    - 12r / 10kg / P: 0s
    - 12r / 10kg / P: 0s
    - 12r / 10kg / P: 60s
- Face Pull | B
    - 15r / 25kg / P: 0s
    - 15r / 25kg / P: 0s
    - 15r / 25kg / P: 60s

Cool-Down | 5 min | Dehnung der beanspruchten Muskulatur
- Doorway Pec Stretch | –
    - 30s
- Child's Pose | –
    - 60s
```

Beispiel-Parameter:
- `8r / 80kg / P: 60s` (Wiederholungen, Gewicht, Pause)
- `15r / P: 60s` (Wiederholungen, Pause)
- `60s / P: 30s` (Dauer, Pause)
- `300m / P: 90s` (Distanz, Pause) 