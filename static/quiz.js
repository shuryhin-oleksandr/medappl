let unansweredOptions = {};
let unansweredQuestions = questions;
// let unansweredQuestions = [questions[0], questions[1], questions[2]];

let audios = {};

let savedQuestions = {};
let deleteQuestions = {};

let scores = 0;

let questionCounter = 0;
let optionCounter = 0;
let currentQuestion;

let total_number_of_data = 2 + usedOptions.length + Object.keys(questions).length;
let number_of_data_loaded = 0;
let dataLoaded = false;

let restart = true;

let timerID;
let x;
let timeLeft = 90 * 60 * 1000;

let currentHost = document.location.protocol + '//' + document.location.host;
let correctOptionURL = `${currentHost}/static/media/${language}/answers/soundeffects/correct.mp3`;
let incorrectOptionURL = `${currentHost}/static/media/${language}/answers/soundeffects/incorrect.mp3`;

let progressBar = document.getElementById('progress-bar');
let readyButton = document.getElementById("ready-button");

let recognition = undefined;
let currentManuallyAdded = false;

loadData();

async function incrementProgressBar(offset = 1) {
    number_of_data_loaded += offset;
    let value = Math.ceil(100 * number_of_data_loaded / total_number_of_data);
    progressBar.style.width = `${value}%`;
}

async function loadData() {
    audios["correct"] = getHowlObject(correctOptionURL);
    await incrementProgressBar();
    audios["incorrect"] = getHowlObject(incorrectOptionURL)
    await incrementProgressBar();
    audios["options"] = {};
    audios["questions"] = {};

    for (let i in usedOptions) {
        audios["options"][usedOptions[i]] = getHowlObject(getOptionURL(usedOptions[i]));
        await incrementProgressBar();
    }

    for (let i in unansweredQuestions) {
        audios["questions"][unansweredQuestions[i].id] = getHowlObject(getQuestionURL(unansweredQuestions[i].question))
        await incrementProgressBar();
    }

    dataLoaded = true;
    readyButton.classList.remove("bg-dark");
    readyButton.classList.add("bg-success");
    readyButton.innerHTML = "Are you ready?"
}

function toArray(obj) {
    return Array.prototype.slice.call(obj);
}

function getHowlObject(file) {
    if (language === 'no-audio')
        return undefined;

    return new Howl({
        src: [file]
    });
}

/**
 * Play an audio file
 * @param {string} file URL to the audio file
 * @returns a Promise
 */
async function playAudio(instance) {
    if (language === 'no-audio')
        return;

    return new Promise(resolve => {
        instance.on("loaderror", resolve);
        instance.on('playerror', resolve);
        instance.on('end', resolve);
        instance.play();
    });
}

/**
 * Get the audio file assocaited with a question
 * @param {number} number Question number
 * @returns A URL to the question's audio file
 */
function getQuestionURL(number) {
    if (typeof number === "string" && number.charAt(number.length - 1) == '.')
        return `${currentHost}/static/media/${language}/questions/${number}mp3`;

    return `${currentHost}/static/media/${language}/questions/${number}.mp3`;
}

/**
 * Get the audio file assocaited with a answer
 * @param {number} name Answer number
 * @returns A URL to the answer's audio file
 */
