import * as API from "../api.js";
import * as Errors from "../objects/errors.js";
import * as OntoSem from "../objects/ontosem.js";
import { contentTabs } from "../tabs.js";


$(document).ready(function() {
    $(".ontosem-input-button").on("click", _onOntoSemInputButtonClick);
});


async function _onOntoSemInputButtonClick(event) {
    $(event.currentTarget).prop("disabled", true);

    const input = $(event.currentTarget).closest(".ontosem-sidebar-header").children(".ontosem-input-text").val();
    const results = await API.apiOntoSemAnalyze(input);

    if ("error" in results) {
        results.name = input;

        const errors = new Errors.ErrorReport(results);
        contentTabs.addObject(errors);
        return;
    }

    const analysis = new OntoSem.Analysis(results);
    contentTabs.addObject(analysis);

    $(event.currentTarget).prop("disabled", false);
}