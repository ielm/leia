import { LEIAObject } from "./_default.js";


export class Sense extends LEIAObject {

    constructor(content) {
        super();
        this.content = content;
    }

    prepareData() {
        return {
            ...super.prepareData(),
            sense: this.content["SENSE"],
            word: this.content["WORD"],
            pos: this.content["CAT"],
            comments: this.content["COMMENTS"],
            definition: this.content["DEF"],
            example: this.content["EX"],
            synonyms: this.content["SYNONYMS"],
            hyponyms: this.content["HYPONYMS"],
            tmrhead: this.content["TMR-HEAD"],
            synstruc: this.content["SYN-STRUC"],
            semstruc: this.content["SEM-STRUC"],
            mps: this.content["MEANING-PROCEDURES"],
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