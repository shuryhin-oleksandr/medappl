import math
import random
from secrets import token_hex
from django.shortcuts import redirect
from .models import RepeatQuizQuestion, RepeatQuiz, RepeatQuizOption

GENERAL_QUIZ_DATA_CACHE = {}

def return_to_previous_url(request):
    if request.META.get('HTTP_REFERER'):
        return redirect(request.META.get('HTTP_REFERER'))
    
    return redirect("/")

def get_general_quiz_data(mode, start, user, subject):
    """
    Load general quiz data
    """
    if subject in GENERAL_QUIZ_DATA_CACHE.keys():
        subject_questions, answer_key = GENERAL_QUIZ_DATA_CACHE[subject]
    else:
        subject_questions = questions_from_file(subject + "-questions.txt")
        answer_key = answer_keys_from_file(subject + "-answerkeys.txt")
        GENERAL_QUIZ_DATA_CACHE[subject] = [subject_questions, answer_key]

    return get_quiz_data(mode, start, user, subject_questions, answer_key)

def get_repeat_quiz_data(quiz, start):
    return quiz.build_quiz_data(start)

def get_saved_quiz_data(quiz, start, mode):
    if not quiz.questions:
        questions_file_data = generate_questions_file_template_data(quiz.number_of_questions, quiz.number_of_options_per_question)
    else:
        questions_file_data = quiz.questions.read().decode("utf-8")

    answer_key_file_data = quiz.answers.read().decode("utf-8")

    if mode in [1, 2]:
        number_of_questions = min(quiz.number_of_questions, 100)
    elif mode in [3, 4]:
        number_of_questions = min(quiz.number_of_questions, 50)
    else:
        number_of_questions = quiz.number_of_questions
        
    data = get_custom_quiz_data(questions_file_data, answer_key_file_data, number_of_questions, quiz.number_of_options_per_question, mode, start)

    if not isinstance(data, dict):
        print(data[0], data[1])
        return None, None
    
    return data["questions"], data["used_options"]

def generate_questions_file_template_data(number_of_questions, number_of_options_per_question):
    template = ""
    for i in range(1, number_of_questions + 1):
        template += str(i) + ".\t \n"

        for j in range(number_of_options_per_question):
            template += chr(97 + j) + ".\t \n"
    
    return template[:-1]

def get_quiz_data(mode, start, user, subject_questions, answer_key):
    """
    Load quiz data
    """
    questions = {}
    used_options = []    

    if mode == 1:
        questions, used_options = select_random_questions(subject_questions, answer_key, 4, 100)
    elif mode == 2:
        questions, used_options = select_random_questions_from_start(start, subject_questions, answer_key, 4, 100)
    elif mode == 3:
        questions, used_options = select_random_questions(subject_questions, answer_key, 8, 50)
    elif mode == 4:
        questions, used_options = select_random_questions_from_start(start, subject_questions, answer_key, 8, 50)
    else:
        questions = { "error": "Wrong mode selected :(" }
    
    return questions, list(used_options)

def create_answer_object(answers_string):
    """
    Convert an answers string to a usable format
    """
    answers = []
    answer_domain = "abcdefgh"

    for i in range(0, 8):
        answers.append({
            "option": answer_domain[i],
            "option_text": "",
            "key": answers_string[i]
        })

    return answers

def select_random_questions(subject_questions, answer_key, options_per_question_limit=4, number_of_questions=100):
    """
    Get [number_of_questions] random questions for a subject

    Args:
      subject: Subject name
      subject_questions: Questions of a subject
      answer_key: Answer key
      options_per_question_limit: Number of options per question
      number_of_questions: Number of questions
    Returns:
      A dictionary of questions along with their options
    """
    questions = []
    used_options = set()
    questions_random_sequence = random.sample(range(1, 1501), k=number_of_questions)

    for i in questions_random_sequence:
        current_question = subject_questions[i]
        question = {}
        question['id'] = token_hex(16)
        question['question'] = current_question['question']
        question['question_text'] = current_question['question_text']
        question['options'] = []

        options_random_sequence = random.sample(range(0, 8), k=options_per_question_limit)

        for j in options_random_sequence:
            question['options'].append(answer_key[i][j])
            used_options.add(current_question['options'][j])

        questions.append(question)

    return questions, used_options

