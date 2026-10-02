/*
 * messagerie.js
 * -------------
 * Gère l'enregistrement d'un message vocal directement depuis le
 * microphone du navigateur (API MediaRecorder), pour la page de
 * conversation. L'audio enregistré est converti en base64 et envoyé au
 * serveur dans un champ caché du formulaire.
 */
document.addEventListener("DOMContentLoaded", () => {
    const boutonMicro = document.getElementById("bouton-micro");
    if (!boutonMicro) return; // on n'est pas sur une page de conversation

    const champAudio = document.getElementById("champ-audio");
    const champTexte = document.getElementById("champ-texte");
    const formulaire = document.getElementById("form-message");
    const etatEnregistrement = document.getElementById("etat-enregistrement");

    let enregistreur = null;
    let morceauxAudio = [];
    let enregistrementEnCours = false;

    const iconeMicro = boutonMicro.innerHTML;
    const iconeStop = '<svg viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="6" width="12" height="12" rx="2"/></svg>';

    boutonMicro.addEventListener("click", async () => {
        if (!enregistrementEnCours) {
            try {
                const flux = await navigator.mediaDevices.getUserMedia({ audio: true });
                enregistreur = new MediaRecorder(flux);
                morceauxAudio = [];

                enregistreur.ondataavailable = (evenement) => morceauxAudio.push(evenement.data);

                enregistreur.onstop = () => {
                    const blobAudio = new Blob(morceauxAudio, { type: "audio/webm" });
                    const lecteur = new FileReader();
                    lecteur.onloadend = () => {
                        champAudio.value = lecteur.result;
                        formulaire.submit();
                    };
                    lecteur.readAsDataURL(blobAudio);
                };

                enregistreur.start();
                enregistrementEnCours = true;
                boutonMicro.innerHTML = iconeStop;
                boutonMicro.classList.add("actif");
                etatEnregistrement.textContent = "Enregistrement en cours… clique pour envoyer";
            } catch (erreur) {
                etatEnregistrement.textContent = "Micro non disponible ou refusé.";
            }
        } else {
            enregistreur.stop();
            enregistrementEnCours = false;
            boutonMicro.innerHTML = iconeMicro;
            boutonMicro.classList.remove("actif");
            etatEnregistrement.textContent = "Envoi du message vocal…";
        }
    });

    formulaire.addEventListener("submit", () => {
        if (champTexte.value.trim() === "") {
            champTexte.removeAttribute("name");
        }
    });
});
