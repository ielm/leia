class LEIAHBSTemplates {

    constructor() {
        this.templates = {
            "leia.default.template": "handlebars/_default.html",
            "leia.knowledge.ontology.concept": "handlebars/ontology/concept.html",
            "leia.knowledge.ontology.sidebar.results": "handlebars/ontology/sidebar_results.html",
            "leia.ontosem.analysis": "handlebars/ontosem/analysis.html",
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