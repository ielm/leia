import { LEIAObject } from "./_default.js";

export class Concept extends LEIAObject {

    constructor(name, parent) {
        super();
        this.name = name;
        this.parent = parent;
    }

    prepareData() {
        return {
            ...super.prepareData(),
            xyz: 123
        }
    }

    activateListeners(element) {
        element.find("button").click(this._onButtonClicked.bind(this));
    }

    templateName() {
        return "leia.knowledge.ontology.concept";
    }

    out() {
        return this.name + " isa " + this.parent;
    }

    _onButtonClicked(event) {
        console.log(this);
        console.log(this.constructor.name);
        console.log(this.out());
        console.log(event);
        console.log(event.target);
        console.log($(event.target).val());
    }

}