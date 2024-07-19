import * as API from "../api.js";
import { LEIAObject } from "./_default.js";


export class PropertiesTree extends LEIAObject {

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
        return "leia.knowledge.properties.tree";
    }

    label() {
        return "Properties";
    }

    name() {
        return "Properties";
    }

    _childrenTemplate() {
        return `
            <ul class="nested">
                {{#each children}}
                <li>
                    <span class="caret" data-property="{{this}}"></span>
                    <a is="content-link" data-content-type="properties.property" data-content-id="\${{this}}">\${{this}}</a>
                </li>
                {{/each}}
            </ul>
        `;
    }

    async _onCaretClicked(event) {
        const span = $(event.currentTarget);
        span.toggleClass("caret-down");

        const property = span.data("property");

        if (span.hasClass("caret-down")) {
            const children = await API.apiKnowledgePropertiesChildren(property);
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


export class Property extends LEIAObject {

    constructor(content) {
        super();
        this.content = content;
    }

    prepareData() {
        return {
            ...super.prepareData(),
            property: this.content
        }
    }

    activateListeners(element) {

    }

    templateName() {
        return "leia.knowledge.properties.property";
    }

    label() {
        return this.name();
    }

    name() {
        return this.content.name;
    }

}