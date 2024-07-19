import { LEIAObject } from "./_default.js";


export class Sense extends LEIAObject {

    constructor(content) {
        super();
        this.content = content;
    }

    prepareData() {
        return {
            ...super.prepareData(),
            sense: this.content
        }
    }

    activateListeners(element) {

    }

    templateName() {
        return "leia.knowledge.lexicon.sense";
    }

    label() {
        return "~" + this.name();
    }

    name() {
        return this.content.SENSE;
    }

}