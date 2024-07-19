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


$(document).ready(function() {
    $(".ontology-sidebar-filter").on("keyup", _onOntologySidebarFilterKeyup);
    $(".ontology-sidebar-content").append($(enterSearchTemplate));
});


async function _onOntologySidebarFilterKeyup(event) {
    const filter = $(event.currentTarget).val();
    const container = $(".ontology-sidebar-content");
    container.empty();

    if (filter == "") {
        container.append($(enterSearchTemplate));
        return;
    }

    const results = await API.apiKnowledgeOntologyFilter(filter);

    if (results.length == 0) {
        container.append($(noResultsTemplate));
        return;
    }

    const resultsElement = new OntologySidebarResults(results);
    container.append(await resultsElement.html());
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