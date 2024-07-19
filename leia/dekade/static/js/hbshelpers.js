Handlebars.registerHelper("inc", function(value, options) {
    return parseInt(value) + 1;
});

Handlebars.registerHelper("json", function(context) {
    return JSON.stringify(context);
});

Handlebars.registerHelper("eachCandidateScoreParameter", function(score, options) {
    const copiedScore = {};
    Object.assign(copiedScore, score);
    delete copiedScore.type;
    delete copiedScore.message;
    delete copiedScore.score;

    return options.fn(copiedScore);
});