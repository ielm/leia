import * as API from "../api.js";
import { LEIAObject } from "../objects/_default.js";


const enterSearchTemplate = `
    <div class="empty-contents-message">
        Enter a search in the field above.
    </div>
`;

const noResultsTemplate = `
    <div class="empty-contents-message">
        No results found.
    </div>
`;

const treeChildrenTemplate = `
    <ul class="nested">
        {{#each children}}
        <li>
            <span class="caret" data-concept="{{this}}"></span>
            <a is="content-link" data-content-id="@{{this}}">@{{this}}</a>
        </li>
        {{/each}}
    </ul>
`;


$(document).ready(function() {
    $(".ontology-sidebar-tree-viewer").on("click", ".caret", _onCaretClicked);
    $(".ontology-sidebar-tree").on("click", _onOntologySidebarTreeClick);
    $(".ontology-sidebar-filter").on("keyup", _onOntologySidebarFilterKeyup);
    $(".ontology-sidebar-search-results").append($(enterSearchTemplate));
});


async function _onCaretClicked(event) {
    const span = $(event.currentTarget);
    span.toggleClass("caret-down");

    const concept = span.data("concept");

    if (span.hasClass("caret-down")) {
        const children = await API.apiKnowledgeOntologyChildren(concept);
        const template = Handlebars.compile(treeChildrenTemplate);
        const rendered = $(template({"children": children}));

        span.parent().append(rendered);
    } else {
        span.parent().find("ul").remove();
    }

    const ul = span.siblings();
    ul.toggleClass("active");
}


async function _onOntologySidebarTreeClick(event) {
    const treeview = $(".ontology-sidebar-tree-viewer");
    const container = $(".ontology-sidebar-search-results");

    treeview.removeClass("hidden");
    container.addClass("hidden");
}


async function _onOntologySidebarFilterKeyup(event) {
    const filter = $(event.currentTarget).val();
    const treeview = $(".ontology-sidebar-tree-viewer");
    const container = $(".ontology-sidebar-search-results");
    container.empty();

    if (filter == "") {
        container.append($(enterSearchTemplate));
        treeview.removeClass("hidden");
        container.addClass("hidden");
        return;
    }

    const results = await API.apiKnowledgeOntologyFilter(filter);

    if (results.length == 0) {
        container.append($(noResultsTemplate));
        treeview.addClass("hidden");
        container.removeClass("hidden");
        return;
    }

    const resultsElement = new OntologySidebarResults(results);
    container.append(await resultsElement.html());

    treeview.addClass("hidden");
    container.removeClass("hidden");
}


export class OntologySidebarResults extends LEIAObject {

    constructor(results) {
        super();
        this.results = results;
    }

    activateListeners(element) {

    }

    templateName() {
        return "leia.knowledge.ontology.sidebar.results";
    }

}