def questions_from_file(filename):
    """
    Read questions from file
    """
    all_questions = {}
    last_number = 0

    with open(filename, encoding="utf-8") as file:
        for i in file:
            number, question = i.replace("\n", "").split("\t")

            if number[-1] == ".":
                number = number[:-1]

            try:
                number = int(number)
                last_number = number
                
                if number not in all_questions:
                    all_questions[number] = {}
                    all_questions[number]['question'] = number
                    all_questions[number]['question_text'] = question
                    all_questions[number]['options'] = []
            except:
                all_questions[last_number]['options'].append(number)

    return all_questions

def read_file_content(filename):
    with open(filename, encoding="utf-8") as file:
        return "".join(file.readlines()).strip()

def validate_custom_quiz_data(questions_file_data, answer_key_file_data, number_of_questions, options_per_questions):
    questions_file_data = questions_file_data.replace('"', "'")
    answer_key_file_data = answer_key_file_data.replace('"', "'")

    questions_data_parts = [list(map(lambda x: x.strip().replace('\r', ''), line.split("\t"))) for line in questions_file_data.split("\n")]
    answers_data_parts = [list(map(lambda x: x.strip().replace('\r', ''), line.split("\t"))) for line in answer_key_file_data.split("\n")]
    
    if len(answers_data_parts) < number_of_questions:
        return ["answers", "Number of answers don't match the number of questions"]

    if len(questions_data_parts) < (number_of_questions * (1 + options_per_questions)):
        return ["questions", "Not enough entries in questions file"]

    return None

def get_custom_quiz_data(questions_file_data, answer_key_file_data, number_of_questions, options_per_questions, mode, start):
    questions_file_data = questions_file_data.replace('"', "'")
    answer_key_file_data = answer_key_file_data.replace('"', "'")

    questions_data_parts = [list(map(lambda x: x.strip().replace('\r', ''), line.split("\t"))) for line in questions_file_data.split("\n")]
    answers_data_parts = [list(map(lambda x: x.strip().replace('\r', ''), line.split("\t"))) for line in answer_key_file_data.split("\n")]
    
    if len(answers_data_parts) < number_of_questions:
        return ["answers", "Number of answers don't match the number of questions"]

    if len(questions_data_parts) < (number_of_questions * (1 + options_per_questions)):
        return ["questions", "Not enough entries in questions file"]

    questions, k = [], 0
    used_options = set()

    # print("LENGTH OF QUESTIONS DATA PARTS:", len(questions_data_parts))
    # print("NUMBERS OF QUESTIONS:", number_of_questions)
    # print("NUMBERS OF OPTIONS PER QUESTION:", options_per_questions)

    for i in range(0, len(questions_data_parts), 1 + options_per_questions):
        temp = {
            'id': token_hex(16),
            "question": questions_data_parts[i][0],
            "question_text": questions_data_parts[i][1],
            "options": []
        }
        
        if mode in [1, 2]:
            options_random_sequence = random.sample(range(0, options_per_questions), k=math.ceil(options_per_questions / 2))
        else:
            options_random_sequence = random.sample(range(0, options_per_questions), k=options_per_questions)

        for j in options_random_sequence:            
            # If the option text is missing, add an empty string
            if len(questions_data_parts[i + j + 1]) == 1:
                questions_data_parts[i + j + 1].append("")
            
            print("J:", j )
            temp["options"].append({
                "option": questions_data_parts[i + j + 1][0],
                "option_text": questions_data_parts[i + j + 1][1],
                "key": answers_data_parts[k][1][j]
            })

            used_options.add(questions_data_parts[i + j + 1][0])

        k += 1
        random.shuffle(temp["options"])
        questions.append(temp)

    if mode in [2, 4]:
        questions.sort(key=lambda x: int(x["question"][:-1]))
        questions = list(filter(lambda x: int(x["question"][:-1]) >= start, questions))
    else:
        random.shuffle(questions)

    questions = questions[:number_of_questions]
    return { "questions": questions, "used_options": list(used_options) }

