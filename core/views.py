import random
import json
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db.models import F
from django.contrib import messages
from .models import Word

def type_the_word_game(request):
    """
    Selects a word for the typing game with a weighted preference 
    for words with lower scores to add variance.
    """
    all_words = list(Word.objects.all())

    if not all_words:
        messages.error(request, "No words found. Please add words to play this game.")
        return redirect('add_words')

    all_words.sort(key=lambda w: w.score)

    priority_cutoff = int(len(all_words) * 0.4)
    if len(all_words) > 0 and priority_cutoff == 0:
        priority_cutoff = 1  # Ensure at least one word is in the priority pool

    priority_words = all_words[:priority_cutoff]
    other_words = all_words[priority_cutoff:]

    word_to_guess = None

    if random.random() < 0.7:
        if priority_words:
            word_to_guess = random.choice(priority_words)
        elif other_words:  # Fallback if priority pool is empty
            word_to_guess = random.choice(other_words)
    else:
        if other_words:
            word_to_guess = random.choice(other_words)
        elif priority_words:  # Fallback if other_words pool is empty
            word_to_guess = random.choice(priority_words)
    
    if not word_to_guess:
        word_to_guess = random.choice(all_words)

    context = {
        'word_id': word_to_guess.id,
        'russian_translation': word_to_guess.russian_translation,
        'greek_word': word_to_guess.greek_word
    }
    return render(request, 'type_word_game.html', context)


def add_words(request):
    """
    Handles the bulk addition of new word pairs from a textarea.
    """
    if request.method == 'POST':
        raw_text = request.POST.get('word_pairs', '')
        lines = raw_text.strip().split('\n')
        
        added_count = 0
        duplicate_count = 0
        error_count = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue

            parts = line.split('---')
            if len(parts) == 2:
                greek_word = parts[0].strip()
                russian_translation = parts[1].strip()

                if not greek_word or not russian_translation:
                    error_count += 1
                    continue
                
                if Word.objects.filter(greek_word__iexact=greek_word).exists():
                    duplicate_count += 1
                else:
                    try:
                        Word.objects.create(
                            greek_word=greek_word,
                            russian_translation=russian_translation
                        )
                        added_count += 1
                    except Exception as e:
                        print(f"🚨 \033[91mError creating word '{greek_word}': {e}\033[0m")
                        error_count += 1
            else:
                error_count += 1
        
        if added_count > 0:
            messages.success(request, f'Successfully added {added_count} new word pair(s).')
        if duplicate_count > 0:
            messages.warning(request, f'Skipped {duplicate_count} word pair(s) that already exist in the database.')
        if error_count > 0:
            messages.error(request, f'Failed to process {error_count} line(s) due to incorrect formatting or empty values.')

        return redirect('add_words')

    return render(request, 'add_words.html')

def card_match_game(request):
    """
    Prepares and displays the card matching game.
    """
    is_daily_challenge = request.GET.get('daily_challenge') == 'true'
    all_words = list(Word.objects.all())
    
    if is_daily_challenge:
        if len(all_words) < 10:
            return render(request, 'card_match_game.html', {'error': 'Please add at least 10 word pairs for the daily challenge.'})
        words = random.sample(all_words, 10)
    else:
        if len(all_words) < 2:
            return render(request, 'card_match_game.html', {'error': 'Please add at least 2 word pairs.'})

        all_words.sort(key=lambda w: w.score)

        priority_cutoff = int(len(all_words) * 0.4)
        if len(all_words) > 0 and priority_cutoff == 0:
            priority_cutoff = 1

        priority_words = all_words[:priority_cutoff]
        other_words = all_words[priority_cutoff:]

        game_words = []
        
        num_priority_to_pick = min(len(priority_words), 7)
        if priority_words:
            game_words.extend(random.sample(priority_words, num_priority_to_pick))

        num_other_to_pick = 10 - len(game_words)
        if other_words and num_other_to_pick > 0:
            num_other_to_pick = min(len(other_words), num_other_to_pick)
            game_words.extend(random.sample(other_words, num_other_to_pick))

        if len(game_words) < 10:
            remaining_pool = [w for w in all_words if w not in game_words]
            needed = 10 - len(game_words)
            if remaining_pool:
                game_words.extend(random.sample(remaining_pool, min(needed, len(remaining_pool))))

        random.shuffle(game_words)
        words = game_words[:10]

    if not words:
        return render(request, 'card_match_game.html', {'error': 'Could not select any words for the game.'})

    greek_cards = []
    russian_cards = []
    for word in words:
        greek_cards.append({'id': word.id, 'text': word.greek_word, 'pair_id': word.id})
        russian_cards.append({'id': word.id, 'text': word.russian_translation, 'pair_id': word.id})

    random.shuffle(greek_cards)
    random.shuffle(russian_cards)

    context = {
        'greek_cards': greek_cards,
        'russian_cards': russian_cards,
        'total_pairs': len(words)
    }
    return render(request, 'card_match_game.html', context)


@csrf_exempt
@require_POST
def update_score(request):
    """
    Updates the score of a word pair based on a game attempt.
    """
    try:
        data = json.loads(request.body)
        word_id = data.get('word_id')
        was_successful = data.get('success')

        if word_id is None or was_successful is None:
            return JsonResponse({'status': 'error', 'message': 'Missing word_id or success status.'}, status=400)

        word = Word.objects.get(id=int(word_id))
        
        if was_successful:
            word.score = F('score') + 1
        else:
            word.score = F('score') - 1
        
        word.save()
        word.refresh_from_db()

        return JsonResponse({'status': 'success', 'new_score': word.score})

    except Word.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': f'Word with ID {word_id} not found.'}, status=404)
    except Exception as e:
        print(f"🚨 \033[91mError in update_score: {e}\033[0m")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

def type_word_game_daily(request):
    """
    Handles the daily challenge for the typing game.
    """
    progress = int(request.COOKIES.get('typeWordDailyChallengeProgress', 0))
    if progress >= 50:
        messages.success(request, "You have already completed the daily challenge for today.")
        return redirect('type_word_game')

    all_words = list(Word.objects.all())

    if not all_words:
        messages.error(request, "No words found. Please add words to play this game.")
        return redirect('add_words')

    all_words.sort(key=lambda w: w.score)

    priority_cutoff = int(len(all_words) * 0.4)
    if len(all_words) > 0 and priority_cutoff == 0:
        priority_cutoff = 1

    priority_words = all_words[:priority_cutoff]
    other_words = all_words[priority_cutoff:]

    word_to_guess = None

    if random.random() < 0.7:
        if priority_words:
            word_to_guess = random.choice(priority_words)
        elif other_words:
            word_to_guess = random.choice(other_words)
    else:
        if other_words:
            word_to_guess = random.choice(other_words)
        elif priority_words:
            word_to_guess = random.choice(priority_words)
    
    if not word_to_guess:
        word_to_guess = random.choice(all_words)

    context = {
        'word_id': word_to_guess.id,
        'russian_translation': word_to_guess.russian_translation,
        'greek_word': word_to_guess.greek_word
    }
    return render(request, 'type_word_game_daily.html', context)