import * as API from "../api.js";


$(document).ready(function() {
    $(".ontosem-input-button").on("click", _onOntoSemInputButtonClick);
});


async function _onOntoSemInputButtonClick(event) {
    const input = $(event.currentTarget).closest(".ontosem-sidebar").children(".ontosem-input-text").val();
    const results = await API.apiOntoSemAnalyze(input);

    console.log(input);
    console.log(results);
}