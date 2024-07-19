import { templates } from "../hbstemplates.js";


export class LEIAObject {

    constructor() {
        // Override to include local fields
        // this.myfield = myfield;
    }

    prepareData() {
        // All local fields will be put into a copied dict
        // Override to add additional calculated fields

        return {
            ...this
        }
    }

    activateListeners(element) {
        // Override to add listeners to the element (a JQuery object)
        // Bind "this" to the listener to get a handle on the LEIAObject itself via the "this" keyword

        // Example Listener:
        // element.find("button").click(this._onButtonClicked.bind(this));
    }

    templateName() {
        // Override to provide a custom template (must be mapped in the LEIAHBSTemplates class)
        return "leia.default.template";
    }

    label() {
        // Override to specify a name when displaying this object in a tabbed or list view
        return "LEIAObject";
    }

    async html() {
        // Acquires the template, renders it with the local data, activates listeners on the element, and returns
        // the rendered element (for use by the calling method).

        const template = await templates.getTemplate(this.templateName());
        const rendered = $(template(this.prepareData()));

        this.activateListeners(rendered);

        return rendered;
    }

}