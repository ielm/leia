export { Concept } from "./objects/concept.js";

import * as API from "./api.js";
import * as OntologySidebar from "./sidebars/ontology.js";
import * as OntoSemSidebar from "./sidebars/ontosem.js";
import { contentTabs } from "./tabs.js";

Handlebars.registerHelper("inc", function(value, options) {
    return parseInt(value) + 1;
});

Handlebars.registerHelper("eachCandidateScoreParameter", function(score, options) {
    const copiedScore = {};
    Object.assign(copiedScore, score);
    delete copiedScore.type;
    delete copiedScore.message;
    delete copiedScore.score;

    return options.fn(copiedScore);
});

class HelpButton extends HTMLButtonElement {

    constructor() {
        super();
        this.innerHTML = "?";
        this.addEventListener("click", e => { this._onClicked(e) });
    }

    _onClicked(event) {
        console.log(event);
    }

}

class ContentLink extends HTMLAnchorElement {

    constructor() {
        super();
        this.addEventListener("click", e => { this._onClicked(e) });
    }

    async _onClicked(event) {
        const contentId = $(event.currentTarget).data("content-id");
        const object = await API.contentIdToLEIAObject(contentId);

        // Add the tab, and open it unless the ALT key is held.
        contentTabs.addObject(object, !event.altKey);
    }

}

customElements.define("help-button", HelpButton, { extends: "button" });
customElements.define("content-link", ContentLink, { extends: "a" });