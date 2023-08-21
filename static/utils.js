var csrf_token = document.querySelector("[name=csrfmiddlewaretoken]").value;

function unicodeToChar(text) {
    text = text.replace("\u00c0", "À")
    text = text.replace("\u00c1", "Á")
    text = text.replace("\u00c2", "Â")
    text = text.replace("\u00c3", "Ã")
    text = text.replace("\u00c4", "Ä")
    text = text.replace("\u00c5", "Å")
    text = text.replace("\u00c6", "Æ")
    text = text.replace("\u00c7", "Ç")
    text = text.replace("\u00c8", "È")
    text = text.replace("\u00c9", "É")
    text = text.replace("\u00ca", "Ê")
    text = text.replace("\u00cb", "Ë")
    text = text.replace("\u00cc", "Ì")
    text = text.replace("\u00cd", "Í")
    text = text.replace("\u00ce", "Î")
    text = text.replace("\u00cf", "Ï")
    text = text.replace("\u00d1", "Ñ")
    text = text.replace("\u00d2", "Ò")
    text = text.replace("\u00d3", "Ó")
    text = text.replace("\u00d4", "Ô")
    text = text.replace("\u00d5", "Õ")
    text = text.replace("\u00d6", "Ö")
    text = text.replace("\u00d8", "Ø")
    text = text.replace("\u00d9", "Ù")
    text = text.replace("\u00da", "Ú")
    text = text.replace("\u00db", "Û")
    text = text.replace("\u00dc", "Ü")
    text = text.replace("\u00dd", "Ý")
    text = text.replace("\u00df", "ß")
    text = text.replace("\u00e0", "à")
    text = text.replace("\u00e1", "á")
    text = text.replace("\u00e2", "â")
    text = text.replace("\u00e3", "ã")
    text = text.replace("\u00e4", "ä")
    text = text.replace("\u00e5", "å")
    text = text.replace("\u00e6", "æ")
    text = text.replace("\u00e7", "ç")
    text = text.replace("\u00e8", "è")
    text = text.replace("\u00e9", "é")
    text = text.replace("\u00ea", "ê")
    text = text.replace("\u00eb", "ë")
    text = text.replace("\u00ec", "ì")
    text = text.replace("\u00ed", "í")
    text = text.replace("\u00ee", "î")
    text = text.replace("\u00ef", "ï")
    text = text.replace("\u00f0", "ð")
    text = text.replace("\u00f1", "ñ")
    text = text.replace("\u00f2", "ò")
    text = text.replace("\u00f3", "ó")
    text = text.replace("\u00f4", "ô")
    text = text.replace("\u00f5", "õ")
    text = text.replace("\u00f6", "ö")
    text = text.replace("\u00f8", "ø")
    text = text.replace("\u00f9", "ù")
    text = text.replace("\u00fa", "ú")
    text = text.replace("\u00fb", "û")
    text = text.replace("\u00fc", "ü")
    text = text.replace("\u00fd", "ý")
    text = text.replace("\u00ff", "ÿ")
    return text;
}

function formatDataString(dataString) {
    dataString = dataString.replace(/&quot;/g, '"');
    dataString = dataString.replace(/&#x27;/g, "”");
    dataString = dataString.replace(/'/g, "\'");
    dataString = unicodeToChar(dataString);
    return JSON.parse(dataString);
}

function formatOptionsString(optionsString) {
    optionsString = optionsString.replace(/&quot;/g, '"');
    return JSON.parse(optionsString);
}

function cellInFocus(element) {
    element.classList.add("bg-light");
    element.dataset.old_value = element.innerText;
}

async function cellOutFocus(element, type) {
    element.classList.remove("bg-light");
    let text = element.innerText.trim();
    let target_url = "";

    if (type == "SAVED")
        target_url = "/quiz/saved-quiz/update/name/";
    else if (type == "REPEAT")
        target_url = "/quiz/repeat-quiz/update/name/";

    if (text.length == 0 || text.length > 10) {
        element.innerText = element.dataset.old_value;
    } else {
        await fetch(target_url, {
            headers: {
                "X-CSRFToken": csrf_token,
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            method: "POST",
            body: JSON.stringify({
                slug: element.dataset.slug,
                name: text
            })
        })
        .then(data => data.json())
        .then(data => {
            if (data.status == "fail") {
                element.innerText = element.dataset.old_value;
            } else if (data.status == "success") {
                let linker = element.dataset.linker;
                console.log(linker);
                console.log(`[data-linker="${linker}"]`);
                console.log(document.querySelectorAll(`[data-linker="${linker}"]`));

                document.querySelectorAll(`[data-linker="${linker}"]`).forEach(item => {
                    item.innerText = element.innerText;
                });
            }
        });
    }
}

function cellOnInput(element) {
    
}

function scrollToElement(element) {
    const y = element.getBoundingClientRect().top + window.scrollY;
    window.scroll({
        top: y,
        behavior: "smooth"
    });
}