import { templates } from "../hbstemplates.js";


export class LEIAObject {

    constructor() {
        // Override to include local fields
        // this.myfield = myfield;
        this.rendered = undefined;
        this.listeners = [];
        this.content = undefined;
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
        // Acquires the template and renders it with the local data.

        const template = await templates.getTemplate(this.templateName());
        const rendered = $(`<div class="leia-object">${template(this.prepareData())}</div>`);

        return rendered;
    }

    async render() {
        // Acquires the template, renders it with the local data, activates listeners on the element, and returns
        // the rendered element (for use by the calling method).

        this.rendered = await this.html();
        this.activateListeners(this.rendered);

        return this.rendered;
    }

    async reload() {
        // Override to prove a custom method that assigns a value to this.content.
        // This may involve in a remote call.
        // This method should *not* modify the rendered template or any other UI elements or listeners.
    }

    async refresh() {
        // Calls this.reload to get the latest content, and then redraws itself inside the wrapper leia-object div.
        // After, a custom event is dispatched.

        await this.reload();

        const rendered = await this.html();
        this.rendered.empty();
        this.rendered.append(rendered.children());
        this.activateListeners(this.rendered);

        const event = new CustomEvent("onRefresh", {});
        this.dispatchEvent(event);
    }

    registerListener(type, listener, callback) {
        this.listeners.push({
            type: type,
            listener: listener,
            callback: callback
        });
    }

    dispatchEvent(event) {
        for (var listener of this.listeners.filter(x => x.type == event.type)) {
            listener.callback(this, event);
        }
    }

}