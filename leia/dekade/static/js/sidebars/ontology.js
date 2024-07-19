import * as API from "../api.js";
import { LEIAObject } from "../objects/_default.js";


$(document).ready(function() {
    $(".ontology-sidebar-filter").on("keyup", _onOntologySidebarFilterKeyup);
});


async function _onOntologySidebarFilterKeyup(event) {
    const filter = $(event.currentTarget).val();
    const results = await API.apiKnowledgeOntologyFilter(filter);

    const resultsElement = new OntologySidebarResults(results);

    const container = $(".ontology-sidebar-content");
    container.empty();
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