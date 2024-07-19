import { LEIAObject } from "./_default.js";

export class Concept extends LEIAObject {

    constructor(content) {
        super();
        this.content = content;
    }

    prepareData() {
        return {
            ...super.prepareData(),
            name: this.name(),
        }
    }

    activateListeners(element) {
        element.find("button").click(this._onButtonClicked.bind(this));
    }

    templateName() {
        return "leia.knowledge.ontology.concept";
    }

    label() {
        return "@" + this.name();
    }

    name() {
        return this.content.name;
    }

    _onButtonClicked(event) {
        console.log(this);
        console.log(this.constructor.name);
        console.log(event);
        console.log(event.target);
        console.log($(event.target).val());
    }

}