function getOptionURL(name) {
    if (name.charAt(name.length - 1) == '.')
        return `${currentHost}/static/media/${language}/answers/${name}mp3`;

    return `${currentHost}/static/media/${language}/answers/${name}.mp3`;
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function getDismissingAlertHTML(message, type = "warning") {
    return `<div class="alert alert-${type} alert-dismissible w-100   show" role="alert"><strong>${message}<button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button></div>`;
}

function getAlertHTML(message, type = "primary") {
    return `<div class="alert w-100 alert-${type}" role="alert">${message}</div>`;
}

function addContentToPrompt(content) {
    document.getElementById('prompt').innerHTML += content;
}



$(document).bind('contextmenu', function (e) {
    e.stopPropagation();
    e.preventDefault();
    e.stopImmediatePropagation();
    return false;
});

readyButton.onclick = () => {
    if (!dataLoaded)
        return false

    readyButton.remove();
    progressBar.parentElement.remove();

    askTextQuestions();

    $("#total").text(unansweredQuestions.length);
    $("html, body").animate({
        scrollTop: 0
    }, 100);

    // Update the count down every 1 second
    x = setInterval(function () {
        timeLeft -= 1000;
        let hours = Math.floor((timeLeft % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        let minutes = Math.floor((timeLeft % (1000 * 60 * 60)) / (1000 * 60));
        let seconds = Math.floor((timeLeft % (1000 * 60)) / 1000);
    
        $("#hours").html(hours + "h ")
        $("#minutes").html(minutes + "m ")
        $("#seconds").html(seconds + "s ")
    
        // If the count down is finished, Notify
        if (timeLeft < 0) {
            // Reset timer once it reaches zero, display a modal, then redirect to home page
            $("#hours").html(0 + "h ")
            $("#minutes").html(0 + "m ")
            $("#seconds").html(0 + "s ")
            clearInterval(x);
            $("#modal-title").html("Alokovaný čas 90 minút práve vypršal.");
            $(".modal-body").html(scores + " bodov")
            $("#score-modal").modal('show')
            $(".modal-body").append("<p>Budete presmerovaný na hlavnú stránku do 10 sekúnd.</p>")
            setTimeout(returnToHomePage, 10000)
        }
    }, 1000);

    // Voice Recognition
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition || window.mozSpeechRecognition || window.msSpeechRecognition;
    
    let vrWords = [];

    if (voiceRecognition && language !== 'no-audio') {
        if (SpeechRecognition) {
            addContentToPrompt(getDismissingAlertHTML("Speech recognition supported!"))
        } else {
            addContentToPrompt(getDismissingAlertHTML("Speech recognition not supported!"))
            addContentToPrompt(getDismissingAlertHTML("Speech recognition is only supported on Google Chrome, Safari, and Microsoft Edge on Desktops only."))
            voiceRecognition = false;
            return;
        }

        recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.maxAlternatives = 1;

        if (language.startsWith("slovak")) {
            vrWords = ["áno", "nie"]
            recognition.lang = 'sk-SK';
        } else if (language.startsWith("czech")) {
            vrWords = ["ano", "ne"]
            recognition.lang = 'cs-CZ';
        } else if (language.startsWith("english")) {
            vrWords = ["yes", "no"]
            recognition.lang = 'en-US';
        }

        recognition.onspeechend = () => {
            recognition.stop();
        }

        recognition.onend = () => {
            if (restart) {
                restart = true;
                recognition.start();
            }
        }

        recognition.onresult = (event) => {
            const results = toArray(event.results);
            let result = results[0];

            if (result.isFinal) {
                recognition.stop();
                return;
            }

            alternatives = toArray(result);
            alternative = alternatives[0];
            text = alternative.transcript;
            text = " " + text.toLowerCase() + " ";
            
            let correct = $("button.answer-buttons").first()
            let incorrect = $("button.answer-buttons").first().next()
            let saveOptionButton = $("button.answer-buttons").first().next().next()
            let deleteOptionButton = $("button.answer-buttons").first().next().next().next();

            let ci = text.lastIndexOf(`${ vrWords[0]} `);
            let inci = text.lastIndexOf(`${ vrWords[1]} `);

            if ((ci != -1 || inci != -1) && restart) {
                restart = false;
                recognition.stop();

                if (ci == -1) { // if no correct text was found, it would definately be incorrect
                    if (premiumUser)
                        saveOptionButton.click(); 

                    incorrect.click();
                } else if (inci == -1) { // if no incorrect text was found, it would definately be correct
                    if (premiumUser)
                        deleteOptionButton.click();

                    correct.click();

                } else { // if both were find, use the text that was found last
                    if (ci < inci) {
                        if (premiumUser)
                            saveOptionButton.click();

                        incorrect.click();
                    } else {
                        if (premiumUser)
                            deleteOptionButton.click();

                        correct.click();
                    }
                }
            }
        }
    }
}

async function deleteOption(element) {
    let questionNumber = element.dataset.questionnumber;
    let questionText = element.dataset.questiontext;
    let option = element.dataset.option;
    let optionText = element.dataset.optiontext;
    let key = element.dataset.key;

    console.log(element.dataset)

    if (!(questionNumber in deleteQuestions)) {
        deleteQuestions[questionNumber] = {
            "question_text": questionText,
            "options": {}
        };
    }

    if (!(option in deleteQuestions[questionNumber]["options"])) {
        deleteQuestions[questionNumber]["options"][option] = { key, optionText };
    }

    console.log("DELETE QUESTIONS: ", deleteQuestions);

    // Deleting the selected option
    await fetch("/quiz/delete-options/", {
        headers: {
            "X-CSRFToken": csrf_token,
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        method: "POST",
        body: JSON.stringify({
            "question": {
                questionNumber,
                questionText,
                option,
                optionText,
                key
            },
            quizDetails
        })
    })
    .then(data => data.json())
    .then(data => {
        console.log("REPEAT QUIZ REQUEST'S RESPONSE: ", data);
        console.log("Question/Option deleted successfully!");
    });    
}

async function saveOption(element) {
    let questionNumber = element.dataset.questionnumber;
    let questionText = element.dataset.questiontext;
    let option = element.dataset.option;
    let optionText = element.dataset.optiontext;
    let key = element.dataset.key;
    element.classList.remove("btn-secondary");
    element.classList.add("btn-dark");
    element.classList.add("clicked");

    console.log(element.dataset)

    if (!(questionNumber in savedQuestions)) {
        savedQuestions[questionNumber] = {
            "question_text": questionText,
            "options": {}
        };
    }

    if (!(option in savedQuestions[questionNumber]["options"])) {
        savedQuestions[questionNumber]["options"][option] = { key, optionText };
    }

    console.log("SAVED QUESTIONS: ", savedQuestions);

    // Saving the selected option
    await fetch("/quiz/save-options/", {
        headers: {
            "X-CSRFToken": csrf_token,
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        method: "POST",
        body: JSON.stringify({
            "question": {
                questionNumber,
                questionText,
                option,
                optionText,
                key
            },
            quizDetails
        })
    })
    .then(data => data.json())
    .then(data => {
        console.log("REPEAT QUIZ REQUEST'S RESPONSE: ", data);
        console.log("Question and option saved successfully!");
    });    
}

function newTextQuestion(question, option) {
    let template = $("<div class='question-container' id='" + question.id + "'>")
    let heading = $("<div class='question'>").append($("<h5>").text("Otázka " + question.question + " " + question.question_text))
    template.append(heading)
    template.append(newTextOption(question, option))
    return template
}

function newTextOption(question, option) {
    let container = $("<div class='options'>")
    let row1 = $("<div class='row'>")
    let row2 = $("<div class='option d-flex flex-row'>")
    
    let optionText = option.option + " " + option.option_text;
    row1.append($("<p class='col-md-12 spacing-left'>").text("odpoveď " +  optionText))

    container.append(row1);

    let content = $("<div class='input-group parent-input-group mr-3'>");
    content.append($("<div class='input-group-prepend'>").append($("<span class='input-group-text'>").text("Klávesy A/D")));

    content.append($("<input type='text' class='form-control answer' name='" + question.question + "-" + "' required>"))
    row2.append($("<div class='w- d-none d-sm-none d-md-block input-container'>").append(content))

    let buttonCorrect = $("<button class='answer-buttons rounded-1 w-100 btn btn-success correct' type='button'>").text("Správne")
    let buttonIncorrect = $("<button class='answer-buttons rounded-1 w-100 btn btn-danger incorrect' type='button'>").text("Nesprávne")
    let buttonSaveOption = $(`<button class='answer-buttons rounded-1 w-100 btn btn-secondary rounded-1 save-option' type='button' data-questiontext='${question.question_text}' data-questionnumber='${question.question}' data-option='${option.option}' data-key='${option.key}' data-optiontext='${option.option_text}'>`).html("<i class='fa fa-plus'></i>");
    let buttonDeleteOption = $(`<button class='answer-buttons hide w-100 btn btn-light delete-option' type='button' data-questiontext='${question.question_text}' data-questionnumber='${question.question}' data-option='${option.option}' data-key='${option.key}' data-optiontext='${option.option_text}'>`).html("<i class='fa fa-plus'></i>");

    buttonSaveOption[0].onclick = async () => {
        await saveOption(buttonSaveOption[0]);
        buttonSaveOption[0].disabled = true;
        currentManuallyAdded = true;
    }

    buttonDeleteOption[0].onclick = async () => {
        if (!currentManuallyAdded) {
            await deleteOption(buttonDeleteOption[0]);
        }
        buttonDeleteOption[0].disabled = true;
    }

    if (!premiumUser) {
        buttonSaveOption[0].disabled = true;
        buttonDeleteOption[0].disabled = true;
    }

    row2.append(buttonCorrect)
    row2.append(buttonIncorrect)
    row2.append(buttonSaveOption)
    row2.append(buttonDeleteOption)

    row2.append($("<div class='col-1 col-md-1 checkmark text-center'>").append($("<span class='fa fa-2x a-status'>")))
    // row2.append($("<div class='col-1 col-md-1'>").append($("<span class='fa fa-2x a-status'>")))
    container.append(row2)
    return container
}

function changeTextOption(question, option) {
    newTextOption(question, option).insertBefore($("div.options").first())
}

let checkInputAnswer = async function (event) {
    let input = $("input.answer").first();
    let val = input.val().toUpperCase()
    
    if (val.length > 1)
        val = val[0]
    
    input.val(val);

    // If input is not A or D, delete input
    if (val != "A" && val != "D") {
        input.val("")
    } else {
        let fieldButtons = input.parent().parent().siblings('button');
        let verdict;

        if (val == "A") {
            verdict = currentQuestion.options[optionCounter].key == 'S';
            fieldButtons.eq(0).addClass('clicked');
        } else {
            verdict = currentQuestion.options[optionCounter].key == 'N';
            fieldButtons.eq(1).addClass('clicked');
        }

        $("button.answer-buttons").attr({ "disabled": "" });
        input.attr({ "disabled": "" });

        let status_span = $(".col-md-1 span.a-status").first();

        if (verdict == true) {
            scores += 1;
            status_span.removeClass("text-danger fa-times-circle");
            status_span.addClass("text-success fa-check-circle");

            // Deleting option
            if (premiumUser) {
                fieldButtons.eq(3)[0].disabled = false;
                fieldButtons.eq(3)[0].click();
                fieldButtons.eq(3)[0].disabled = true;
            }

            await playAudio(audios.correct);
        } else {
            if (negativeMarking)
                scores -= 1;

            status_span.removeClass("text-success fa-times-circle");
            status_span.addClass("text-danger fa-times-circle");

            // Saving option
            if (premiumUser) {
                fieldButtons.eq(2)[0].disabled = false;
                fieldButtons.eq(2)[0].click();
                fieldButtons.eq(2)[0].disabled = true;
            }
            
            await playAudio(audios.incorrect);
        }
        
        removeAnswered(currentQuestion);
        askTextQuestions();
        console.log("SCORE: ", scores);

        $("html, body").animate({
            scrollTop: 0
        }, 100);
    }
}

// Debounce function: Input as function which needs to be debounced and delay is the debounced time in milliseconds
let debounceFunction = function (func, delay) {
    // Cancels the setTimeout method execution
    clearTimeout(timerID)

    // Executes the func after delay time.
    timerID = setTimeout(func, delay)
}

function buttonAnswer() {
    if ($(this).hasClass("correct")) {
        $(this).siblings(".input-container").children(".input-group").children("input").val("A")
    } else {
        $(this).siblings(".input-container").children(".input-group").children("input").val("D")
    }
    $("button.answer-buttons").attr({ "disabled": "" })
    $(this).addClass('clicked')
    checkInputAnswer()
    $("html, body").animate({
        scrollTop: 0
    }, 100);
}

function removeAnswered(question) {
    // Remove answered options from array of unanswered options
    unansweredOptions[question.id].splice(0, 1);

    // Remove answered number from object of unanswered questions
    if (unansweredOptions[question.id].length == 0) { // If options in question are finished, remove number totally
        unansweredQuestions.splice(0, 1);
        delete (unansweredOptions[question.id])
        return false
    }

    $("html, body").animate({
        scrollTop: 0
    }, 100);
}

async function returnToHomePage() {
    console.log("QUIZ ENDED 🎊");
    // window.location = "/"
}

async function askTextQuestions() {
    currentManuallyAdded = false;
    
    if (unansweredQuestions.length == 0) {
        clearInterval(x);
        $("#modal-title").html("Vaše skóre: " + scores + " bodov");
        $("#score-modal").modal('show');
        $(".modal-body").append("<p>Budete presmerovaný na hlavnú stránku do 10 sekúnd.</p>");
        setTimeout(returnToHomePage, 10000);
        return null
    }

    let question = unansweredQuestions[0]; 
    console.log("CURRENT QUESTION: ", question);

    if (question.id in unansweredOptions == false) {
        currentQuestion = question;
        unansweredOptions[question.id] = [ ...question.options ];
        $("#count").text(questionCounter)
        questionCounter++;
        $("form").prepend(newTextQuestion(question, unansweredOptions[question.id][0]))
        optionCounter = 0;
        
        await playAudio(audios.questions[question.id]);
    } else {
        optionCounter++;
        changeTextOption(question, unansweredOptions[question.id][0])
    }

    // play latest option's audio
    await playAudio(audios.options[unansweredOptions[question.id][0].option]);
    
    // Focuses on last option and buttons spawned
    let lastInput = $("input.answer").first()
    let lastButton0 = $("button.answer-buttons").first()
    let lastButton1 = $("button.answer-buttons").first().next()
    lastInput.focus()
    lastInput.on("input", function () { debounceFunction(checkInputAnswer, 500) })
    lastButton0.on("click", buttonAnswer)
    lastButton1.on("click", buttonAnswer)
    $("body")[0].scrollIntoView()

    // Start voice recognition
    if (voiceRecognition) {
        try {
            recognition.start();
        } catch {
        }

        restart = true;
    }

    return true
}

function checkLogin() {
    $.ajax({
        url: "/user/login-status/",
        success: function (data) {
            if (!data.logged_in) {
                $("#modal-title").html("Boli ste odhlásený!");
                $(".modal-body").html("Na Váš účet sa prihlásilo ďalšie zariadenie.")
                $("#score-modal").modal('show')
                $(".modal-body").append("<p>Budete presmerovaný na hlavnú stránku do 10 sekúnd.</p>")
                setInterval(returnToHomePage, 10000)
            }
        }
    })
}

var checkLoginTimer = setInterval(function () {
    checkLogin(); // Checks if user is still logged in every 1 minutes
}, 60000);