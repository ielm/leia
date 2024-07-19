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
        element.find("a.config-content-link").click(this._onConfigContentLinkClicked.bind(this));
        element.find("a.constituencies-content-link").click(this._onConstituenciesContentLinkClicked.bind(this));
        element.find("a.dependencies-content-link").click(this._onDependenciesContentLinkClicked.bind(this));
        element.find("a.word-content-link").click(this._onWordContentLinkClicked.bind(this));
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

    async _onConfigContentLinkClicked(event) {
        const config = new Config(this.content.config);
        await this.showContent(config);
    }

    async _onConstituenciesContentLinkClicked(event) {
        const link = $(event.currentTarget);
        const sentence = this.content.sentences[parseInt(link.data("sentence"))];

        const constituencies = new Constituencies(sentence.syntax.parse);
        await this.showContent(constituencies);
    }

    async _onDependenciesContentLinkClicked(event) {
        const link = $(event.currentTarget);
        const sentence = this.content.sentences[parseInt(link.data("sentence"))];

        const dependencies = new Dependencies(sentence.syntax.dependencies);
        await this.showContent(dependencies);
    }

    async _onWordContentLinkClicked(event) {
        const link = $(event.currentTarget);
        const sentence = this.content.sentences[parseInt(link.data("sentence"))];
        const word = sentence.syntax.words[parseInt(link.data("word"))];
        const senses = this.content.lexicon[word.index];

        const element = new Word(word, senses);
        await this.showContent(element);
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


export class Config extends LEIAObject {

    constructor(content) {
        super();
        this.content = content;
    }

    prepareData() {
        return {
            ...super.prepareData(),
            config: this.content
        }
    }

    activateListeners(element) {

    }

    templateName() {
        return "leia.ontosem.config";
    }

    label() {
        return "Config";
    }

    name() {
        return "Config";
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


export class Constituencies extends LEIAObject {

    constructor(content) {
        super();
        this.content = content;
    }

    prepareData() {
        return {
            ...super.prepareData(),
            constituencies: this.content
        }
    }

    activateListeners(element) {

    }

    templateName() {
        return "leia.ontosem.syntax.constituencies";
    }

    label() {
        return "Constituencies";
    }

    name() {
        return "Constituencies";
    }

}


export class Dependencies extends LEIAObject {

    constructor(content) {
        super();
        this.content = content;
    }

    prepareData() {
        return {
            ...super.prepareData(),
            dependencies: this.content
        }
    }

    activateListeners(element) {

    }

    templateName() {
        return "leia.ontosem.syntax.dependencies";
    }

    label() {
        return "Dependencies";
    }

    name() {
        return "Dependencies";
    }

}


export class Word extends LEIAObject {

    constructor(content, senses = []) {
        super();
        this.content = content;
        this.senses = senses;
    }

    prepareData() {
        return {
            ...super.prepareData(),
            word: this.content,
            senses: this.senses,
        }
    }

    activateListeners(element) {

    }

    templateName() {
        return "leia.ontosem.syntax.word";
    }

    label() {
        return "Word";
    }

    name() {
        return "Word";
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