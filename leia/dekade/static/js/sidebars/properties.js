import * as API from "../api.js";
import { LEIAObject } from "../objects/_default.js";
import { PropertiesTree } from "../objects/properties.js";
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

    $(".properties-sidebar-filter").on("keyup", _onPropertySidebarFilterKeyup);
    $(".properties-sidebar-search-results").append($(enterSearchTemplate));
});


async function _onPropertySidebarFilterKeyup(event) {
    const filter = $(event.currentTarget).val();
    const treeview = $(".properties-sidebar-tree-viewer-container");
    const container = $(".properties-sidebar-search-results");
    container.empty();

    if (filter == "") {
        container.append($(enterSearchTemplate));
        treeview.removeClass("hidden");
        container.addClass("hidden");
        return;
    }

    const results = await API.apiKnowledgePropertiesFilter(filter);

    if (results.length == 0) {
        container.append($(noResultsTemplate));
        treeview.addClass("hidden");
        container.removeClass("hidden");
        return;
    }

    const resultsElement = new PropertiesSidebarResults(results);
    container.append(await resultsElement.html());

    treeview.addClass("hidden");
    container.removeClass("hidden");
}


export class PropertiesSidebarResults extends LEIAObject {

    constructor(results) {
        super();
        this.results = results;
    }

    activateListeners(element) {

    }

    templateName() {
        return "leia.knowledge.properties.sidebar.results";
    }

}


$(".properties-sidebar-tree-viewer-container").append(await new PropertiesTree().html());