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

customElements.define("help-button", HelpButton, { extends: "button" });