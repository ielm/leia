export { Concept } from "./objects/concept.js";

import * as OntologySidebar from "./sidebars/ontology.js";

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

    _onClicked(event) {
        const contentId = $(event.currentTarget).data("content-id");

        if (!event.altKey) {
            console.log("Open " + contentId + " and display it.");
        } else {
            console.log("Open " + contentId + " but do not display it, unless it is the only content.")
        }
    }

}

customElements.define("help-button", HelpButton, { extends: "button" });
customElements.define("content-link", ContentLink, { extends: "a" });