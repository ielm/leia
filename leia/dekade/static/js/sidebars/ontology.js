import * as API from "../api.js";
import { LEIAObject } from "../objects/_default.js";
import { OntologyTree } from "../objects/tree.js";
import { contentTabs } from "../tabs.js";


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


$(document).ready(function() {
    // Note there are other document.ready type calls at the bottom of the script, that require "await".

    $(".ontology-sidebar-tree").on("click", _onOntologySidebarTreeClick);
    $(".ontology-sidebar-filter").on("keyup", _onOntologySidebarFilterKeyup);
    $(".ontology-sidebar-search-results").append($(enterSearchTemplate));
});


async function _onOntologySidebarTreeClick(event) {
    if (event.altKey) {
        contentTabs.addObject(await new OntologyTree());
        return;
    }

    const treeview = $(".ontology-sidebar-tree-viewer-container");
    const container = $(".ontology-sidebar-search-results");

    treeview.removeClass("hidden");
    container.addClass("hidden");
}


async function _onOntologySidebarFilterKeyup(event) {
    const filter = $(event.currentTarget).val();
    const treeview = $(".ontology-sidebar-tree-viewer-container");
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
    container.append(await resultsElement.render());

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


$(".ontology-sidebar-tree-viewer-container").append(await new OntologyTree().render());