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
    $(".lexicon-sidebar-filter").on("keyup", _onLexiconSidebarFilterKeyup);
    $(".lexicon-sidebar-search-results").append($(enterSearchTemplate));
});


async function _onLexiconSidebarFilterKeyup(event) {
    const filter = $(event.currentTarget).val();
    if (filter.length == 1) {
        return;
    }

    const container = $(".lexicon-sidebar-search-results");
    container.empty();

    if (filter == "") {
        container.append($(enterSearchTemplate));
        return;
    }

    const results = await API.apiKnowledgeLexiconFilter(filter);

    if (results.length == 0) {
        container.append($(noResultsTemplate));
        return;
    }

    const resultsElement = new LexiconSidebarResults(results);
    container.append(await resultsElement.html());
}


export class LexiconSidebarResults extends LEIAObject {

    constructor(results) {
        super();
        this.results = results;
    }

    activateListeners(element) {

    }

    templateName() {
        return "leia.knowledge.lexicon.sidebar.results";
    }

}