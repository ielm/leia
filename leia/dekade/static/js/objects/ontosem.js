import { LEIAObject } from "./_default.js";

export class Analysis extends LEIAObject {

    constructor(content) {
        super();
        this.content = content;
    }

    prepareData() {
        return {
            ...super.prepareData(),
        }
    }

    activateListeners(element) {

    }

    templateName() {
        return "leia.ontosem.analysis";
    }

    label() {
        const text = this.text();
        let truncated = text.slice(0, 17);
        if (truncated != text) {
            truncated = truncated + "...";
        }
        return truncated;
    }

    name() {
        return this.text();
    }

    text() {
        return this.content.sentences.map(s => s.text).join(" ");
    }

}