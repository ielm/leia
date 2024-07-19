import * as API from "../api.js";
import { LEIAObject } from "./_default.js";


export class OntologyTree extends LEIAObject {

    constructor() {
        super();
    }

    prepareData() {
        return {
            ...super.prepareData(),
        }
    }

    activateListeners(element) {
        $(element).on("click", ".caret", this._onCaretClicked.bind(this));
    }

    templateName() {
        return "leia.knowledge.ontology.tree";
    }

    label() {
        return "Ontology";
    }

    name() {
        return "Ontology";
    }

    _childrenTemplate() {
        return `
            <ul class="nested">
                {{#each children}}
                <li>
                    <span class="caret" data-concept="{{this}}"></span>
                    <a is="content-link" data-content-type="ontology.concept" data-content-id="@{{this}}">@{{this}}</a>
                </li>
                {{/each}}
            </ul>
        `;
    }

    async _onCaretClicked(event) {
        const span = $(event.currentTarget);
        span.toggleClass("caret-down");

        const concept = span.data("concept");

        if (span.hasClass("caret-down")) {
            const children = await API.apiKnowledgeOntologyChildren(concept);
            const template = Handlebars.compile(this._childrenTemplate());
            const rendered = $(template({"children": children}));

            span.parent().append(rendered);
        } else {
            span.parent().find("ul").remove();
        }

        const ul = span.siblings();
        ul.toggleClass("active");
    }

}