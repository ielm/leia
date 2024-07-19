import * as API from "../api.js";
import * as OntoSem from "../objects/ontosem.js";
import { contentTabs } from "../tabs.js";


$(document).ready(function() {
    $(".ontosem-input-button").on("click", _onOntoSemInputButtonClick);
});


async function _onOntoSemInputButtonClick(event) {
    const input = $(event.currentTarget).closest(".ontosem-sidebar").children(".ontosem-input-text").val();
    const results = await API.apiOntoSemAnalyze(input);

    console.log(results);
    const analysis = new OntoSem.Analysis(results);
    contentTabs.addObject(analysis);
}