def answer_keys_from_file(filename):
    """
    Reads the answer key file from filename
    """
    answer_key = {}

    with open(filename, 'r') as answer_key_file:
        i = 1

        for line in answer_key_file:
            line_parts = line.strip().split()

            try:
                answer_key[int(line_parts[0])] = create_answer_object(line_parts[1])
            except (IndexError, AssertionError):
                print("Couldn't read file. Input is malformed.")
                print("Line #{}: {}".format(i, line.strip()))

            i += 1

    return answer_key

def select_random_questions_from_start(start, subject_questions, answer_key, options_per_question_limit=4, number_of_questions=100):
    """
    Get [number_of_questions] random questions for a subject

    Args:
      start: A starting point for the questions
      subject_questions: Questions of a subject
      answer_key: Answer key
      options_per_question_limit: Number of options per question
      number_of_questions: Number of questions
    Returns:
      A dictionary of questions along with their options and answers
    """
    used_options = set()
    total_number_of_questions = 1500
    end = (start + number_of_questions - 1) if ((start + number_of_questions) < total_number_of_questions) else total_number_of_questions
    questions = []
    
    for i in range(start, end + 1):
        current_question = subject_questions[i]
        question = {}
        question['id'] = token_hex(16)
        question['question'] = current_question['question']
        question['question_text'] = current_question['question_text']
        question['options'] = []

        options_random_sequence = random.sample(range(0, 8), k=options_per_question_limit)

        for j in options_random_sequence:
            question['options'].append(answer_key[i][j])
            used_options.add(current_question['options'][j])

        questions.append(question)

    return questions, used_options

def format_question_options(options):
    return ":".join(options).strip()

def create_repeat_quiz(name, user, saved_questions_data, quiz_data):
    quiz = RepeatQuiz.objects.create(
        name=name,
        user=user,
        quiz_type=quiz_data["quizType"].upper(),
        voice_recognition=quiz_data["voice_recognition"],
        negative_marking=quiz_data["voice_recognition"],
        mode=int(quiz_data["mode"]),
        subject=quiz_data["subject"],
        language=quiz_data["language"],
    )

    create_repeat_quiz_questions_and_options(quiz, saved_questions_data)
    return quiz    

def update_existing_repeat_quiz(slug, user, saved_questions_data, quiz_data):
    quiz = RepeatQuiz.objects.filter(slug=slug, user=user)

    if quiz.exists():
        quiz = quiz.first()
    else:
        return None

    quiz.get_questions().delete()
    create_repeat_quiz_questions_and_options(quiz, saved_questions_data)
    return quiz

def create_repeat_quiz_questions_and_options(quiz, saved_questions_data):
    question_models = []
    option_models = []

    for key in saved_questions_data.keys():
        question = RepeatQuizQuestion.objects.create(
            repeat_quiz = quiz,
            question=key,
            question_text=saved_questions_data[key]["question_text"]
        )
        question_models.append(question)

    for i, key in enumerate(saved_questions_data.keys()):
        for option_key in saved_questions_data[key]["options"].keys():
            option_models.append(RepeatQuizOption(
                repeat_quiz_question = question_models[i],
                option=option_key.replace(".", ""),
                option_text=saved_questions_data[key]["options"][option_key]["optionText"],
                key=saved_questions_data[key]["options"][option_key]["key"]
            ))

    option_models = RepeatQuizOption.objects.bulk_create(option_models)