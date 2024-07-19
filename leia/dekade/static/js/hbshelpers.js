Handlebars.registerHelper("inc", function(value, options) {
    return parseInt(value) + 1;
});

Handlebars.registerHelper("json", function(context) {
    return JSON.stringify(context);
});

Handlebars.registerHelper("ifeq", function(arg1, arg2, options) {
    return (arg1 == arg2) ? options.fn(this) : options.inverse(this);
});

Handlebars.registerHelper("ifempty", function(arg, options) {
    return (arg == {}) || (arg == []) || (arg == "") ? options.fn(this): options.inverse(this);
});

Handlebars.registerHelper("toUpperCase", function(str) {
    return str.toUpperCase();
});

Handlebars.registerHelper({
    eq: (v1, v2) => v1 === v2,
    ne: (v1, v2) => v1 !== v2,
    lt: (v1, v2) => v1 < v2,
    gt: (v1, v2) => v1 > v2,
    lte: (v1, v2) => v1 <= v2,
    gte: (v1, v2) => v1 >= v2,
    and() {
        return Array.prototype.every.call(arguments, Boolean);
    },
    or() {
        return Array.prototype.slice.call(arguments, 0, -1).some(Boolean);
    }
});

Handlebars.registerHelper("eachCandidateScoreParameter", function(score, options) {
    const copiedScore = {};
    Object.assign(copiedScore, score);
    delete copiedScore.type;
    delete copiedScore.message;
    delete copiedScore.score;

    return options.fn(copiedScore);
});