import argparse
import datetime
import json
import random
from pathlib import Path

def get_args():
    parser = argparse.ArgumentParser(description="Auto-generates a daily AI factcheck quiz")
    parser.add_argument('--count', type=int, default=5, help='Number of questions')
    parser.add_argument('--date', type=str, default=None, help='Date for the quiz (YYYY-MM-DD)')
    return parser.parse_args()

def generate_questions_for_dossier(metadata, folder_name):
    questions = []
    
    portfolio = metadata.get('portfolio_story', {})
    hook_ko = portfolio.get('the_hook', '')
    hook_en = portfolio.get('the_hook_en', '')
    verdict = metadata.get('verdict', 'UNKNOWN')
    
    explanation_ko = portfolio.get('engineering_takeaways', '')
    explanation_en = ""
    
    # Type A (Verdict)
    if hook_ko and verdict in ["VERIFIED_TRUE", "HALF_TRUE", "GAMED"]:
        q_verdict = {
            "id": None,
            "type": "verdict",
            "claim": hook_ko,
            "claim_en": hook_en,
            "options": [
                {"label": "✅ 사실 (VERIFIED_TRUE)", "value": "VERIFIED_TRUE"},
                {"label": "⚠️ 반만 맞음 (HALF_TRUE)", "value": "HALF_TRUE"},
                {"label": "❌ 과장 (GAMED)", "value": "GAMED"},
                {"label": "🤔 판단 불가", "value": "UNKNOWN"}
            ],
            "correct_answer": verdict,
            "explanation_ko": explanation_ko,
            "explanation_en": explanation_en,
            "source_case": folder_name,
            "difficulty": "medium"
        }
        questions.append(q_verdict)
        
    # Type C (Community)
    community_signals = metadata.get('community_signals', [])
    for signal in community_signals:
        signal_type = signal.get('signal_type')
        quote = signal.get('quote')
        if signal_type in ['POSITIVE', 'NEGATIVE'] and quote:
            q_community = {
                "id": None,
                "type": "community",
                "claim": f'"{quote}"',
                "claim_en": "",
                "options": [
                    {"label": "👍 긍정적 (POSITIVE)", "value": "POSITIVE"},
                    {"label": "👎 부정적 (NEGATIVE)", "value": "NEGATIVE"}
                ],
                "correct_answer": signal_type,
                "explanation_ko": f"이 반응은 {signal_type} 커뮤니티 시그널로 분류되었습니다.",
                "explanation_en": f"This reaction was classified as a {signal_type} community signal.",
                "source_case": folder_name,
                "difficulty": "easy"
            }
            questions.append(q_community)
            
    # Shuffle and pick up to 2 questions to simulate "generate 1-2 quiz questions"
    random.shuffle(questions)
    return questions[:2]

def main():
    args = get_args()
    
    target_date = args.date if args.date else datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Seed based on date for reproducible quiz of the day
    random.seed(target_date)
    
    project_root = Path(__file__).parent.parent
    investigations_dir = project_root / 'investigations'
    
    all_questions = []
    dossier_count = 0
    
    if investigations_dir.exists():
        for metadata_path in investigations_dir.glob('*/metadata.json'):
            dossier_count += 1
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                folder_name = metadata_path.parent.name
                folder_qs = generate_questions_for_dossier(metadata, folder_name)
                all_questions.extend(folder_qs)
            except Exception as e:
                print(f"Error reading {metadata_path}: {e}")
                
    # Randomly shuffle all possible questions and pick N
    random.shuffle(all_questions)
    selected_questions = all_questions[:args.count]
    
    # Re-assign sequential IDs
    for i, q in enumerate(selected_questions):
        q['id'] = i + 1
        
    quiz_data = {
        "quiz_date": target_date,
        "questions": selected_questions,
        "total_questions": len(selected_questions)
    }
    
    public_dir = project_root / 'public' / 'quiz'
    public_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = public_dir / 'daily_quiz.json'
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(quiz_data, f, ensure_ascii=False, indent=2)
        
    print(f"Quiz generation complete for {target_date}.")
    print(f"Found {dossier_count} dossiers.")
    print(f"Generated {len(selected_questions)} questions (out of {len(all_questions)} possible).")
    print(f"Saved to {output_path}")

if __name__ == '__main__':
    main()
