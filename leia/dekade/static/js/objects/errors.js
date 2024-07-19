import { LEIAObject } from "./_default.js";


export class ErrorReport extends LEIAObject {

    constructor(content) {
        super();
        this.content = content;
    }

    prepareData() {
        return {
            ...super.prepareData(),
            error: this.content.error,
            trace: this.content.trace
        }
    }

    activateListeners(element) {

    }

    templateName() {
        return "leia.errors.report";
    }

    label() {
        return this.name();
    }

    name() {
        return "[ERR] " + this.content.name;
    }

}