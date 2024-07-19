export { Concept } from "./objects/concept.js";

import * as API from "./api.js";
import * as HBSHelpers from "./hbshelpers.js";
import * as LexiconSidebar from "./sidebars/lexicon.js";
import * as OntologySidebar from "./sidebars/ontology.js";
import * as OntoSemSidebar from "./sidebars/ontosem.js";
import * as PropertiesSidebar from "./sidebars/properties.js";
import { contentTabs } from "./tabs.js";

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
        const contentType = $(event.currentTarget).data("content-type");
        const object = await API.contentIdToLEIAObject(contentId, contentType);

        // Add the tab, and open it unless the ALT key is held.
        contentTabs.addObject(object, !event.altKey);
    }

}

customElements.define("help-button", HelpButton, { extends: "button" });
customElements.define("content-link", ContentLink, { extends: "a" });