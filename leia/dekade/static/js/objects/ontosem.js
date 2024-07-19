import { LEIAObject } from "./_default.js";

export class Analysis extends LEIAObject {

    constructor(content) {
        super();
        this.content = content;
    }

    prepareData() {
        return {
            ...super.prepareData(),
            analysis: this.content
        }
    }

    activateListeners(element) {
        element.find("span.caret").click(this._onCaretClicked.bind(this));
        element.find("a.syntax-content-link").click(this._onSyntaxContentLinkClicked.bind(this));
        element.find("a.candidate-content-link").click(this._onCandidateContentLinkClicked.bind(this));
    }

    templateName() {
        return "leia.ontosem.analysis";
    }

    label() {
        const text = this.name();
        let truncated = text.slice(0, 17);
        if (truncated != text) {
            truncated = truncated + "...";
        }
        return truncated;
    }

    name() {
        return '"' + this.text() + '"-' + this.content.id;
    }

    text() {
        return this.content.sentences.map(s => s.text).join(" ");
    }

    async render() {
        const rendered = $(await super.render());
        const logs = new Logs(this.content.logs);
        const logsElement = await logs.render();

        rendered.find("div.analysis-logs").empty();
        rendered.find("div.analysis-logs").append(logsElement);

        return this.rendered;
    }

    async showContent(content) {
        const rendered = await content.render();

        this.rendered.find("div.analysis-content").empty();
        this.rendered.find("div.analysis-content").append(rendered);
    }

    _onCaretClicked(event) {
        const span = $(event.currentTarget);
        span.toggleClass("caret-down");

        const ul = span.siblings();
        ul.toggleClass("active");
    }

    async _onSyntaxContentLinkClicked(event) {
        const link = $(event.currentTarget);
        const sentence = this.content.sentences[parseInt(link.data("sentence"))];

        const syntax = new Syntax(sentence.syntax);
        await this.showContent(syntax);
    }

    async _onCandidateContentLinkClicked(event) {
        const link = $(event.currentTarget);
        const sentence = this.content.sentences[parseInt(link.data("sentence"))];
        const candidate = sentence.candidates[parseInt(link.data("candidate"))];
        const contentTarget = link.data("content");

        if (contentTarget == "basic-tmr") {
            const tmr = new TMR(candidate["basic-tmr"]);
            await this.showContent(tmr);
        } else if (contentTarget == "extended-tmr") {
            const tmr = new TMR(candidate["extended-tmr"]);
            await this.showContent(tmr);
        } else if (contentTarget == "meta-data") {
            const cand = new Candidate(candidate);
            await this.showContent(cand);
        } else {
            console.log("Unhandled content target type: " + contentTarget);
        }
    }

}


export class Logs extends LEIAObject {

    constructor(content) {
        super();
        this.content = content;
    }

    prepareData() {
        return {
            ...super.prepareData(),
            logs: this.content
        }
    }

    activateListeners(element) {

    }

    templateName() {
        return "leia.ontosem.logs";
    }

    label() {
        return "Logs";
    }

    name() {
        return "Logs";
    }

}


export class Syntax extends LEIAObject {

    constructor(content) {
        super();
        this.content = content;
    }

    prepareData() {
        return {
            ...super.prepareData(),
            syntax: this.content
        }
    }

    activateListeners(element) {

    }

    templateName() {
        return "leia.ontosem.syntax";
    }

    label() {
        return "Syntax";
    }

    name() {
        return "Syntax";
    }

}


export class Candidate extends LEIAObject {

    constructor(content) {
        super();
        this.content = content;
    }

    prepareData() {
        return {
            ...super.prepareData(),
            constraints: this.content.constraints,
            scores: this.content.scores,
            finalScore: this.content["final-score"],
            senseMaps: this.content["sense-maps"]
        }
    }

    activateListeners(element) {

    }

    templateName() {
        return "leia.ontosem.candidate";
    }

    label() {
        return "Candidate";
    }

    name() {
        return "Candidate";
    }

}


export class TMR extends LEIAObject {

    constructor(content) {
        super();
        this.content = content;
    }

    prepareData() {
        return {
            ...super.prepareData(),
            instances: this.content.instances
        }
    }

    activateListeners(element) {

    }

    templateName() {
        return "leia.ontosem.tmr";
    }

    label() {
        return "TMR";
    }

    name() {
        return this.text();
    }

}