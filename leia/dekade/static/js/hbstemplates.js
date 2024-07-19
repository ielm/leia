class LEIAHBSTemplates {

    constructor() {
        this.templates = {
            "leia.default.template": "handlebars/_default.html",
            "leia.errors.report": "handlebars/errors/report.html",
            "leia.knowledge.lexicon.sense": "handlebars/lexicon/sense.html",
            "leia.knowledge.lexicon.sidebar.results": "handlebars/lexicon/sidebar_results.html",
            "leia.knowledge.ontology.concept": "handlebars/ontology/concept.html",
            "leia.knowledge.ontology.sidebar.results": "handlebars/ontology/sidebar_results.html",
            "leia.knowledge.ontology.tree": "handlebars/ontology/tree.html",
            "leia.knowledge.properties.property": "handlebars/properties/property.html",
            "leia.knowledge.properties.sidebar.results": "handlebars/properties/sidebar_results.html",
            "leia.knowledge.properties.tree": "handlebars/properties/tree.html",
            "leia.ontosem.analysis": "handlebars/ontosem/analysis.html",
            "leia.ontosem.candidate": "handlebars/ontosem/candidate.html",
            "leia.ontosem.logs": "handlebars/ontosem/logs.html",
            "leia.ontosem.syntax": "handlebars/ontosem/syntax.html",
            "leia.ontosem.tmr": "handlebars/ontosem/tmr.html",
        };
    }

    async getTemplate(name) {
        let template = this.templates[name];

        if (typeof(template) == "string") {
            template = await this.getTemplateContent(template);
            template = Handlebars.compile(template);
            this.templates[name] = template;
        }

        return template;
    }

    async getTemplateContent(path) {
        try {
            const response = await axios.get(path);
            return response.data;
        } catch (error) {
            console.error(error);
        }
    }
}

export const templates = new LEIAHBSTemplates();